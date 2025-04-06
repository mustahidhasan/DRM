from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from .models import UploadedFile, CustomUser


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['book_name','book_description','file', 'user', 'uploaded_at', 'is_archieved']
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

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Super admin can see all users
        elif request.user.role == 'publisher':
            return qs.filter(role='author')  # Publishers can only see authors
        return qs.none()  # Authors can't see any users (except their own)

    def has_view_permission(self, request, obj=None):
        # Check view permissions based on the user's role
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            return obj is None or obj.role == 'author'
        return False

    def has_change_permission(self, request, obj=None):
        # Check change permissions
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            return obj is None or obj.role == 'author'  # Publishers can only modify authors
        return False

    def has_delete_permission(self, request, obj=None):
        # Check delete permissions
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        # Publishers can add new authors, and they can set the role as 'author'
        if request.user.is_superuser:
            return True
        return request.user.role == 'publisher'  # Publishers can only add authors

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # If the logged-in user is a publisher, restrict the role field to 'author'
        if request.user.role == 'publisher':
            if 'role' in form.base_fields:
                # Allow publisher to select the 'author' role for the user
                form.base_fields['role'].widget.choices = [('author', 'Author')]  # Only allow 'author' role
                if not obj:  # If it's a new user being created
                    form.base_fields['role'].initial = 'author'  # Automatically set the role to 'author'
                    form.base_fields['role'].widget.attrs['readonly'] = 'readonly'  # Make the role field read-only

        return form

    def save_model(self, request, obj, form, change):
        if request.user.role == 'publisher':
            # Ensure that the role is 'author' for any new user created by a publisher
            if obj.role != 'author':  # Prevent role other than 'author' from being set
                obj.role = 'author'

        super().save_model(request, obj, form, change)
