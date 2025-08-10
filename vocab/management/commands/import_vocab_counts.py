from django.core.management.base import BaseCommand, CommandError
from vocab.models import GlobalTranslation
import csv
import io

def sniff_dialect(sample):
    try:
        return csv.Sniffer().sniff(sample)
    except Exception:
        class D: delimiter = ','
        return D()

def read_rows(path):
    try:
        with open(path, 'rb') as fb:
            raw = fb.read()
        if not raw:
            return []
        enc = 'utf-8-sig'
        if raw.startswith(b'\xff\xfe'):
            enc = 'utf-16-le'
        elif raw.startswith(b'\xfe\xff'):
            enc = 'utf-16-be'
        text = raw.decode(enc, errors='ignore')
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if not lines:
            return []
        for delim in [',', '\t', ';', '|']:
            try:
                sample = '\n'.join(lines[:50])
                dialect = sniff_dialect(sample)
            except Exception:
                class D: delimiter = delim
                dialect = D()
            reader = csv.reader(io.StringIO('\n'.join(lines)), dialect)
            header = next(reader, [])
            keys = [str(h).strip().lower() for h in header]
            if not keys:
                continue
            rows = []
            for cells in reader:
                if not any((c or '').strip() for c in cells):
                    continue
                row = {keys[i] if i < len(keys) else str(i): cells[i] for i in range(len(cells))}
                rows.append(row)
            if rows:
                return rows
        return []
    except Exception:
        return []

def normalize_int(text):
    s = (text or '').replace(',', '').strip()
    try:
        return int(float(s))
    except Exception:
        return 0

def get_count(row):
    for k in ['count', 'frequency', 'freq', 'frequency (%)']:
        if k in row:
            return normalize_int(row.get(k))
    return 0

def get_word(row):
    for k in ['word', 'korean_word']:
        if k in row:
            return (row.get(k) or '').strip()
    return ''

def upsert_word(word, count):
    obj, _ = GlobalTranslation.objects.get_or_create(
        korean_word=word,
        defaults={'english_translation': word, 'usage_count': max(1, count)}
    )
    target = max(1, count)
    if obj.usage_count != target:
        obj.usage_count = target
        obj.save(update_fields=['usage_count'])

class Command(BaseCommand):
    help = 'Import vocabulary counts from CSV into GlobalTranslation. Columns include Word and Count.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)

    def handle(self, *args, **options):
        path = options['csv_path']
        rows = read_rows(path)
        if not rows:
            raise CommandError('No rows parsed from CSV')
        updated = 0
        for row in rows:
            word = get_word(row)
            if not word:
                continue
            count = get_count(row)
            upsert_word(word, count)
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {updated} rows'))


