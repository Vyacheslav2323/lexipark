from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from billing.models import Subscription
from django.utils.timezone import now, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Grant free access to users by username or email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            nargs='+',
            help='List of usernames or emails to grant access to'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='File containing usernames/emails (one per line)'
        )
        parser.add_argument(
            '--lifetime',
            action='store_true',
            help='Grant lifetime free access instead of trial extension'
        )
        parser.add_argument(
            '--trial-days',
            type=int,
            default=30,
            help='Number of days to extend trial (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        users_to_process = []
        
        if options['users']:
            users_to_process = options['users']
        elif options['file']:
            try:
                with open(options['file'], 'r') as f:
                    users_to_process = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                raise CommandError(f'File {options["file"]} not found')
        else:
            raise CommandError('Must specify either --users or --file')

        if not users_to_process:
            self.stdout.write(self.style.WARNING('No users specified'))
            return

        self.stdout.write(f'Processing {len(users_to_process)} users...')
        
        granted_count = 0
        not_found = []
        
        for user_identifier in users_to_process:
            try:
                if '@' in user_identifier:
                    user = User.objects.get(email=user_identifier)
                else:
                    user = User.objects.get(username=user_identifier)
                
                if options['dry_run']:
                    self.stdout.write(f'Would process: {user.username} ({user.email})')
                    continue
                
                sub, created = Subscription.objects.get_or_create(user=user)
                
                if options['lifetime']:
                    sub.lifetime_free = True
                    sub.status = 'ACTIVE'
                    self.stdout.write(f'Granted lifetime free access to {user.username}')
                else:
                    trial_extension = now() + timedelta(days=options['trial_days'])
                    sub.trial_end_at = trial_extension
                    self.stdout.write(f'Extended trial for {user.username} by {options["trial_days"]} days')
                
                sub.save()
                granted_count += 1
                
            except User.DoesNotExist:
                not_found.append(user_identifier)
                self.stdout.write(self.style.WARNING(f'User not found: {user_identifier}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {user_identifier}: {e}'))

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Dry run completed - no changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully processed {granted_count} users'))
            
        if not_found:
            self.stdout.write(self.style.WARNING(f'Users not found: {", ".join(not_found)}'))
