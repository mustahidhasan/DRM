# admin.py

from django.contrib import admin
from .models import UploadedFile, CustomUser
from django.contrib import messages

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file', 'user', 'uploaded_at', 'is_archieved']

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            role = request.user.role

            if role == 'publisher':
                obj.user = request.user
                super().save_model(request, obj, form, change)
            elif role == 'author':
                count = UploadedFile.objects.filter(user=request.user).count()
                if count >= 10:
                    self.message_user(request, "Authors can upload a maximum of 10 books.", level=messages.ERROR)
                    return
                obj.user = request.user
                super().save_model(request, obj, form, change)
            else:
                self.message_user(request, "Access denied.", level=messages.ERROR)
        else:
            super().save_model(request, obj, form, change)
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']
