from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    path('', views.meetings_list_view, name='list'),
    path('secretary/', views.secretary_dashboard_view, name='secretary_dashboard'),
    path('events/<int:pk>/edit/', views.edit_event_view, name='edit_event'),
    path('events/<int:pk>/toggle-cancel/', views.cancel_event_view, name='toggle_cancel'),
]
