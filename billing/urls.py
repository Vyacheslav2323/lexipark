from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('create-subscription/', views.create_subscription, name='create_subscription'),
    path('status/', views.subscription_status, name='subscription_status'),
    path('webhook/', views.webhook, name='webhook'),
    path('get-gold/', views.get_gold_page, name='get_gold'),
    path('redeem/', views.redeem_promo, name='redeem'),
    path('admin/grant-free-access/', views.grant_free_access, name='grant_free_access'),
    path('admin/revoke-free-access/', views.revoke_free_access, name='revoke_free_access'),
    path('admin/free-access-page/', views.admin_free_access_page, name='admin_free_access_page'),
]


