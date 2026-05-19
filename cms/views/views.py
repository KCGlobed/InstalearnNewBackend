from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from cms.serializers import *
from cms.renderers import CMSRenderer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from mini_lms.utils import *
from mini_lms.roles import *
from mini_lms.permissions import RoleOrPermissionCheck
from mini_lms.pagination import CustomPageNumberPagination
from rest_framework import filters
import pandas as pd
from datetime import datetime,timezone
from rest_framework import serializers
from django.conf import settings
import os
from google.cloud import storage


class FaqTopicListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, format=None):
        category = FAQTopic.objects.filter(status = True)
        serializer = FaqTopicListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class FaqsListView(APIView):
    renderer_classes = [CMSRenderer]
    def get(self, request, cid=None):
        topic = FAQTopic.objects.filter(id=cid).first()
        if topic is None:
            raise ValidationError("Invalid FAQ Topic ID!")
        
        category = FAQs.objects.filter(status = True, faq_topic_id = cid)
        serializer = FaqListingSerializer(category, many=True)
        return success_response(message="", data=serializer.data, status_code=status.HTTP_200_OK)
    

class ContactUsView(APIView):
    renderer_classes = [CMSRenderer]
    def post(self, request, format=None):

        serializer = ContactUsSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            user  = serializer.save()
            return success_response(message="Message sent Successfully", data=serializer.data, status_code=status.HTTP_200_OK)

        return error_response(message="failed", data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)