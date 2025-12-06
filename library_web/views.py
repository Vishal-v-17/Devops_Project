"""Views for Library Web application."""
# pylint: disable=no-member

# Standard library imports
import os
from datetime import date

# Third-party imports
#import boto3
#from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.db.models import FileField

# Local imports
from library_web.forms import EBooksForm, RegistrationForm, BorrowForm
from library_web.models import EBooksModel, BorrowRecord
from .decorators import allowed_users


@csrf_protect
def home(request):
    """Display categorized books, top rated, and most borrowed."""
    edu_books = EBooksModel.objects.filter(category="Education")
    fiction_books = EBooksModel.objects.filter(category="Fiction")
    science_books = EBooksModel.objects.filter(category="Science")
    non_fiction_books = EBooksModel.objects.filter(category="NonFriction")
    book_rating = EBooksModel.objects.all().order_by("-rating")
    book_borrow = EBooksModel.objects.all().order_by("-borrow_count")

    return render(
        request,
        "home.html",
        {
            "edu_books": edu_books,
            "fiction_books": fiction_books,
            "science_books": science_books,
            "non_fiction_books": non_fiction_books,
            "book_rating": book_rating,
            "book_borrow": book_borrow,
        },
    )


@csrf_protect
def register_view(request):
    """Handle user registration using RegistrationForm."""
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})


@csrf_protect
def login_view(request):
    """Handle login for users."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid credentials")

    return render(request, "login.html")


def logout_view(request):
    """Logout the current user."""
    django_logout(request)
    return redirect("home")


@csrf_protect
@login_required
@allowed_users(allowed_roles=["admin", "superuser"])
def add_book(request):
    """Add a new book (Admin only)."""
    if request.method == "POST":
        form = EBooksForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.save()
            return redirect("home")
    else:
        form = EBooksForm()

    return render(request, "addBook.html", {"form": form})


@csrf_protect
@login_required(login_url="login")
def borrow_book(request, book_id):
    """Allow a user to borrow a book if not already borrowed."""
    book = get_object_or_404(EBooksModel, id=book_id)
    user = request.user

    active_record = BorrowRecord.objects.filter(
        book=book, actual_return_date__isnull=True
    ).first()

    if active_record:
        messages.error(request, "This book is already borrowed.")
        return redirect("book_detail", book_id=book_id)

    if request.method == "POST":
        form = BorrowForm(request.POST)
        if form.is_valid():
            borrow_record = form.save(commit=False)
            borrow_record.book = book
            borrow_record.user = user
            borrow_record.borrow_date = date.today()

            if borrow_record.borrow_date > borrow_record.return_date:
                messages.error(
                    request,
                    "Return date cannot be before the borrow date.",
                )
                return render(
                    request, "borrow_book.html", {"form": form, "book": book}
                )

            borrow_record.save()
            book.borrow_count += 1
            book.is_borrowed = True
            book.save()

            return render(request, "borrow_message.html", {"record": borrow_record})
    else:
        form = BorrowForm(initial={"student_id": user.id})

    return render(request, "borrow_book.html", {"form": form, "book": book})


@csrf_protect
def return_book(request, book_id):
    """Process the return of a borrowed book."""
    book = get_object_or_404(EBooksModel, id=book_id)

    if not book.is_borrowed:
        messages.error(request, "This book is not currently borrowed.")
        return render(request, "explore.html")

    record = BorrowRecord.objects.filter(
        book=book, actual_return_date__isnull=True
    ).first()

    if not record:
        messages.error(request, "No active borrow record found for this book.")
        return render(request, "explore.html")

    today = date.today()

    if today > record.return_date:
        extra_days = (today - record.return_date).days
        record.late_fee = extra_days * 8
    else:
        record.late_fee = 0

    record.actual_return_date = today
    record.save()

    book.is_borrowed = False
    book.save()

    return render(
        request,
        "return_Book.html",
        {"book": book, "record": record},
    )


@csrf_protect
def view_book(request, book_id):
    """View details of a single book."""
    book = get_object_or_404(EBooksModel, id=book_id)
    return render(request, "viewBook.html", {"book": book})


@csrf_protect
@login_required
@allowed_users(allowed_roles=["admin"])
def edit_book(request, book_id):
    """Edit existing book details (Admin only)."""
    book = get_object_or_404(EBooksModel, id=book_id)

    if request.method == "POST":
        form = EBooksForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = EBooksForm(instance=book)

    return render(request, "editBook.html", {"form": form, "book": book})


@login_required
@allowed_users(allowed_roles=["admin"])
def delete_book(request, book_id):
    """Delete a book and remove associated files."""
    book = get_object_or_404(EBooksModel, id=book_id)

    if request.method == "POST":
        for field in book._meta.get_fields():
            if isinstance(field, FileField):
                file_field = getattr(book, field.name)
                if file_field and os.path.isfile(file_field.path):
                    os.remove(file_field.path)

        book.delete()
        return redirect("home")

    return render(request, "deletebook.html", {"book": book})


@csrf_protect
def explore(request):
    """Explore books page."""
    return render(request, "explore.html")


@csrf_protect
def search_books(request):
    """Search books by title using keyword AND matching."""
    query = request.GET.get("q", "").strip()
    books = EBooksModel.objects.all()

    if query:
        for word in query.split():
            books = books.filter(title__icontains=word)

    return render(
        request,
        "search_books.html",
        {"books": books, "query": query},
    )
