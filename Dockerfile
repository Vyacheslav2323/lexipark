# Dockerfile  (script-based MeCab install)

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── OS build deps ──────────────────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential curl git autoconf automake libtool \
        pkg-config wget swig && \
    rm -rf /var/lib/apt/lists/*

# ── Pin the packaging toolchain *before* running the installer ────────────────
RUN pip install --no-cache-dir --upgrade \
        "pip==23.3.1" \
        "setuptools==65.5.1" \
        "wheel==0.42.0"

# Tell pip *not* to spin up an isolated (new) build env
ENV PIP_NO_BUILD_ISOLATION=1

# ── Konlpy’s MeCab-ko installer (now succeeds) ────────────────────────────────
RUN curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh | bash -s

# ── Python deps & app code ─────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input --verbosity=2
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
