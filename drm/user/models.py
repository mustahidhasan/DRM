from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('publisher', 'Publisher'),
        ('author', 'Author'),
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    publisher = models.ForeignKey('self', related_name='authors', on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.pk:
            self.is_staff = True  # Ensure the user can access the admin if it's a new user
        if self.role == 'author' and not self.publisher:
            raise ValueError("Author must be assigned to a publisher.")
        super().save(*args, **kwargs)

    def has_module_perms(self, app_label):
        if self.role == 'customer':
            return False
        return super().has_module_perms(app_label)

    def has_perm(self, perm, obj=None):
        if self.role == 'customer':
            return False
        return super().has_perm(perm, obj)

    def __str__(self):
        return f"{self.username} ({self.role})"

class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book_name = models.CharField(max_length=200, blank=True, null=True)
    book_description = models.TextField(max_length=400, blank=True, null=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)  # <-- Added field
    price = models.DecimalField(decimal_places=2, max_digits=10,)
    file_created_at = models.DateTimeField(auto_now=True)
    is_archieved = models.BooleanField(default=False)

    def __str__(self):
        return self.book_name or self.file.name

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="orders", 
        null=True,  # Allow guests (non-logged-in users)
        blank=True
    )
    transaction_id = models.CharField(max_length=255, unique=True)
    tx_ref = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=50)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=255)
    customer_mobile = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.tx_ref}"
