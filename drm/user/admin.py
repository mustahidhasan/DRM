from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from .models import UploadedFile, CustomUser


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file', 'user', 'uploaded_at', 'is_archieved']
    exclude = ['user']  # Hide user field from form

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'user' in form.base_fields:
                del form.base_fields['user']
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)  # Only return files of logged-in user

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            role = request.user.role

            if role == 'publisher':
                obj.user = request.user

            elif role == 'author':
                count = UploadedFile.objects.filter(user=request.user).count()
                if count >= 10:
                    self.message_user(
                        request,
                        "Authors can upload a maximum of 10 books.",
                        level=messages.ERROR
                    )
                    return
                obj.user = request.user

            else:
                self.message_user(request, "Access denied.", level=messages.ERROR)
                return
        else:
            # Optional: default superuser's uploads to themselves if user isn't set
            if not obj.user_id:
                obj.user = request.user

        super().save_model(request, obj, form, change)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        # Assign UploadedFile model permissions based on role
        content_type = ContentType.objects.get_for_model(UploadedFile)
        uploadedfile_perms = Permission.objects.filter(content_type=content_type)

        # Remove previous UploadedFile perms
        obj.user_permissions.remove(*uploadedfile_perms)

        if obj.role in ['publisher', 'author']:
            perms_to_assign = ['add_uploadedfile', 'view_uploadedfile']
            for codename in perms_to_assign:
                try:
                    perm = Permission.objects.get(codename=codename, content_type=content_type)
                    obj.user_permissions.add(perm)
                except Permission.DoesNotExist:
                    pass

        elif obj.role == 'super_admin':
            for perm in uploadedfile_perms:
                obj.user_permissions.add(perm)
