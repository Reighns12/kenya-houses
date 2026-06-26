from django.urls import path
from tenants import views

app_name = 'tenants'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('browse/', views.browse, name='browse'),
    path('preview/<int:property_id>/', views.property_preview, name='property_preview'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('subscribe/', views.payment_page, name='payment'),
    path('home/', views.home, name='home'),
    path('property/<int:property_id>/', views.property_detail, name='property_detail'),
    path('save/<int:property_id>/', views.toggle_save, name='toggle_save'),
    path('saved/', views.saved_properties, name='saved'),
    path('profile/', views.profile, name='profile'),
]
