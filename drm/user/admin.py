from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import CustomUser, UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['book_name', 'book_description', 'file', 'user', 'uploaded_at', 'is_archieved']
    exclude = ['user']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and 'user' in form.base_fields:
            del form.base_fields['user']
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'publisher':
            return qs.filter(user__publisher=request.user)
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            role = request.user.role
            if role == 'publisher':
                obj.user = request.user
            elif role == 'author':
                if UploadedFile.objects.filter(user=request.user).count() >= 10:
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
        elif not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role', 'publisher')}),
    )
    list_display = ['username', 'email', 'role', 'publisher', 'is_staff']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'publisher':
            return qs.filter(publisher=request.user)
        return qs.none()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            return obj is None or obj.publisher == request.user
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            return obj is None or obj.publisher == request.user
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.role == 'publisher'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.role == 'publisher':
            form.base_fields['publisher'].widget.choices = [(request.user.id, request.user.username)]
            if not obj:
                form.base_fields['publisher'].initial = request.user
                form.base_fields['publisher'].widget.attrs['readonly'] = 'readonly'
        return form

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        if request.user.role == 'publisher' and not obj.publisher:
            obj.publisher = request.user
        super().save_model(request, obj, form, change)
        form.save_m2m()
        
        # Ensure m2m relations are set up
        # Assign UploadedFile permissions
        content_type = ContentType.objects.get_for_model(UploadedFile)
        perms_to_assign = ['add_uploadedfile', 'change_uploadedfile', 'delete_uploadedfile', 'view_uploadedfile']

        for codename in perms_to_assign:
            try:
                perm = Permission.objects.get(codename=codename, content_type=content_type)
                obj.user_permissions.add(perm)
            except Permission.DoesNotExist:
                pass
