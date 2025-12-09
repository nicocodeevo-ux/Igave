from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@api_view(["GET"])
def get_users(request):
    users = User.objects.all().values("id", "username", "password", "date_joined", "is_staff")
    return JsonResponse(list(users), safe=False)

@csrf_exempt
def delete_user(request, id):
    if request.method == "DELETE":
        try:
            user = User.objects.get(id=id)
            user.delete()
            return JsonResponse({"message": "User deleted"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "User already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    return JsonResponse({"success": True, "message": "User created"})
    

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "username": user.username,
                "is_staff": user.is_staff,
            })
        else:
            return JsonResponse({"success": False, "error": "Invalid credentials"}, status=400)

