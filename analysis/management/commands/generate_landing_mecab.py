from django.core.management.base import BaseCommand
from analysis.mecab_utils import analyze_sentence, is_interactive_pos
from vocab.models import GlobalTranslation
import json, os, datetime, sys

def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

def log(path, data):
    os.makedirs('logs', exist_ok=True)
    with open(path, 'a') as f:
        f.write(json.dumps(data) + "\n")
    return True

def build_spans(items):
    offset = 0
    spans = []
    for it in items:
        t = (it.get('text') or '')
        start = offset
        end = start + len(t)
        spans.append({'item': it, 'start': start, 'end': end})
        offset = end + 1
    return spans

def find_range(text, token, from_index):
    s = text.find(token, from_index)
    if s == -1:
        return None
    return {'start': s, 'end': s + len(token)}

def find_span(spans, start, end):
    for sp in spans:
        if start >= sp['start'] and end <= sp['end']:
            return sp
    return None

def compute_rel_box(span, start, end):
    box = span['item'].get('boundingBox') or {'x':0,'y':0,'w':0,'h':0}
    width_chars = max(1, span['end'] - span['start'])
    rel_start = float(start - span['start']) / float(width_chars)
    rel_end = float(end - span['start']) / float(width_chars)
    left = box['x'] + box['w'] * rel_start
    top = box['y']
    width = box['w'] * (rel_end - rel_start)
    height = box['h']
    return {'x': left, 'y': top, 'w': width, 'h': height}

def preload_translations(bases):
    qs = GlobalTranslation.objects.filter(korean_word__in=bases)
    return {g.korean_word: g.english_translation for g in qs}

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--overlay', required=True)
        parser.add_argument('--output', required=True)

    def handle(self, *args, **options):
        tried = ['mecab_sentence']
        errors = []
        working = []
        overlay_path = options['overlay']
        out_path = options['output']
        try:
            data = read_json(overlay_path)
            items = (data.get('ocr_data') or [])
            full_text = ' '.join([(it.get('text') or '') for it in items])
            spans = build_spans(items)
            parts = [p for p in full_text.split(' ') if p]
            cursor = 0
            boxes = []
            bases = []
            for token in parts:
                rng = find_range(full_text, token, cursor)
                if not rng:
                    continue
                cursor = rng['end']
                sp = find_span(spans, rng['start'], rng['end'])
                if not sp:
                    continue
                try:
                    analyzed = analyze_sentence(token)
                except Exception:
                    analyzed = []
                if not analyzed:
                    continue
                local_cursor = 0
                for surface, base, pos, grammar in analyzed:
                    if not base or not is_interactive_pos(pos or ''):
                        continue
                    fr = find_range(token, surface, local_cursor)
                    local_cursor = (fr['end'] if fr else local_cursor)
                    st = rng['start'] + (fr['start'] if fr else 0)
                    en = rng['start'] + (fr['end'] if fr else len(surface))
                    rb = compute_rel_box(sp, st, en)
                    boxes.append({'bbox': rb, 'surface': surface, 'base': base or surface, 'pos': pos or '', 'grammar': grammar or '', 'translation': ''})
                    bases.append(base or surface)
            tr_map = preload_translations(list(set(bases))) if bases else {}
            for b in boxes:
                b['translation'] = tr_map.get(b['base'], '')
            out = {'image_size': data.get('image_size'), 'token_boxes': boxes}
            write_json(out_path, out)
            working.append('mecab_boxes_written')
            log('logs/ocr_demo.log', {'ts': datetime.datetime.utcnow().isoformat()+'Z','overlay':overlay_path,'output':out_path,'tried':tried,'errors':errors,'working':working})
            self.stdout.write(self.style.SUCCESS(out_path))
        except Exception as e:
            log('logs/ocr_demo.log', {'ts': datetime.datetime.utcnow().isoformat()+'Z','overlay':overlay_path,'output':out_path,'tried':tried,'errors':[str(e)],'working':working})
            self.stderr.write(str(e))
            sys.exit(1)


