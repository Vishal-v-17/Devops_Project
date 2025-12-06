"""URL configuration for library_web app"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('register/', views.register_view, name='register'),
  path('login', views.login_view, name='login'),
  path('logout/', views.logout_view, name='logout'),
  path('explore/', views.explore, name='explore'),
  path('addBook/', views.add_book, name='addBook'),
  path('editbook/<int:book_id>/', views.edit_book, name='editBook'),
  path('deletebook/<int:book_id>/', views.delete_book, name='deleteBook'),
  path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
  path('viewBook/<int:book_id>', views.view_book, name='viewBook'),
  path("return/<int:book_id>/", views.return_book, name="return_book"),
  path("search/", views.search_books, name="search_books"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
