from django.db import models
from django.contrib.auth import get_user_model


class Subscription(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='subscription')
    paypal_subscription_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    plan_id = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=64, default='NONE')
    trial_end_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    lifetime_free = models.BooleanField(default=False)
    discount_plan_id = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.lifetime_free or self.status == 'ACTIVE'


class PromoCode(models.Model):
    KIND_LIFETIME_FREE = 'LIFETIME_FREE'
    KIND_DISCOUNT_9999 = 'DISCOUNT_9999'
    KIND_CHOICES = [
        (KIND_LIFETIME_FREE, 'Lifetime Free'),
        (KIND_DISCOUNT_9999, 'Discount 9,999 KRW Forever'),
    ]
    code = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    assigned_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='assigned_promos', null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PromoRedemption(models.Model):
    promo = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='promo_redemptions')
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('promo', 'user')


