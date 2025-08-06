FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mecab \
    mecab-utils \
    swig \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and run our Korean MeCab installation script
COPY install_mecab_ko.sh /tmp/
RUN chmod +x /tmp/install_mecab_ko.sh && /tmp/install_mecab_ko.sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Make startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./start.sh"] 