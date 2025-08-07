# Dockerfile

# 1. Base image
FROM python:3.11.9-slim-bookworm

# 2. Prevent Python from writing .pyc files and buffer flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory
WORKDIR /app

# 4. Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      git \
      autoconf \
      automake \
      libtool \
      pkg-config \
      wget \
      swig \
    && rm -rf /var/lib/apt/lists/*

# 5. Pin older packaging tools to bypass the strict PEP 440 check
RUN pip install --no-cache-dir --upgrade \
      "pip==23.3.1" \
      "setuptools<66" \
      "wheel==0.42.0"

# 6. Install MeCab-ko via the official Konlpy script
RUN curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh | bash -s

# 7. Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copy application code
COPY . .

# 9. Collect static files
RUN python manage.py collectstatic --no-input --verbosity=2

# 10. Make entrypoint script executable
RUN chmod +x start.sh

# 11. Expose application port
EXPOSE 8000

# 12. Default command
CMD ["./start.sh"]
