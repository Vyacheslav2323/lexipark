# Dockerfile – MeCab + Konlpy (works)

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Lightweight MeCab runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        mecab \
        libmecab-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. MeCab wrapper, modern ko-dictionary wheel, Konlpy
RUN pip install --no-cache-dir \
        mecab-python3 \
        python-mecab-ko-dic \
        konlpy

# 2b. Create global mecabrc + KoNLPy-friendly symlink
RUN set -e && \
    DICDIR=$(python -c "import mecab_ko_dic, sys; print(str(mecab_ko_dic.dictionary_path))") && \
    for CFG in /usr/local/etc/mecabrc /etc/mecabrc; do \
        mkdir -p \"$(dirname \"$CFG\")\" && \
        echo \"dicdir = ${DICDIR}\" > \"$CFG\"; \
    done && \
    mkdir -p /usr/local/lib/mecab/dic && \
    ln -sf \"${DICDIR}\" /usr/local/lib/mecab/dic/mecab-ko-dic

ENV MECABRC=/usr/local/etc/mecabrc
ENV MECAB_ARGS="-d /usr/local/lib/mecab/dic/mecab-ko-dic"

# 3. Project deps & code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input --verbosity=2
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
