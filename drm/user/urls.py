from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment-complete/', views.payment_complete_view, name='payment-complete'),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_user, name="logout"),

    path("profile/", views.profile_view, name="profile"),
]
