from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from rest_framework.routers import DefaultRouter
from portfolio.views import ProfileViewSet, ProjectViewSet, CertificateViewSet, github_webhook

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'projects', ProjectViewSet)
router.register(r'certificates', CertificateViewSet)

def home_view(request):
    return render(request, 'index.html', {
        'user': request.user,
        'is_admin': request.user.is_staff if request.user.is_authenticated else False
    })

def custom_logout(request):
    logout(request)
    return redirect('/')

urlpatterns = [
    path('admin/logout/', custom_logout, name='logout'),
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('api/', include('portfolio.urls')),
    path('webhook/github/', github_webhook, name='github_webhook'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)