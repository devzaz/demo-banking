from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from .models import (
    LoginOTP
)
from audit.services import log_action

DEMO_OTP = "123456"

def login_view(request):
    # 🔒 If already logged in, redirect away
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_customer_list")
        return redirect("client_dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user:
            LoginOTP.objects.create(user=user, code=DEMO_OTP)
            request.session["otp_user_id"] = user.id
            return redirect("otp_verify")

        return render(request, "auth/login.html", {
            "error": "Invalid email or password"
        })

    return render(request, "auth/login.html")



def otp_verify(request):

    # If already logged in, do not show OTP again
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")
        return redirect("client_dashboard")
    
    user_id = request.session.get("otp_user_id")
    if not user_id:
        return redirect("login")

    if request.method == "POST":
        otp = request.POST.get("otp")

        otp_obj = LoginOTP.objects.filter(
            user_id=user_id,
            code=otp,
            is_used=False
        ).first()

        if otp_obj:
            otp_obj.is_used = True
            otp_obj.save()

            user = User.objects.get(id=user_id)
            login(
                request, 
                user,
                backend="accounts.auth_backend.EmailBackend"
                )
            log_action(
                user=request.user,
                action="LOGIN",
                description="User logged in successfully"
            )
            
            del request.session["otp_user_id"]

            if user.is_staff:
                return redirect("admin_dashboard")
            return redirect("client_dashboard")

        return render(request, "auth/otp.html", {"error": "Invalid OTP"})

    return render(request, "auth/otp.html")


def logout_view(request):
    logout(request)
    return redirect("login")