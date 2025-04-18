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
    return render(request, "register.html")
    
def login_view(request):
    return render(request, "login.html")