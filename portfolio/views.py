import json
import requests
import cloudinary.uploader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Profile, Project, Certificate, Skill
from .serializers import ProfileSerializer, ProjectSerializer, CertificateSerializer, SkillSerializer

def get_skill_category(language_name):
    if not language_name: return 'Soft'
    lang = language_name.lower()
    frontend = ['javascript', 'typescript', 'html', 'css', 'vue', 'react', 'angular', 'svelte', 'jsx', 'tsx', 'scss', 'sass', 'dockerfile']
    backend = ['python', 'django', 'java', 'c++', 'ruby', 'php', 'go', 'rust', 'swift', 'sql', 'kotlin', 'scala', 'elixir']
    tools = ['docker', 'git', 'linux', 'bash', 'shell', 'makefile', 'jupyter notebook', 'vim script', 'cuda']
    if any(f in lang for f in frontend): return 'Frontend'
    if any(b in lang for b in backend): return 'Backend'
    if any(t in lang for t in tools): return 'Tools'
    return 'Soft'

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        profile = Profile.objects.first()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        if 'profile_pic' in request.FILES:
            try:
                upload_result = cloudinary.uploader.upload(
                    request.FILES['profile_pic'],
                    folder='portfolio/profiles',
                    resource_type='image'
                )
                profile.profile_pic = upload_result['secure_url']
                profile.save()
                return Response(ProfileSerializer(profile).data)
            except Exception as e:
                return Response({"error": f"Upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(ProfileSerializer(profile).data)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def sync_all_github(self, request):
        github_username = "DarkSun2003" 
        api_url = f"https://api.github.com/users/{github_username}/repos?per_page=100"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            repos = response.json()
            count_new = 0; count_updated = 0
            for repo in repos:
                project, created = Project.objects.get_or_create(
                    github_url=repo['html_url'],
                    defaults={
                        'title': repo['name'],
                        'description': repo['description'] or "No description provided.",
                        'stars': repo['stargazers_count'],
                        'tags': 'GitHub, Project',
                        'is_synced': True
                    }
                )
                if created: count_new += 1
                else:
                    project.stars = repo['stargazers_count']
                    project.save()
                    count_updated += 1
                languages_url = repo.get('languages_url')
                if languages_url:
                    try:
                        lang_res = requests.get(languages_url)
                        if lang_res.status_code == 200:
                            for lang_name in lang_res.json().keys():
                                category = get_skill_category(lang_name)
                                Skill.objects.get_or_create(name=lang_name, defaults={'category': category})
                    except: pass
            return Response({"message": f"Sync Complete. Added {count_new} new. Updated {count_updated}. Skills updated."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

@csrf_exempt 
def github_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            if 'repository' in payload and 'pusher' in payload:
                repo_data = payload['repository']
                project, created = Project.objects.get_or_create(
                    github_url=repo_data['html_url'],
                    defaults={'title': repo_data['name'], 'description': repo_data.get('description', "No desc."), 'stars': 0, 'tags': 'GitHub, Auto', 'is_synced': True}
                )
                if created: print(f"New: {repo_data['name']}")
                languages_url = repo_data.get('languages_url')
                if languages_url:
                    try:
                        lang_res = requests.get(languages_url)
                        if lang_res.status_code == 200:
                            for lang_name in lang_res.json().keys():
                                Skill.objects.get_or_create(name=lang_name, defaults={'category': get_skill_category(lang_name)})
                    except: pass
                return JsonResponse({'status': 'success'})
        except: return HttpResponse(str(e), status=400)
    return HttpResponse('Method not allowed', status=405)