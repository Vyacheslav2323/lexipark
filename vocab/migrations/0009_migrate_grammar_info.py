from django.db import migrations

def migrate_grammar_info(apps, schema_editor):
    Grammar = apps.get_model('vocab', 'Grammar')
    Vocabulary = apps.get_model('vocab', 'Vocabulary')
    for vocab in Vocabulary.objects.all():
        grammar_info = vocab.grammar_info
        if grammar_info and grammar_info.strip():
            grammar, _ = Grammar.objects.get_or_create(name=grammar_info.strip())
            vocab.grammars.add(grammar)

def reverse_migration(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('vocab', '0008_grammar_remove_vocabulary_deleted_at_and_more'),
    ]
    operations = [
        migrations.RunPython(migrate_grammar_info, reverse_migration),
    ] 