from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('create-subscription/', views.create_subscription, name='create_subscription'),
    path('status/', views.subscription_status, name='subscription_status'),
    path('webhook/', views.webhook, name='webhook'),
    path('get-gold/', views.get_gold_page, name='get_gold'),
    path('redeem/', views.redeem_promo, name='redeem'),
]


