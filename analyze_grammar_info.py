from vocab.models import Vocabulary
from collections import Counter
import re

def main():
    all_infos = Vocabulary.objects.exclude(grammar_info='').values_list('grammar_info', flat=True)
    unique_infos = set(all_infos)
    print(f"Total non-empty grammar_info entries: {len(all_infos)}")
    print(f"Unique grammar_info strings: {len(unique_infos)}\n")

    # Show all unique grammar_info strings
    print("Sample unique grammar_info strings:")
    for info in list(unique_infos)[:20]:
        print(f"  {info}")
    if len(unique_infos) > 20:
        print("  ...")

    # Analyze separators
    sep_patterns = [(';', r';'), ('|', r'\|'), (',', r','), ('/', r'/'), ('\\', r'\\'), ('space', r' ')]
    sep_counter = Counter()
    for info in all_infos:
        for sep, pat in sep_patterns:
            if re.search(pat, info):
                sep_counter[sep] += 1
    print("\nSeparator usage:")
    for sep, count in sep_counter.items():
        print(f"  '{sep}': {count} entries")

if __name__ == "__main__":
    main() 