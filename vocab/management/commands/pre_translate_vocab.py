import csv
import os
import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from vocab.models import GlobalTranslation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Command(BaseCommand):
    help = 'Pre-translate Korean words from CSV file using Papago API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='/Users/slimslavik/Desktop/vorp_extra/full_vocab_analysis.csv',
            help='Path to CSV file containing Korean words'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of words to process in each batch'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between API calls in seconds'
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Start processing from this row number (0-indexed)'
        )
        parser.add_argument(
            '--max-words',
            type=int,
            default=None,
            help='Maximum number of words to process'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        delay = options['delay']
        start_from = options['start_from']
        max_words = options['max_words']

        self.stdout.write(f'DEBUG: Command options: {options}')
        self.stdout.write(f'DEBUG: CSV file path: {csv_file}')

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        self.stdout.write(f'DEBUG: CSV file exists and is accessible')

        client_id = os.getenv('NAVER_CLIENT_ID')
        client_secret = os.getenv('NAVER_CLIENT_SECRET')

        self.stdout.write(f'DEBUG: Client ID exists: {bool(client_id)}')
        self.stdout.write(f'DEBUG: Client Secret exists: {bool(client_secret)}')

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR('Missing NAVER_CLIENT_ID or NAVER_CLIENT_SECRET environment variables')
            )
            return

        # Test database connection
        self.stdout.write(f'DEBUG: Testing database connection...')
        
        # Check database environment variables
        database_url = os.getenv('DATABASE_URL')
        self.stdout.write(f'DEBUG: DATABASE_URL exists: {bool(database_url)}')
        if database_url:
            self.stdout.write(f'DEBUG: DATABASE_URL starts with: {database_url[:20]}...')
        
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.stdout.write(f'DEBUG: Database connection successful: {result}')
            
            # Check if GlobalTranslation table exists and has data
            cursor.execute("SELECT COUNT(*) FROM vocab_globaltranslation")
            count = cursor.fetchone()[0]
            self.stdout.write(f'DEBUG: GlobalTranslation table exists with {count} existing translations')
            
            # Check database engine
            self.stdout.write(f'DEBUG: Database engine: {connection.settings_dict["ENGINE"]}')
            self.stdout.write(f'DEBUG: Database name: {connection.settings_dict.get("NAME", "N/A")}')
            self.stdout.write(f'DEBUG: Database host: {connection.settings_dict.get("HOST", "N/A")}')
            self.stdout.write(f'DEBUG: Database port: {connection.settings_dict.get("PORT", "N/A")}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Database connection failed: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Starting pre-translation from {csv_file}')
        )
        self.stdout.write(f'Batch size: {batch_size}, Delay: {delay}s, Start from: {start_from}')

        words_processed = 0
        words_translated = 0
        words_skipped = 0
        words_failed = 0

        try:
            self.stdout.write(f'DEBUG: Opening CSV file with UTF-8 encoding...')
            with open(csv_file, 'r', encoding='utf-8') as file:
                self.stdout.write(f'DEBUG: File opened successfully')
                reader = csv.DictReader(file)
                self.stdout.write(f'DEBUG: CSV reader created')
                rows = list(reader)
                self.stdout.write(f'DEBUG: Loaded {len(rows)} rows from CSV')
                
                if start_from >= len(rows):
                    self.stdout.write(
                        self.style.ERROR(f'Start row {start_from} is beyond file length {len(rows)}')
                    )
                    return

                total_rows = len(rows) - start_from
                if max_words:
                    total_rows = min(total_rows, max_words)

                self.stdout.write(f'Total words to process: {total_rows}')
                self.stdout.write(f'DEBUG: Will process rows {start_from} to {start_from + total_rows - 1}')

                for i in range(start_from, len(rows)):
                    if max_words and words_processed >= max_words:
                        self.stdout.write(f'DEBUG: Reached max_words limit ({max_words})')
                        break

                    row = rows[i]
                    word = row['Word'].strip()
                    
                    self.stdout.write(f'DEBUG: Processing row {i}: word="{word}", count={row.get("Count", "N/A")}')
                    
                    if not word:
                        self.stdout.write(f'DEBUG: Skipping empty word at row {i}')
                        continue

                    words_processed += 1

                    if words_processed % 100 == 0:
                        self.stdout.write(f'Processed {words_processed}/{total_rows} words...')

                    if self.should_skip_word(word):
                        self.stdout.write(f'DEBUG: Skipping word "{word}" (already exists or invalid)')
                        words_skipped += 1
                        continue

                    self.stdout.write(f'DEBUG: Attempting to translate word "{word}"')
                    if self.translate_and_save_word(word):
                        self.stdout.write(f'DEBUG: Successfully translated and saved "{word}"')
                        words_translated += 1
                    else:
                        self.stdout.write(f'DEBUG: Failed to translate "{word}"')
                        words_failed += 1

                    if words_processed % batch_size == 0:
                        self.stdout.write(
                            f'Batch completed. Translated: {words_translated}, '
                            f'Failed: {words_failed}, Skipped: {words_skipped}'
                        )
                        self.stdout.write(f'DEBUG: Sleeping for {delay} seconds...')
                        time.sleep(delay)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing CSV: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'\nPre-translation completed!\n'
                f'Total processed: {words_processed}\n'
                f'Successfully translated: {words_translated}\n'
                f'Skipped: {words_skipped}\n'
                f'Failed: {words_failed}'
            )
        )
        self.stdout.write(f'DEBUG: Final statistics - Processed: {words_processed}, Translated: {words_translated}, Skipped: {words_skipped}, Failed: {words_failed}')

    def should_skip_word(self, word):
        if not word or len(word) < 2:
            self.stdout.write(f'DEBUG: Word "{word}" too short or empty')
            return True

        if GlobalTranslation.objects.filter(korean_word=word).exists():
            self.stdout.write(f'DEBUG: Word "{word}" already exists in database')
            return True

        if not any('\uAC00' <= char <= '\uD7A3' for char in word):
            self.stdout.write(f'DEBUG: Word "{word}" contains no Korean characters')
            return True

        self.stdout.write(f'DEBUG: Word "{word}" passed all filters, will translate')
        return False

    def translate_and_save_word(self, word):
        try:
            self.stdout.write(f'DEBUG: Calling Papago API for word "{word}"')
            translation = self._request_papago_api(word)
            
            if translation and translation != word:
                self.stdout.write(f'DEBUG: Got translation "{translation}" for word "{word}"')
                try:
                    obj, created = GlobalTranslation.objects.get_or_create(
                        korean_word=word,
                        defaults={'english_translation': translation}
                    )
                    if created:
                        self.stdout.write(f'DEBUG: Created new translation record for "{word}"')
                    else:
                        self.stdout.write(f'DEBUG: Updated existing translation record for "{word}"')
                    self.stdout.write(f'DEBUG: Database save successful - ID: {obj.id}')
                    return True
                except Exception as db_error:
                    self.stdout.write(f'DEBUG: Database save failed for "{word}": {db_error}')
                    return False
            else:
                self.stdout.write(f'DEBUG: No translation received or translation same as original for "{word}"')
                return False

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to translate "{word}": {e}')
            )
            return False

    def _request_papago_api(self, text):
        url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
        client_id = os.getenv('NAVER_CLIENT_ID')
        client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        self.stdout.write(f'DEBUG: API URL: {url}')
        self.stdout.write(f'DEBUG: Request data: {{"source": "ko", "target": "en", "text": "{text}"}}')
        
        headers = {
            "x-ncp-apigw-api-key-id": client_id,
            "x-ncp-apigw-api-key": client_secret,
            "Content-Type": "application/json"
        }
        
        data = {
            "source": "ko",
            "target": "en",
            "text": text
        }
        
        try:
            self.stdout.write(f'DEBUG: Sending POST request to Papago API...')
            response = requests.post(url, headers=headers, json=data, timeout=10)
            self.stdout.write(f'DEBUG: Response status code: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                self.stdout.write(f'DEBUG: Response JSON: {result}')
                translated_text = result["message"]["result"]["translatedText"]
                self.stdout.write(f'DEBUG: Extracted translation: "{translated_text}"')
                return translated_text
            else:
                self.stdout.write(f'DEBUG: API error response: {response.text}')
                return None
        except Exception as e:
            self.stdout.write(f'DEBUG: Exception during API call: {e}')
            return None
