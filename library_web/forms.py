"""Forms for user registration, ebook management, and borrow records."""

# pylint: disable=too-few-public-methods

import datetime
import re
from django import forms
from .models import EBooksModel, User, BorrowRecord

class RegistrationForm(forms.ModelForm):
    """Form for registering a new user."""
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        """Metadata for RegistrationForm."""
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_password2(self):
        """Validate that both passwords match."""
        password_1 = self.cleaned_data.get("password1")
        password_2 = self.cleaned_data.get("password2")

        if password_1 and password_2 and password_1 != password_2:
            raise forms.ValidationError("Passwords don't match")

        return password_2

    def save(self, commit=True):
        """Save the user with a hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class EBooksForm(forms.ModelForm):
    """Form for creating and editing ebooks."""
    CATEGORY_CHOICES = [
        ("Education", "Education"),
        ("NonFriction", "NonFriction"),
        ("Fiction", "Fiction"),
        ("Science", "Science"),
    ]

    category = forms.ChoiceField(choices=CATEGORY_CHOICES)

    rating = forms.IntegerField(
        min_value=0,
        max_value=5,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter rating (0–5)"
            }
        ),
    )

    class Meta:
        """Metadata for EBooksForm."""
        model = EBooksModel
        fields = [
            "title", "description", "image", "category", "subtitle",
            "author", "publisher", "rating", "book_pdf", "book_audio"
        ]
        labels = {
            "title": "Book Title",
            "description": "Short Description",
        }

    def __init__(self, *args, **kwargs):
        """Add Bootstrap classes and make selected fields required."""
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes
        self.fields["title"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter title"}
        )
        self.fields["subtitle"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter Subtitle"}
        )
        self.fields["author"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter Author"}
        )
        self.fields["publisher"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter Publisher"}
        )
        self.fields["description"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter description"}
        )
        self.fields["image"].widget.attrs.update({"class": "form-control"})
        self.fields["category"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Select category"}
        )
        self.fields["book_pdf"].widget.attrs.update({"class": "form-control"})
        self.fields["book_audio"].widget.attrs.update({"class": "form-control"})
        self.fields["rating"].widget.attrs.update({"class": "form-control"})

        # Required fields logic
        for name, field in self.fields.items():
            field.required = name not in ["book_pdf", "book_audio", "publisher"]


class BorrowForm(forms.ModelForm):
    """Form to validate borrow record details."""
    class Meta:
        """Metadata for BorrowForm."""
        model = BorrowRecord
        fields = ["student_id", "return_date"]
        widgets = {
            "student_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Student ID"
                }
            ),
            "return_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),
        }

    def clean_student_id(self):
        """Validate student ID format: must start with 'x' followed by up to 9 digits."""
        student_id = self.cleaned_data["student_id"]

        if not re.fullmatch(r"x\d{0,9}", student_id):
            raise forms.ValidationError(
                "Student ID must start with 'x' and contain only digits (max 10 characters)."
            )

        return student_id

    def clean_return_date(self):
        """Ensure the return date is after today."""
        return_date = self.cleaned_data["return_date"]
        today = datetime.date.today()

        if return_date <= today:
            raise forms.ValidationError("Return date must be later than today.")

        return return_date
