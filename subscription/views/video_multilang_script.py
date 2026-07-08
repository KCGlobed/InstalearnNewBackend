import os
import sys
import json
import asyncio

import ffmpeg
from django.conf import settings
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel
import edge_tts
from google.cloud import storage
from google.oauth2 import service_account

# Map target language codes to an Edge neural voice. Add more as needed -
# full list: `edge-tts --list-voices` in your terminal.
EDGE_VOICE_MAP = {
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "hi": "hi-IN-SwaraNeural",
}


def run_ffmpeg(stream, label):
    """
    Runs an ffmpeg stream, prints full stderr on failure instead of 
    swallowing it.
    """
    try:
        stream.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else "no stderr captured"
        print(f"--- ffmpeg failed at step: {label} ---\n{stderr}", file=sys.stderr)
        raise


def synthesize_tts(text, voice, out_path, rate="+0%"):
    """
    edge-tts's API is async-only; wrap it for use inside a sync Django view.
    """
    async def _run():
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(out_path)
    asyncio.run(_run())


def transcribe_audio(model, audio_path):
    """
    Runs faster-whisper and normalizes its generator output into the
    same {start, end, text} shape the rest of the pipeline expects.
    """
    segments_gen, _info = model.transcribe(audio_path, beam_size=5)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments_gen]


def process_one_video(video_info, model, storage_client, bucket, base_media_dir, target_lang, parse_gcs_url):
    """
    Runs the full dub pipeline for a single video. Returns True on
    success, returns False on structural skip, or raises on failure.
    """
    segment_files_to_clean = []
    local_input_path = local_audio_eng = local_output_path = None

    try:
        # Parse bucket details cleanly
        _bucket_name, full_gcs_file_path = parse_gcs_url(video_info.video_file.url)
        gcs_blob_path = full_gcs_file_path.lstrip("/")
        raw_filename = os.path.basename(gcs_blob_path)

        voice = EDGE_VOICE_MAP.get(target_lang)
        if not voice:
            raise ValueError(f"No Edge voice configured for target_lang='{target_lang}'. Add it to EDGE_VOICE_MAP.")

        # Local absolute workspace paths
        local_input_path = os.path.join(base_media_dir, raw_filename)
        local_audio_eng = os.path.join(base_media_dir, f"eng_{raw_filename}.wav")
        local_output_path = os.path.join(base_media_dir, f"output_{target_lang}_{raw_filename}.mp4")

        print(f"Processing item: {raw_filename} -> {target_lang}")

        # Step 1: Download target source file from GCS
        blob = bucket.blob(full_gcs_file_path)
        blob.download_to_filename(local_input_path)

        # Step 2: Extract full target audio track configuration
        run_ffmpeg(
            ffmpeg.input(local_input_path).output(local_audio_eng, ac=1, ar='16000'),
            "extract_audio"
        )

        # Step 3: Transcribe with faster-whisper
        segments = transcribe_audio(model, local_audio_eng)
        if not segments:
            print(f"Skipping {raw_filename}: no speech detected.")
            return False

        # Step 4: Translate + TTS + speed-correct each segment
        processed_audio_clips = []
        valid_segments_metadata = []

        for idx, segment in enumerate(segments):
            start_time = segment["start"]
            end_time = segment["end"]
            original_duration = end_time - start_time
            english_text = segment["text"]

            if not english_text or original_duration <= 0:
                continue

            # Translate phrase blocks
            translated_text = GoogleTranslator(source='en', target=target_lang).translate(english_text)

            temp_seg_raw = os.path.join(base_media_dir, f"raw_{idx}_{target_lang}_{raw_filename}.mp3")
            segment_files_to_clean.append(temp_seg_raw)

            # Generate target language vocal track slice
            synthesize_tts(translated_text, voice, temp_seg_raw)

            try:
                probe = ffmpeg.probe(temp_seg_raw)
                generated_duration = float(probe['format']['duration'])
            except Exception:
                generated_duration = original_duration

            # Calculate scale multiplier needed to keep tracking synchronous
            speed_factor = generated_duration / original_duration
            speed_factor = max(0.5, min(speed_factor, 2.0)) # Clamped safely between 0.5x and 2.0x

            temp_seg_synced = os.path.join(base_media_dir, f"sync_{idx}_{target_lang}_{raw_filename}.wav")
            segment_files_to_clean.append(temp_seg_synced)

            # Apply audio tempo modifications without raising the output vocal pitch
            try:
                run_ffmpeg(
                    ffmpeg.input(temp_seg_raw).filter('atempo', speed_factor).output(
                        temp_seg_synced, ar='16000', ac=1
                    ),
                    f"atempo_segment_{idx}"
                )
                processed_audio_clips.append((start_time, temp_seg_synced))
                valid_segments_metadata.append(segment)
            except ffmpeg.Error:
                # Direct fallback on scaling errors
                processed_audio_clips.append((start_time, temp_seg_raw))
                valid_segments_metadata.append(segment)

        if not processed_audio_clips:
            print(f"Skipping {raw_filename}: no valid audio segments produced.")
            return False

        # =========================================================================
        # 🚀 STEP 5: OBJECT-ORIENTED MULTI-TRACK OVERLAY GRAPH (No tracking text strings)
        # =========================================================================
        video_input = ffmpeg.input(local_input_path)
        bg_audio = ffmpeg.input(local_audio_eng).audio

        # Apply background volume ducking
        ducked_bg = bg_audio
        for seg in valid_segments_metadata:
            s, e = seg["start"], seg["end"]
            if e > s:
                ducked_bg = ducked_bg.filter('volume', volume=0.15, enable=f'between(t,{s},{e})')

        # Map delayed TTS streams
        mixed_streams = [ducked_bg]
        for start_time, clip_path in processed_audio_clips:
            delay_ms = int(start_time * 1000)
            tts_stream = ffmpeg.input(clip_path).audio
            
            # 🚀 BOOST VOCAL VOLUME: Make the AI voice 2.5x louder before mixing
            loud_tts = tts_stream.filter('volume', volume=1.5)
            
            # Delay it and append it to our stream layer array
            delayed_tts = loud_tts.filter('adelay', f'{delay_ms}|{delay_ms}')
            mixed_streams.append(delayed_tts)

        # 🚀 MIX STREAMS WITH NORMALIZE=0 FIX
        # This stops FFmpeg from automatically lowering the volume of your tracks
        mixed_audio = ffmpeg.filter(
            mixed_streams, 
            'amix', 
            inputs=len(mixed_streams), 
            duration='longest', 
            dropout_transition=0,
            normalize=0  # <-- CRITICAL FIX HERE
        )

        # Step 6: Mux the unified audio node directly with the original video stream
        try:
            output_node = ffmpeg.output(
                video_input.video,   # Collect original video channel
                mixed_audio,         # Collect synchronized compound multi-track audio channel
                local_output_path,
                vcodec='copy',
                acodec='aac'
            )
            
            run_ffmpeg(output_node, "mux_final_video_native_graph")
            
        except ffmpeg.Error:
            return False

        # Step 7: Push the fully synchronized output file back up to GCS
        output_blob_name = f"translated/{target_lang}_{raw_filename}"
        bucket.blob(output_blob_name).upload_from_filename(local_output_path)
        print(f"Successfully uploaded: {output_blob_name}")
        
        # Optional: Save back to Django model state matrix
        # video_info.transcoded_video = output_blob_name
        # video_info.save()
        return True

    except Exception as general_error:
        print(f"Unexpected processing system breakdown: {str(general_error)}")
        raise general_error

    finally:
        # File workspace cleanup to prevent disk storage exhaustion leaks
        all_cleanup_paths = [p for p in [local_input_path, local_audio_eng, local_output_path] if p] + segment_files_to_clean
        for path in all_cleanup_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
 
