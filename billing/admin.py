from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Subscription, PromoCode, PromoRedemption

User = get_user_model()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'lifetime_free', 'trial_end_at', 'current_period_end', 'created_at']
    list_filter = ['status', 'lifetime_free', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['grant_lifetime_free', 'revoke_lifetime_free', 'extend_trial', 'go_to_free_access_page']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status')
        }),
        ('Access Control', {
            'fields': ('lifetime_free', 'trial_end_at', 'current_period_end')
        }),
        ('PayPal Integration', {
            'fields': ('paypal_subscription_id', 'plan_id', 'discount_plan_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def grant_lifetime_free(self, request, queryset):
        updated = queryset.update(lifetime_free=True, status='ACTIVE')
        self.message_user(request, f'Granted lifetime free access to {updated} subscription(s).')
    grant_lifetime_free.short_description = "Grant lifetime free access"
    
    def revoke_lifetime_free(self, request, queryset):
        updated = queryset.update(lifetime_free=False)
        self.message_user(request, f'Revoked lifetime free access from {updated} subscription(s).')
    revoke_lifetime_free.short_description = "Revoke lifetime free access"
    
    def extend_trial(self, request, queryset):
        from django.utils.timezone import now, timedelta
        trial_extension = now() + timedelta(days=30)
        updated = queryset.update(trial_end_at=trial_extension)
        self.message_user(request, f'Extended trial for {updated} subscription(s) by 30 days.')
    extend_trial.short_description = "Extend trial by 30 days"
    
    def go_to_free_access_page(self, request, queryset):
        return HttpResponseRedirect('/billing/admin/free-access-page/')
    go_to_free_access_page.short_description = "Go to Free Access Management Page"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'kind', 'assigned_user', 'used_at', 'created_at', 'is_used']
    list_filter = ['kind', 'used_at', 'created_at']
    search_fields = ['code', 'assigned_user__username', 'assigned_user__email']
    readonly_fields = ['created_at']
    actions = ['create_lifetime_free_promo', 'assign_to_user']
    
    fieldsets = (
        ('Code Information', {
            'fields': ('code', 'kind')
        }),
        ('User Assignment', {
            'fields': ('assigned_user', 'used_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def is_used(self, obj):
        return obj.used_at is not None
    is_used.boolean = True
    is_used.short_description = 'Used'
    
    def create_lifetime_free_promo(self, request, queryset):
        from django.utils.crypto import get_random_string
        code = f"FREE_{get_random_string(8).upper()}"
        PromoCode.objects.create(code=code, kind=PromoCode.KIND_LIFETIME_FREE)
        self.message_user(request, f'Created new lifetime free promo code: {code}')
    create_lifetime_free_promo.short_description = "Create lifetime free promo code"
    
    def assign_to_user(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one promo code to assign.', level=messages.ERROR)
            return
        promo = queryset.first()
        if promo.assigned_user:
            self.message_user(request, f'Promo code {promo.code} is already assigned to {promo.assigned_user}.', level=messages.WARNING)
            return
        return HttpResponseRedirect(f'/admin/billing/promocode/{promo.id}/change/')
    assign_to_user.short_description = "Assign promo code to user"


@admin.register(PromoRedemption)
class PromoRedemptionAdmin(admin.ModelAdmin):
    list_display = ['promo', 'user', 'redeemed_at']
    list_filter = ['redeemed_at']
    search_fields = ['promo__code', 'user__username', 'user__email']
    readonly_fields = ['redeemed_at']
    
    def has_add_permission(self, request):
        return False


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'subscription_status', 'lifetime_free', 'trial_status']
    list_filter = ['subscription__lifetime_free', 'subscription__status']
    search_fields = ['username', 'email']
    actions = ['grant_lifetime_free', 'revoke_lifetime_free', 'extend_trial']
    
    def subscription_status(self, obj):
        sub = getattr(obj, 'subscription', None)
        if not sub:
            return 'No Subscription'
        return sub.status
    subscription_status.short_description = 'Subscription Status'
    
    def lifetime_free(self, obj):
        sub = getattr(obj, 'subscription', None)
        return sub.lifetime_free if sub else False
    lifetime_free.boolean = True
    lifetime_free.short_description = 'Lifetime Free'
    
    def trial_status(self, obj):
        sub = getattr(obj, 'subscription', None)
        if not sub or not sub.trial_end_at:
            return 'No Trial'
        from django.utils.timezone import now
        if sub.trial_end_at > now():
            return f'Trial Active (ends {sub.trial_end_at.strftime("%Y-%m-%d")})'
        return 'Trial Expired'
    trial_status.short_description = 'Trial Status'
    
    def grant_lifetime_free(self, request, queryset):
        for user in queryset:
            sub, created = Subscription.objects.get_or_create(user=user)
            sub.lifetime_free = True
            sub.status = 'ACTIVE'
            sub.save()
        updated = queryset.count()
        self.message_user(request, f'Granted lifetime free access to {updated} user(s).')
    grant_lifetime_free.short_description = "Grant lifetime free access"
    
    def revoke_lifetime_free(self, request, queryset):
        for user in queryset:
            sub = getattr(user, 'subscription', None)
            if sub:
                sub.lifetime_free = False
                sub.save()
        updated = queryset.count()
        self.message_user(request, f'Revoked lifetime free access from {updated} user(s).')
    revoke_lifetime_free.short_description = "Revoke lifetime free access"
    
    def extend_trial(self, request, queryset):
        from django.utils.timezone import now, timedelta
        trial_extension = now() + timedelta(days=30)
        for user in queryset:
            sub, created = Subscription.objects.get_or_create(user=user)
            sub.trial_end_at = trial_extension
            sub.save()
        updated = queryset.count()
        self.message_user(request, f'Extended trial for {updated} user(s) by 30 days.')
    extend_trial.short_description = "Extend trial by 30 days"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
