from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from igaveapp.views import UserViewSet, ReceiptViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'receipts', ReceiptViewSet, basename='receipt')
from django.urls import path
from igaveapp.views import get_users, register_user, login_user, delete_user


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', register_user),
    path('api/login/', login_user),
    path('api/users/', get_users),
    path('api/users/<int:id>/delete/', delete_user),
] 