class ManageBackgroundTaskView(APIView):
    renderer_classes = [SubscriptionRenderer]
 
    def get(self, request, format=None):
        calculate_video_duration_and_questions()
 
        info = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(info)
        storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
 
        video_list = Videos.objects.filter(
            is_uploaded=True,
            is_completed=True
        ).filter(Q(transcoded_video="") | Q(transcoded_video__isnull=True))
 
        if not video_list.exists():
            return Response({"message": "Nothing to process.", "videos_processed": 0}, status=status.HTTP_200_OK)
 
        target_lang = "it"
        bucket = storage_client.bucket(settings.GS_BUCKET_NAME)
        base_media_dir = os.path.join(settings.MEDIA_ROOT, "mini_lms", "videos")
        os.makedirs(base_media_dir, exist_ok=True)
 
        print("Loading faster-whisper model...")
        # compute_type='int8' keeps CPU RAM/latency reasonable; use 'float16' if you have a GPU
        model = WhisperModel("small", device="cpu", compute_type="int8")
 
        processed_count = 0
        for video_info in video_list:
            try:
                success = process_one_video(
                    video_info, model, storage_client, bucket, base_media_dir, target_lang, parse_gcs_url
                )
                if success:
                    processed_count += 1
            except Exception as general_error:
                print(f"Unexpected error processing video item: {general_error}")
                continue
 
        return Response({
            "message": "Processing cycle completed.",
            "videos_processed": processed_count
        }, status=status.HTTP_200_OK)
                