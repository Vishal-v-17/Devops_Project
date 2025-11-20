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

User = get_user_model()

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
    return render(request, 'home.html',{'edu_books':edu_books,'fiction_books':fiction_books,'science_books':science_books})

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
#@allowed_users(allowed_roles=['admin'])
def addBook(request,user_id):
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        form = EBooksForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            # book.author = user.first_name + " " + user.last_name
            # book.author_id = user.id
            print(book.author)
            book.save()
            print()
            print()
            print(book.author)
            print("Book saved successfully")
            print()
            print()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = EBooksForm()
    return render(request, 'addBook.html', {'form': form})

#@allowed_users(allowed_roles=['admin','customer'])
def viewBook(request,book_id):
    book = EBooksModel.objects.get(id=book_id)
    return render(request, 'viewBook.html', {'book': book})

@login_required
#@allowed_users(allowed_roles=['admin'])
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
    
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:651360790304:BorrowBookNotification"

@login_required(login_url="login")
def borrow_book(request, book_id):
    book = get_object_or_404(EBooksModel, id=book_id)
    user = request.user  # logged-in user

    if request.method == "POST":
        form = BorrowForm(request.POST)

        if form.is_valid():
            borrow_record = form.save(commit=False) 
            borrow_record.book = book
            borrow_record.email = user.email      # 👈 ensure user email is used
            
            # Generate tracking ID
            borrow_record.tracking_code = str(uuid.uuid4())[:8]
            borrow_record.save()
            print("Borrow record ID:", borrow_record.id)
            
            # Mark book as borrowed
            book.is_borrowed = True
            book.save()

            # Prepare email
            subject = f"Borrow Confirmation - {book.title}"
            message = (
                f"Hello {user.username},\n\n"
                f"You have borrowed the book: {book.title}\n\n"
                f"Student ID : {borrow_record.student_id}\n"
                f"Return Date: {borrow_record.return_date}\n"
                f"Tracking Code: {borrow_record.tracking_code}\n\n"
                f"Please keep this tracking code safe.\n"
                f"Thank You!"
            )

            # Send email to logged-in user only
            send_mail(
                subject,
                message,
                'noreply@yourdomain.com',  # from email
                [user.email],              # recipient (logged-in user only)
                fail_silently=False
            )

            return render(request, "borrow_message.html", {"record": borrow_record})

    else:
        # Pre-fill email and student id from logged-in user
        form = BorrowForm(initial={
            "email": user.email,
            "student_id": user.id
        })

    return render(request, "borrow_form.html", {"form": form, "book": book})

def return_book(request, record_id):
    record = get_object_or_404(BorrowRecord, id=record_id)
    book = record.book

    if request.method == "POST":
        # Mark book as available
        book.is_borrowed = False
        book.save()

        # Delete borrow record (or set returned=True if using status)
        record.delete()

        return render(request, "return_message.html", {"book": book})

    return render(request, "return_confirm.html", {"record": record, "book": book})

@allowed_users(allowed_roles=['admin'])
def contri(request,user_id):
    books = EBooksModel.objects.filter(author_id=user_id)
    return render(request, 'contri.html', {'books': books})

