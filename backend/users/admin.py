from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your models here.


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'subscription_status']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'profile_picture',
         'bio', 'subscription_status', 'subscription_expiry')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
