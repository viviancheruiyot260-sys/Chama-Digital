from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/', views.make_payment_view, name='make_payment'),
    path('history/', views.payment_history_view, name='payment_history'),
    path('receipt/<int:receipt_id>/', views.receipt_detail_view, name='receipt_detail'),
    path('receipt/<int:receipt_id>/pdf/', views.receipt_pdf_view, name='receipt_pdf'),
    path('treasurer/', views.treasurer_dashboard_view, name='treasurer_dashboard'),
    path('treasurer/verify/<int:tx_id>/', views.verify_payment_view, name='verify_payment'),
    path('treasurer/notifications/read/', views.mark_notifications_read_view, name='mark_notifications_read'),
    path('treasurer/export-csv/', views.export_ledger_csv_view, name='export_ledger_csv'),
    path('ussd/', views.ussd_info_view, name='ussd_access'),
    path('ussd/callback/', views.ussd_callback_stub, name='ussd_callback'),
]
