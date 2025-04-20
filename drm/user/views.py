UPLOAD_DIR = "uploaded_files/"  # Directory to save uploaded files


import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from .models import UploadedFile, Order
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
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.html import escape  # To prevent HTML injection if username is echoed

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator  # If you use class-based views
from django.shortcuts import render
import requests
import json
import uuid
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from drm.settings import REDIRECT_SITE_URL_ROOT, PAYMENT_AUTH_TOKEN
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

# Use the custom user model
User = get_user_model()


def home(request):
    books = UploadedFile.objects.filter(is_archieved=False).order_by('-uploaded_at')

    return render(request, "home.html",  {'books': books})



@csrf_exempt
def checkout_view(request):
    user = request.user if not isinstance(request.user, AnonymousUser) else None

    if request.method == "POST":
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        transaction_uuid = uuid.uuid4()

        # Save phone number and cart data to session
        request.session["customer_phone"] = phone

        cart_json = request.POST.get("cart_data", "[]")
        try:
            cart = json.loads(cart_json)
        except json.JSONDecodeError:
            cart = []
        request.session["cart"] = cart
        request.session.modified = True

        tx_ref = f"TX-{transaction_uuid}-{email}"
        redirect_url = f"{REDIRECT_SITE_URL_ROOT}/payment-complete/"

        headers = {
            "Authorization": f"Bearer {PAYMENT_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": "USD",
            "redirect_url": redirect_url,
            "payment_options": "card,banktransfer",
            "customer": {
                "email": email,
                "name": full_name,
            },
            "customizations": {
                "title": "DRM Purchase",
                "description": "Payment for Order",
            }
        }

        response = requests.post("https://api.flutterwave.com/v3/payments", headers=headers, data=json.dumps(payload))
        res_data = response.json()

        if res_data.get("status") == "success":
            return redirect(res_data["data"]["link"])
        else:
            return render(request, "payment.html", {
                "success": False,
                "error": res_data.get("message", "Something went wrong.")
            })

    # Fallback if user is not authenticated
    full_name = user.get_full_name() if user else ""
    email = user.email if user else ""

    return render(request, 'checkout.html', {
        "data": {
            "full_name": full_name,
            "email": email,
        }
    })


@csrf_exempt
def payment_complete_view(request):
    transaction_id = request.GET.get('transaction_id', "")
    customer_mobile = request.session.pop("customer_phone", "")
    cart_data = request.session.pop("cart", [])

    # ✅ Extract uploaded_file_ids from cart
    uploaded_file_ids = [item.get("id") for item in cart_data if "id" in item]

    if not transaction_id:
        return render(request, "payment.html", {
            "success": False,
            "error": "Missing transaction ID in the request."
        })

    headers = {
        "Authorization": f"Bearer {PAYMENT_AUTH_TOKEN}"
    }

    verify_url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    response = requests.get(verify_url, headers=headers)
    res_data = response.json()

    if res_data.get("status") == "success" and res_data["data"]["status"] == "successful":
        payment_data = res_data["data"]
        user = request.user if request.user.is_authenticated else None

        # Create order
        order = Order.objects.create(
            user=user,
            transaction_id=payment_data["id"],
            tx_ref=payment_data["tx_ref"],
            amount=payment_data["amount"],
            currency=payment_data["currency"],
            payment_type=payment_data.get("payment_type", ""),
            payment_status=payment_data["status"],
            customer_email=payment_data["customer"]["email"],
            customer_mobile=customer_mobile,
            customer_name=payment_data["customer"]["name"],
        )

        # ✅ Attach uploaded files from cart
        if uploaded_file_ids:
            uploaded_files = UploadedFile.objects.filter(id__in=uploaded_file_ids)
            order.uploaded_files.set(uploaded_files)

        return render(request, "payment.html", {
            "success": True,
            "payment": res_data["data"],
            "customer_phone": customer_mobile,
            "created_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        return render(request, "payment.html", {
            "success": False,
            "error": res_data.get("message", "Transaction verification failed.")
        })

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



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, "login.html", {
                "username": username
            })

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == 'customer':
                login(request, user)
                tokens = get_tokens_for_user(user)

                # Optionally store tokens in session
                request.session['access_token'] = tokens['access']
                request.session['refresh_token'] = tokens['refresh']

                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home')  # Redirect to customer dashboard or home
            else:
                messages.error(request, "Only customers can log in from here.")
        else:
            messages.error(request, "Invalid username or password.")

        return render(request, "login.html", {
            "username": username,
        })

    return render(request, "login.html")



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import CustomerProfileForm

@login_required
def profile_view(request):
    user = request.user
    if user.role != "customer":
        return redirect('home')  # Optional: restrict to customers

    if request.method == "POST":
        form = CustomerProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = CustomerProfileForm(instance=user)

    return render(request, "profile.html", {
        "form": form,
        "user_data": user
    })

@login_required(login_url='login')
def books_view(request):

    return render(request, "books.html")