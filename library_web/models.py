"""
Models for the Library Web application.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    """Create a user manager"""
    def create_user(self, username, email, password=None, **extra_fields):
        """Creating a user"""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # securely hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Creating a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Creating a user account"""
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class EBooksModel(models.Model):
    """Creating a eBook details"""
    book_id = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    image = models.ImageField(upload_to="books/")
    rating = models.IntegerField(default=0)
    borrow_count = models.PositiveIntegerField(default=0)
    book_pdf = models.FileField(upload_to="pdfs/", null=True, blank=True)
    book_audio = models.FileField(upload_to="audio/", null=True, blank=True)
    is_borrowed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Saving the ebook data"""
        if not self.book_id:
            self.book_id = "BOOK-" + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        """returning the ebook data"""
        return f"{self.id}"

class BorrowRecord(models.Model):
    """Creating a eBook borrow details"""
    student_id = models.CharField(max_length=50)
    book = models.ForeignKey("EBooksModel", on_delete=models.CASCADE)
    tracking_code = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    borrow_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        """Returing a eBook borrow details """
        return f"{self.student_id} borrowed {self.book.title}"
