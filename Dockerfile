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
# mecab-python3   → C-extension with wheels for Linux
# mecab-ko-dic    → packaged Eunjeon ko-dictionary
# konlpy          → NLP wrapper we actually call in the app
RUN pip install --no-cache-dir \
        mecab-python3 \
        mecab-ko-dic \
        konlpy

# Tell Konlpy where the dictionary was installed
ENV MECAB_ARGS="-d $(python - <<'PY'\nimport mecab_ko_dic, os; print(os.path.dirname(mecab_ko_dic.dictionary_path))\nPY)"

# ── 3. Project deps & code ───────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input --verbosity=2
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
