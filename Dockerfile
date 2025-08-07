# Use a specific version for reproducibility
FROM python:3.11.9-slim-bookworm

# Set environment variables to prevent interactive prompts during build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory early
WORKDIR /app

# Install system dependencies for both the application and MeCab compilation
# Combining them in one layer is more efficient
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
# This section replaces the need for 'install_mecab_ko.sh'
# We use more stable BitBucket URLs and Docker's ADD command for reliability.

# Use ADD to download and auto-extract the archives into /tmp/
# This is cached by Docker. It will only re-run if the URL changes.
ADD https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz /tmp/
ADD https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz /tmp/

# Compile and install MeCab from source
RUN cd /tmp/mecab-0.996-ko-0.9.2 && \
    ./configure && \
    make -j$(nproc) && \
    make install

# Compile and install the MeCab dictionary
RUN cd /tmp/mecab-ko-dic-2.1.1-20180720 && \
    ./configure --with-dicdir=/usr/local/lib/mecab/dic && \
    make -j$(nproc) && \
    make install

# Configure library path and mecabrc for the system
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab.conf && \
    ldconfig && \
    echo "dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic" > /usr/local/etc/mecabrc

# --- Python Dependencies ---
# Copy only the requirements file first to leverage Docker cache.
# This layer only rebuilds if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
# Now copy the rest of your application code
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