from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path('dashboard/', views.member_dashboard_view, name='member_dashboard'),
]
