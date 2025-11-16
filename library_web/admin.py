from django.contrib import admin
from .models import User, EBooksModel

# Register your models here.

admin.site.register(User)
admin.site.register(EBooksModel)