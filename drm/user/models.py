from django.db import models
from django.contrib.auth.models import User


from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('publisher', 'Publisher'),
        ('author', 'Author'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='super_admin')

    def save(self, *args, **kwargs):
        if not self.pk:  # New user being created
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


from django.conf import settings

class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name
