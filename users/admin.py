from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.crypto import get_random_string
from logger import log_error, log_tried, log_working


def make_password(length):
    return get_random_string(length)


def set_user_password(data):
    u = data['user']
    p = data['password']
    u.set_password(p)
    u.save(update_fields=['password'])
    return f"{u.username}:{p}"


def reset_passwords(modeladmin, request, queryset):
    results = []
    for u in queryset:
        try:
            log_tried(f"admin:reset_password:{u.id}")
            p = make_password(12)
            msg = set_user_password({'user': u, 'password': p})
            results.append(msg)
            log_working(f"admin:reset_password_ok:{u.id}")
        except Exception as e:
            log_error(f"admin:reset_password_err:{u.id}:{str(e)}")
    if results:
        modeladmin.message_user(request, " ".join(results), level=messages.INFO)


reset_passwords.short_description = 'Set random password and show it'


class UserAdmin(DjangoUserAdmin):
    actions = [reset_passwords]
    actions_on_top = True
    actions_on_bottom = True


try:
    admin.site.unregister(User)
except Exception:
    pass
admin.site.register(User, UserAdmin)
