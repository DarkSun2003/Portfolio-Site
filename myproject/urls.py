from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from rest_framework.routers import DefaultRouter
from portfolio.views import ProfileViewSet, ProjectViewSet, CertificateViewSet, SkillViewSet, github_webhook # <--- IMPORT GITHUB_WEBHOOK

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'projects', ProjectViewSet)
router.register(r'certificates', CertificateViewSet)
router.register(r'skills', SkillViewSet)

def home_view(request):
    return render(request, 'index.html', {
        'user': request.user,
        'is_admin': request.user.is_staff if request.user.is_authenticated else False
    })

# Custom logout to prevent default "Logged Out" page
def custom_logout(request):
    logout(request)
    return redirect('/')

urlpatterns = [
    # 1. Custom Logout
    path('admin/logout/', custom_logout, name='logout'),

    # 2. Admin
    path('admin/', admin.site.urls),

    # 3. Home Page
    path('', home_view, name='home'),
    
    # 4. API Endpoints
    path('api/', include('portfolio.urls')),
    
    # 5. THE WEBHOOK (Must be here!)
    path('webhook/github/', github_webhook, name='github_webhook'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)