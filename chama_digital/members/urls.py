from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('chairperson/', views.chairperson_dashboard_view, name='chairperson_dashboard'),
    path('chairperson/applications/<int:member_id>/review/', views.review_member_application_view, name='review_application'),
    path('directory/', views.member_directory_view, name='directory'),
    path('directory/<int:member_id>/', views.member_public_profile_view, name='public_profile'),
    path('profile/', views.my_profile_view, name='my_profile'),
]
