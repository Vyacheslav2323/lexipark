FROM python:3.11-slim

# Install system dependencies and MeCab with Korean support
RUN apt-get update && apt-get install -y \
    mecab \
    mecab-utils \
    mecab-ko \
    mecab-ko-dic \
    swig \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up mecabrc
RUN echo "dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files during build
RUN python manage.py collectstatic --no-input --verbosity=2

# List static files for debugging
RUN ls -la staticfiles/analysis/css/ && ls -la staticfiles/analysis/js/

# Make startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./start.sh"] 