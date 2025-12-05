from django import forms
from .models import EBooksModel, User, BorrowRecord
import datetime, re

class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class EBooksForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('Education', 'Education'),
        ('NonFriction', 'NonFriction'),
        ('Fiction', 'Fiction'),
        ('Science', 'Science'),
    ]

    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    
    rating = forms.IntegerField(
        min_value=0,
        max_value=5,
        required=False,  # Optional, defaults to model default=0
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter rating (0–5)'
        })
    )

    class Meta:
        model = EBooksModel
        fields = ['title', 'description', 'image', 'category', 'subtitle', 'author', 'publisher','rating', 'book_pdf', 'book_audio']
        labels = {
            'title': 'Book Title',
            'description': 'Short Description',
        }

    def __init__(self, *args, **kwargs):
        super(EBooksForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter title'})
        self.fields['subtitle'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Subtile'})
        self.fields['author'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Author'})
        self.fields['publisher'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Publisher'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter description'})
        self.fields['image'].widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Select category'})
        self.fields['book_pdf'].widget.attrs.update({'class': 'form-control'})
        self.fields['book_audio'].widget.attrs.update({'class': 'form-control'})
        self.fields['rating'].widget.attrs.update({'class': 'form-control'})
        
        # Make all fields required
        for field_name, field in self.fields.items():
            if field_name not in ['book_pdf', 'book_audio', 'publisher']:
                field.required = True
            else:
                field.required = False

class BorrowForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['student_id', 'return_date']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Student ID'}),
            'return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    # Validate student_id
    def clean_student_id(self):
        sid = self.cleaned_data['student_id']

        if not re.fullmatch(r"x\d{0,9}", sid):
            raise forms.ValidationError(
                "Student ID must start with 'x' and contain only digits (max 10 characters)."
            )

        return sid

    # Validate return_date
    def clean_return_date(self):
        return_date = self.cleaned_data['return_date']
        today = datetime.date.today()

        if return_date <= today:
            raise forms.ValidationError("Return date must be later than today.")

        return return_date