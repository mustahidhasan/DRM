from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("logout/", views.logout_user, name="logout"),
]
