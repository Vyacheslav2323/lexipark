FROM python:3.11-slim

# Install system dependencies including MeCab
RUN apt-get update && apt-get install -y \
    mecab \
    mecab-ko \
    mecab-ko-dic \
    mecab-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "jorp.wsgi:application", "--bind", "0.0.0.0:8000"] 