# Dockerfile – working, minimal quoting

FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. MeCab runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        mecab \
        libmecab-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. MeCab wrapper + modern ko-dictionary + Konlpy
RUN pip install --no-cache-dir \
        mecab-python3 \
        python-mecab-ko-dic \
        konlpy

# 2b. Create mecabrc files + symlink
RUN set -e && \
    DICDIR=$(python -c 'import mecab_ko_dic, sys; print(mecab_ko_dic.dictionary_path)') && \
    mkdir -p /usr/local/etc /etc /usr/local/lib/mecab/dic && \
    echo "dicdir = ${DICDIR}" > /usr/local/etc/mecabrc && \
    echo "dicdir = ${DICDIR}" > /etc/mecabrc && \
    ln -sf "${DICDIR}" /usr/local/lib/mecab/dic/mecab-ko-dic

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
