from django.core.management.base import BaseCommand
from analysis.ocr_processing import process_image_file, _load_pil
import json, sys, os, datetime

def read_path(path):
    return open(path, 'rb')

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

def log_entry(path, data):
    os.makedirs('logs', exist_ok=True)
    with open(path, 'a') as f:
        f.write(json.dumps(data) + "\n")
    return True

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--input', required=True)
        parser.add_argument('--output', required=True)

    def handle(self, *args, **options):
        inp = options['input']
        outp = options['output']
        tried = ['clova_ocr']
        errors = []
        working = []
        try:
            f = read_path(inp)
            res = process_image_file(f)
            if not res:
                errors.append('clova_failed')
                pil = _load_pil(read_path(inp))
                w, h = (pil.size if pil else (1000, 1000))
                res = {
                    'image_size': (w, h),
                    'total_items': 0,
                    'filtered_items': 0,
                    'ocr_data': []
                }
            write_json(outp, res)
            working.append('overlay_json_written')
            log_entry('logs/ocr_demo.log', {
                'ts': datetime.datetime.utcnow().isoformat() + 'Z',
                'input': inp,
                'output': outp,
                'tried': tried,
                'errors': errors,
                'working': working
            })
            self.stdout.write(self.style.SUCCESS(outp))
        except Exception as e:
            log_entry('logs/ocr_demo.log', {
                'ts': datetime.datetime.utcnow().isoformat() + 'Z',
                'input': inp,
                'output': outp,
                'tried': tried,
                'errors': [str(e)],
                'working': []
            })
            self.stderr.write(str(e))
            sys.exit(1)


