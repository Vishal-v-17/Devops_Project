"""Admin configuration for library_web app"""

from django.contrib import admin
from .models import User, EBooksModel, BorrowRecord

# Register your models here.

admin.site.register(User)
admin.site.register(EBooksModel)
admin.site.register(BorrowRecord)
