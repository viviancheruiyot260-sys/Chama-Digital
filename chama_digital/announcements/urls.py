from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list_view, name='list'),
    path('create/', views.create_announcement_view, name='create'),
    path('<int:pk>/', views.announcement_detail_view, name='detail'),
]
