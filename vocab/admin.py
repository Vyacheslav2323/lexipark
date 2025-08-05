from django.contrib import admin
from .models import GlobalTranslation, Vocabulary, Grammar
from django.utils.html import format_html_join

@admin.register(Grammar)
class GrammarAdmin(admin.ModelAdmin):
    list_display = ('name', 'users_column', 'hover_count_column', 'first_date_column', 'last_date_column')
    search_fields = ('name',)

    def users_column(self, obj):
        users = obj.vocabularies.values_list('user__username', flat=True).distinct()
        return ', '.join(users)
    users_column.short_description = 'Users'

    def hover_count_column(self, obj):
        return sum(v.hover_count for v in obj.vocabularies.all())
    hover_count_column.short_description = 'Total Hovers'

    def first_date_column(self, obj):
        dates = obj.vocabularies.values_list('created_at', flat=True)
        return min(dates) if dates else None
    first_date_column.short_description = 'First Added'

    def last_date_column(self, obj):
        dates = obj.vocabularies.values_list('created_at', flat=True)
        return max(dates) if dates else None
    last_date_column.short_description = 'Last Added'

@admin.register(GlobalTranslation)
class GlobalTranslationAdmin(admin.ModelAdmin):
    list_display = ('korean_word', 'english_translation', 'usage_count', 'created_at')
    search_fields = ('korean_word', 'english_translation')
    ordering = ('-usage_count', '-created_at')

@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('user', 'korean_word', 'pos_display', 'english_translation', 'hover_count', 'average_duration', 'last_5_durations_display', 'created_at', 'last_reviewed', 'retention_rate')
    list_filter = ('user', 'pos', 'created_at')
    search_fields = ('korean_word', 'english_translation', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_reviewed')
    list_editable = ('retention_rate',)
    
    def pos_display(self, obj):
        return obj.get_pos_display()
    pos_display.short_description = 'Part of Speech'
    
    def average_duration(self, obj):
        return f"{obj.get_average_duration():.1f}ms"
    average_duration.short_description = 'Average Duration'
    
    def last_5_durations_display(self, obj):
        durations = obj.get_durations()
        if not durations:
            return "No hovers yet"
        formatted_durations = [f"{d:.3f}" for d in durations]
        return " ".join(formatted_durations)
    last_5_durations_display.short_description = 'Last 5 Durations (ms)'

    def retention_column(self, obj):
        return obj.get_retention_rate()
    retention_column.short_description = 'Retention'


