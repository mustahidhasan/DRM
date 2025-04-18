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

def home(request):
    books = UploadedFile.objects.filter(is_archieved=False).order_by('-uploaded_at')

    return render(request, "home.html",  {'books': books})


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


def register_user(request):
    return redirect("home")
    # if request.method == "POST":
    #     form = SignUpForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         # authenticate and login
    #         username = form.cleaned_data["username"]
    #         password = form.cleaned_data["password1"]
    #         # user = authenticate(username=username, password=password)
    #         # login(request, user)
    #         messages.success(request, "You have successfully Registered")
    #         return redirect("home")
    # else:
    #     # form = SignUpForm()
    #     # return render(request, "register.html", {"form": form})
    # return render(request, "register.html", {"form": form})
