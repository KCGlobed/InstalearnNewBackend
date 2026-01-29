FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/py/bin:$PATH"

WORKDIR /app

# Install dependencies
COPY ./requirements.txt /requirements.txt
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /requirements.txt

# Copy project and set permissions
COPY . /app
RUN adduser --disabled-password --no-create-home django-user && \
    chown -R django-user:django-user /app

USER django-user

# Note: The $PORT variable is injected by Cloud Run at runtime
CMD exec gunicorn mini_lms.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --threads 4 \
    --timeout 120