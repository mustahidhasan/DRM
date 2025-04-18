UPLOAD_DIR = "uploaded_files/"  # Directory to save uploaded files


import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from .models import UploadedFile
from .forms import SignUpForm
from django.core.exceptions import ValidationError
import jwt
import datetime
from drm.settings import SECRET_KEY
from user.auth_backend import EmailOrUsernameBackend
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

# Use the custom user model
User = get_user_model()


def home(request):
    books = UploadedFile.objects.filter(is_archieved=False).order_by('-uploaded_at')

    return render(request, "home.html",  {'books': books})

@csrf_exempt  # For demo purposes only. In production, handle CSRF properly.
def checkout_view(request):
    return render(request, 'checkout.html')

def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect(login_view)



def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if password and confirm password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        # Check if email is already used
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        try:
            # Create the user with the custom user model
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='customer'  # Ensuring the role is set to 'customer'
            )
            user.is_staff = False  # Prevent admin access
            user.save()

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')

    return render(request, "register.html")



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == 'customer':
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home')  # or your customer home route
            else:
                messages.error(request, "Only customers can log in from here.")
        else:
            messages.error(request, "Invalid username or password.")

        # In both failed cases, re-render login with messages
        return render(request, "login.html", {
            "username": username,
        })

    return render(request, "login.html")

def profile_view(request):
    return render(request, "profile.html")