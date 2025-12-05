from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
  path('', views.home, name='home'),
  #path('explore/', views.explore, name='explore'),
  path('register/', views.register_view, name='register'),
  path('login', views.login_view, name='login'),
  path('logout/', views.logout, name='logout'),
  path('explore/', views.explore, name='explore'),
  path('addBook/<int:user_id>', views.addBook, name='addBook'),
  path('editbook/<int:book_id>/', views.editBook, name='editBook'),
  path('deletebook/<int:book_id>/', views.deleteBook, name='deleteBook'),
  path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
  # path('return/<int:record_id>/', views.return_book, name='return_book'),
  path('logout', views.logout, name='logout'),
  path('viewBook/<int:book_id>', views.viewBook, name='viewBook'),
  path("return/<int:book_id>/", views.return_book, name="return_book"),
  path("search/", views.search_books, name="search_books"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)