from django.urls import path
from payments import views

app_name = 'payments'

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate'),
    path('check/', views.check_payment, name='check'),
    path('verify/', views.manual_verify, name='manual_verify'),
    path('callback/', views.mpesa_callback, name='callback'),
    path('admin/confirm/<int:payment_id>/', views.admin_confirm_payment, name='admin_confirm'),
    path('admin/reject/<int:payment_id>/', views.admin_reject_payment, name='admin_reject'),
]
