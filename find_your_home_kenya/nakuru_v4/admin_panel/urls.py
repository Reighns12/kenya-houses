from django.urls import path
from admin_panel import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Landlords
    path('landlords/', views.landlords_list, name='landlords'),
    path('landlords/<int:landlord_id>/toggle/', views.toggle_landlord_status, name='toggle_landlord'),
    path('landlords/<int:landlord_id>/delete/', views.delete_landlord, name='delete_landlord'),

    # Tenants
    path('tenants/', views.tenants_list, name='tenants'),
    path('tenants/<int:tenant_id>/toggle/', views.toggle_tenant_status, name='toggle_tenant'),

    # Listings
    path('listings/', views.listings, name='listings'),
    path('listings/add/', views.add_property_admin, name='add_property'),
    path('listings/<int:property_id>/approve/', views.approve_property, name='approve_property'),
    path('listings/<int:property_id>/reject/', views.reject_property, name='reject_property'),
    path('listings/<int:property_id>/delete/', views.delete_property, name='delete_property'),

    # Payments
    path('payments/', views.payments_list, name='payments'),
    path('payments/<int:payment_id>/confirm/', views.confirm_payment, name='confirm_payment'),

    # Settings
    path('settings/', views.site_settings, name='settings'),
]
