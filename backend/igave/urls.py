from django.contrib import admin
from django.urls import path
from igaveapp.views import get_users, register_user, login_user, delete_user


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', register_user),
    path('api/login/', login_user),
    path('api/users/', get_users),
    path('api/users/<int:id>/delete/', delete_user),
] 
