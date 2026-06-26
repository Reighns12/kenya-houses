from django.urls import path
from landlords import views

app_name = 'landlords'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('payment/', views.payment_page, name='payment'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post-property/', views.post_property, name='post_property'),
    path('my-properties/', views.my_properties, name='my_properties'),
    path('edit-property/<int:property_id>/', views.edit_property, name='edit_property'),
    path('delete-property/<int:property_id>/', views.delete_property, name='delete_property'),
    path('profile/', views.profile, name='profile'),
]
