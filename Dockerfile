# Use a specific version for reproducibility
FROM python:3.11.9-slim-bookworm

# Set environment variables to prevent interactive prompts during build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory early
WORKDIR /app

# Install system dependencies for both the application and MeCab compilation
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

# --- MeCab-ko Installation ---

ADD https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz /tmp/
ADD https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz /tmp/

# --- CHANGE IS HERE ---
# Compile and install MeCab from source using the correct extracted directory name
RUN cd /tmp/eunjeon-mecab-ko-c23f290 && \
    ./configure && \
    make -j$(nproc) && \
    make install

# --- AND CHANGE IS HERE ---
# Compile and install the MeCab dictionary using its correct directory name
RUN cd /tmp/eunjeon-mecab-ko-dic-1f2fdDC && \
    ./configure --with-dicdir=/usr/local/lib/mecab/dic && \
    make -j$(nproc) && \
    make install

# Configure library path and mecabrc for the system
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab.conf && \
    ldconfig && \
    echo "dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc

# --- Python Dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input --verbosity=2

# Clean up build artifacts to keep the final image small
RUN rm -rf /tmp/*

# Make startup script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application with migrations
CMD ["./start.sh"]