# Use a specific version for reproducibility
FROM python:3.11.9-slim-bookworm

# Set environment variables to prevent interactive prompts during build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory early
WORKDIR /app

# Install system dependencies. 'curl' is needed for the MeCab installer.
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# --- MeCab-ko Installation (The Robust Way) ---
# Use the official Konlpy installer script.
# This script is maintained by the project and handles finding the correct download URLs.
# 'curl -s ...' downloads the script, and '| bash -s' executes it.
RUN curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh | bash -s

# --- Python Dependencies ---
# Copy only the requirements file first to leverage Docker cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
# Now copy the rest of your application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input --verbosity=2

# Make startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./start.sh"]