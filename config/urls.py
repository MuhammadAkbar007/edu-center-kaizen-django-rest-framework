"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import GroupViewSet, StudentViewSet, TeacherViewSet  # pyright: ignore[reportMissingImports]

BASE_URL: str = "api/v1/"

# DRF router
router = DefaultRouter()
router.register(BASE_URL + "students", StudentViewSet, basename="students")
router.register(BASE_URL + "teachers", TeacherViewSet, basename="teachers")
router.register(BASE_URL + "groups", GroupViewSet, basename="groups")

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT endpoints
    path(BASE_URL + "token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        BASE_URL + "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    # API endpoints
    path("", include(router.urls)),
]
