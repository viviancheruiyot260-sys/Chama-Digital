from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.member_loans_view, name='member_loans'),
    path('applications/<int:app_id>/review/', views.review_loan_application_view, name='review_application'),
    path('<int:loan_id>/repay/', views.record_loan_repayment_view, name='record_repayment'),
]
