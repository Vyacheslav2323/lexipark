# Dockerfile

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── 1. Lightweight MeCab runtime ─────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        mecab \
        libmecab-dev && \
    rm -rf /var/lib/apt/lists/*

# ── 2. Python wrapper + Korean dictionary + Konlpy ───────────────────────────
RUN pip install --no-cache-dir \
        mecab-python3 \
        mecab-ko-dic \
        konlpy

# ── 2b. Tell MeCab where that dictionary lives (NEW) ─────────────────────────
RUN set -e; \
    DICDIR=$(python - <<'PY'\nimport mecab_ko_dic, os, sys; sys.stdout.write(os.path.dirname(mecab_ko_dic.dictionary_path))\nPY); \
    mkdir -p /usr/local/etc /usr/local/lib/mecab/dic; \
    echo "dicdir = ${DICDIR}" > /usr/local/etc/mecabrc; \
    ln -s "${DICDIR}" /usr/local/lib/mecab/dic/mecab-ko-dic || true

# (optional) leave this ENV—harmless if mecabrc is present
ENV MECAB_ARGS="-d $(python - <<'PY'\nimport mecab_ko_dic, os; print(os.path.dirname(mecab_ko_dic.dictionary_path))\nPY)"

# ── 3. Project deps & code ───────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input --verbosity=2
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
