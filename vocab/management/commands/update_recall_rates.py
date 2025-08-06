from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from vocab.models import Vocabulary
from vocab.bayesian_recall import update_vocabulary_recall


class Command(BaseCommand):
    help = 'Update recall rates for all existing vocabulary entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update recall rates for specific user only',
        )

    def handle(self, *args, **options):
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
                vocabularies = Vocabulary.objects.filter(user=user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" does not exist')
                )
                return
        else:
            vocabularies = Vocabulary.objects.all()

        total_count = vocabularies.count()
        updated_count = 0

        self.stdout.write(f'Processing {total_count} vocabulary entries...')

        for vocab in vocabularies:
            if vocab.alpha_prior == 1.0 and vocab.beta_prior == 1.0:
                if vocab.hover_count > 0:
                    avg_duration = vocab.get_average_duration()
                    if avg_duration > 1000:
                        vocab.alpha_prior = 1.0
                        vocab.beta_prior = 9.0
                    else:
                        vocab.alpha_prior = 10.0
                        vocab.beta_prior = 0.0
                else:
                    vocab.alpha_prior = 1.0
                    vocab.beta_prior = 9.0
            
            if vocab.hover_count > 0:
                avg_duration = vocab.get_average_duration()
                had_lookup = avg_duration > 1000
            else:
                had_lookup = True

            updated_vocab = update_vocabulary_recall(vocab, had_lookup)
            updated_vocab.save()
            updated_count += 1

            if updated_count % 100 == 0:
                self.stdout.write(f'Processed {updated_count}/{total_count}...')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated recall rates for {updated_count} vocabulary entries'
            )
        ) 