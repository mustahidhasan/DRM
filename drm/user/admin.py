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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if request.user.role == 'publisher':
            # Ensure the publisher field is set to the current logged-in publisher
            if 'publisher' in form.base_fields:
                form.base_fields['publisher'].widget.choices = [(request.user.id, request.user.username)]
                if not obj:
                    form.base_fields['publisher'].initial = request.user
                    form.base_fields['publisher'].widget.attrs['readonly'] = 'readonly'
                    form.base_fields['role'].initial = 'author'  # Automatically set role to 'author' when creating a new user
                    form.base_fields['role'].widget.attrs['readonly'] = 'readonly'

        elif request.user.role == 'author':
            # If the user is an author, they can only add users as publishers
            if 'role' in form.base_fields:
                form.base_fields['role'].widget.choices = [('publisher', 'Publisher')]  # Restrict authors to only create publishers
                if not obj:
                    form.base_fields['role'].initial = 'publisher'  # Set role to publisher by default
                    form.base_fields['role'].widget.attrs['readonly'] = 'readonly'  # Make the role field readonly for authors

        return form

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        
        if request.user.role == 'publisher' and not obj.publisher:
            obj.publisher = request.user
        
        # If author is trying to add a user, restrict based on the role
        if request.user.role == 'author' and obj.role != 'publisher':
            self.message_user(request, "Authors can only add users as publishers.", level=messages.ERROR)
            return
        
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

    def has_add_permission(self, request):
        """
        Modify who has the ability to add new users.
        - Publishers can add authors.
        - Authors can add users as publishers only.
        - Customers cannot add users.
        """
        if request.user.role == 'publisher':
            return True  # Publishers can add authors
        if request.user.role == 'author':
            return True  # Authors can only add users as publishers
        return False  # Customers can't add users

    def has_view_permission(self, request, obj=None):
        """
        Modify who has view permission for users.
        - Superusers can view all users.
        - Publishers can view their authors and themselves.
        - Authors can only view themselves and publishers.
        - Publishers cannot view admin users or superadmins.
        """
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            # Publishers can view:
            # - Their own profile
            # - Their authors
            # - Other publishers
            return obj is None or obj.publisher == request.user or obj.role == 'publisher'
        if request.user.role == 'author':
            # Authors can only view themselves and publishers
            return obj is None or obj == request.user or obj.role == 'publisher'
        return False

    def has_change_permission(self, request, obj=None):
        """
        Modify who has the change permission.
        - Superusers can change all users.
        - Publishers can change their authors.
        - Authors can only change themselves.
        """
        if request.user.is_superuser:
            return True
        if request.user.role == 'publisher':
            return obj is None or obj.publisher == request.user
        return obj == request.user  # Authors can only change themselves

    def has_delete_permission(self, request, obj=None):
        """
        Modify who has delete permission.
        - Superusers can delete any user.
        - Publishers can delete their authors.
        - Authors can only delete themselves.
        """
        return self.has_change_permission(request, obj)
