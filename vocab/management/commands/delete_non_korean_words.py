from django.core.management.base import BaseCommand
from django.db.models import Q, F
from vocab.models import Vocabulary
from logger import log_tried, log_working, log_error
import re


def has_hangul(text):
    return bool(re.search(r"[\uAC00-\uD7A3]", text or ""))


def get_non_korean_qs():
    return Vocabulary.objects.exclude(korean_word__regex=r"[\uAC00-\uD7A3]")

def get_non_interactive_pos_qs():
    allowed = ['NNG','NNP','NP','NR','MAG','MAJ','MM','XR']
    has_pos = Vocabulary.objects.exclude(Q(pos__isnull=True) | Q(pos=''))
    return has_pos.filter(
        ~Q(pos__in=allowed) & ~Q(pos__contains='VV') & ~Q(pos__contains='VA') & ~Q(pos__contains='VX')
    )

def get_explicit_disallowed_pos_qs():
    disallowed = ['EC','ETN','ETM','EP','EF','JKS','JKC','JKG','JKO','JKB','JKV','JKQ','JX','JC','XSV','XSA','XSN','XPN','SF','SP','SS','SE','SO','SW','SL','SH','SN']
    return Vocabulary.objects.filter(pos__in=disallowed)


class Command(BaseCommand):
    help = "Delete Vocabulary rows with no Hangul or no translation (korean_word==english_translation) or non-interactive POS"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            log_tried("delete_non_korean_words:start")
            qs_non = get_non_korean_qs()
            qs_untr = Vocabulary.objects.filter(english_translation=F("korean_word"))
            qs_pos = get_non_interactive_pos_qs()
            qs_exp = get_explicit_disallowed_pos_qs()
            qs = Vocabulary.objects.filter(
                Q(~Q(korean_word__regex=r"[\uAC00-\uD7A3]")) | Q(english_translation=F("korean_word")) | Q(id__in=qs_pos.values("id")) | Q(id__in=qs_exp.values("id"))
            )
            total = qs.count()
            if options.get("dry_run"):
                self.stdout.write(self.style.WARNING(f"Would delete {total} rows (non-korean: {qs_non.count()}, untranslated: {qs_untr.count()}, non-interactive-pos: {qs_pos.count()}, explicit-pos: {qs_exp.count()})"))
                log_working(f"delete_non_korean_words:dry_run:{total}")
                return
            deleted, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} rows"))
            log_working(f"delete_non_korean_words:deleted:{deleted}")
        except Exception as e:
            log_error(f"delete_non_korean_words:error:{str(e)}")
            raise


