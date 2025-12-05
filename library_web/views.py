from django.shortcuts import redirect, render, get_object_or_404
from library_web.forms import EBooksForm, RegistrationForm, BorrowForm
from library_web.models import EBooksModel, BorrowRecord
from django.contrib.auth.models import auth, Group
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import unauthenticated_user, allowed_users
from django.db.models import FileField
import os, uuid, boto3
from django.core.mail import send_mail
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

import re, uuid
from datetime import date
from django.db.models import Q

# Create your views here.

# @unauthenticated_user
# def Registers(request):
#     if request.method == 'POST':
#         email = request.POST['email']
#         password = request.POST['password']
#         firstName = request.POST['first--name']
#         lastName = request.POST['last--name']

#         # Check if a user with the same username already exists
#         if User.objects.filter(username=email).exists():
#             messages.info(request,'User already exists')
#             return render(request, 'register.html')
#         else:
#             # Create a new user
#             register = User.objects.create_user(username=email,password=password,first_name=firstName,last_name=lastName)
#             group = Group.objects.get(name='customer')
#             register.groups.add(group)
            
#             # No need to call save() after create_user(), as it's already saved
#             return redirect('login')
#     else:
#         return render(request, 'register.html')
    
# @unauthenticated_user
# def Login(request):
#     if request.method == 'POST':
#         email = request.POST['email']
#         password = request.POST['password']

#         user = auth.authenticate(username=email, password=password)

#         if user is not None:
#             auth.login(request, user)
#             print('User logged in successfully')
#             return redirect('home')
#         else:
#             messages.info(request,'Invalid Credentials')
#             return render(request, 'login.html')
#     else:
#         return render(request, 'login.html')
    


def home(request):
    edu_books = EBooksModel.objects.filter(category='Education')
    fiction_books = EBooksModel.objects.filter(category='Fiction')
    science_books = EBooksModel.objects.filter(category='Science')
    non_fiction_books = EBooksModel.objects.filter(category='NonFriction')
    book_rating = EBooksModel.objects.all().order_by('-rating')
    book_borrow = EBooksModel.objects.all().order_by('-borrow_count')
    return render(request, 'home.html',{'edu_books':edu_books,'fiction_books':fiction_books,'science_books':science_books,'non_fiction_books':non_fiction_books,'book_rating': book_rating,'book_borrow': book_borrow})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pw = request.POST.get('password')
        user = authenticate(request, username=username, password=pw)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('home')


@login_required
@allowed_users(allowed_roles=['admin', 'superuser'])
def addBook(request, user_id):
    if request.method == 'POST':
        form = EBooksForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.save()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = EBooksForm()

    return render(request, 'addBook.html', {'form': form})

@login_required(login_url="login")
def borrow_book(request, book_id):
    book = get_object_or_404(EBooksModel, id=book_id)
    user = request.user

    active_record = BorrowRecord.objects.filter(
        book=book,
        actual_return_date__isnull=True
    ).first()

    if active_record:
        messages.error(request, "This book is already borrowed.")
        return redirect('book_detail', book_id=book_id)

    if request.method == "POST":
        form = BorrowForm(request.POST)

        if form.is_valid():
            borrow_record = form.save(commit=False)
            borrow_record.book = book
            borrow_record.user = user
            borrow_record.borrow_date = date.today()

            # Validate: borrow_date should not be after return_date (due_date)
            if borrow_record.borrow_date > borrow_record.return_date:
                messages.error(request, "Return date cannot be before the borrow date.")
                return render(request, "borrow_book.html", {"form": form, "book": book})

            # Save record safely
            borrow_record.save()

            # Update book status
            book.borrow_count += 1
            book.is_borrowed = True
            book.save()
            return render(request, "borrow_message.html", {"record": borrow_record})

    else:
        form = BorrowForm(initial={
            "student_id": user.id
        })

    return render(request, "borrow_book.html", {"form": form, "book": book})

def return_book(request, book_id):
    book = get_object_or_404(EBooksModel, id=book_id)

    if not book.is_borrowed:
        messages.error(request, "This book is not currently borrowed.")
        return render(request, 'explore.html')

    # Get active borrow record
    record = BorrowRecord.objects.filter(book=book, actual_return_date__isnull=True).first()

    if not record:
        messages.error(request, "No active borrow record found for this book.")
        return render(request, 'explore.html')

    today = date.today()

    # Calculate late fee based on due date
    if today > record.return_date:
        extra_days = (today - record.return_dat).days
        record.late_fee = extra_days * 8
    else:
        record.late_fee = 0

    # Mark as returned today
    record.actual_return_date = today
    record.save()

    # Update book status
    book.is_borrowed = False
    book.save()

    return render(request, 'return_Book.html', {
        'book': book,
        'record': record
    })

#@allowed_users(allowed_roles=['admin','customer'])
def viewBook(request,book_id):
    book = EBooksModel.objects.get(id=book_id)
    return render(request, 'viewBook.html', {'book': book})

@login_required
@allowed_users(allowed_roles=['admin'])
def editBook(request,book_id):
    book = EBooksModel.objects.get(id=book_id)
    if request.method == 'POST':
        form = EBooksForm(request.POST, request.FILES,instance=book)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = EBooksForm(instance=book)
    return render(request, 'editBook.html', {'form': form,'book':book})

@login_required
@allowed_users(allowed_roles=['admin'])
def deleteBook(request,book_id):
    book = EBooksModel.objects.get(id=book_id)
    
    if request.method == "POST":
        # Loop through all FileField / ImageField in the model
        for field in book._meta.get_fields():
            if isinstance(field, FileField):
                file_field = getattr(book, field.name)
                if file_field and os.path.isfile(file_field.path):
                    os.remove(file_field.path)
            
        # Finally delete the database record    
        book.delete()
        return redirect('home')

    return render(request, 'deletebook.html', {'book': book})

def explore(request):
    # pass context as needed
    return render(request, 'explore.html')

def search_books(request):
    query = request.GET.get("q", "").strip()
    books = EBooksModel.objects.all()

    if query:
        keywords = query.split()  # Split into words

        # Apply AND filter: each word must be in the title
        for word in keywords:
            books = books.filter(title__icontains=word)

    return render(request, "search_books.html", {
        "books": books,
        "query": query
    })
