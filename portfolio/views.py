import json
import requests
import cloudinary.uploader  # Import the generic uploader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Profile, Project, Certificate, Skill
from .serializers import ProfileSerializer, ProjectSerializer, CertificateSerializer, SkillSerializer

# --- HELPER FUNCTION FOR SKILL CATEGORIZATION ---
def get_skill_category(language_name):
    if not language_name: 
        return 'Soft'
    lang = language_name.lower()
    
    frontend = ['javascript', 'typescript', 'html', 'css', 'vue', 'react', 'angular', 'svelte', 'jsx', 'tsx', 'scss', 'sass', 'dockerfile']
    backend = ['python', 'django', 'java', 'c++', 'ruby', 'php', 'go', 'rust', 'swift', 'sql', 'kotlin', 'scala', 'elixir']
    tools = ['docker', 'git', 'linux', 'bash', 'shell', 'makefile', 'jupyter notebook', 'vim script', 'cuda']
    
    if any(f in lang for f in frontend): 
        return 'Frontend'
    if any(b in lang for b in backend): 
        return 'Backend'
    if any(t in lang for t in tools): 
        return 'Tools'
    return 'Soft'


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        # Returns the first (and usually only) profile
        profile = Profile.objects.first()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        
        # Security check: Only staff can update
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        # 1. Handle Image Upload
        if 'profile_pic' in request.FILES:
            try:
                # Manual upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    request.FILES['profile_pic'],
                    folder='portfolio/profiles',
                    resource_type='image'
                )
                
                # Save the returned URL to the database
                profile.profile_pic = upload_result['secure_url']
                profile.save()
                
                return Response(ProfileSerializer(profile).data)
            except Exception as e:
                return Response({"error": f"Upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 2. Handle Text Updates (Bio, Name, etc)
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
            
            count_new = 0
            count_updated = 0
            
            for repo in repos:
                # 1. Create or Update Project
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
                
                if created:
                    count_new += 1
                else:
                    # Update star count if repo already exists
                    project.stars = repo['stargazers_count']
                    project.save()
                    count_updated += 1

                # 2. DEEP SYNC SKILLS (Get ALL languages for this repo)
                languages_url = repo.get('languages_url')
                
                if languages_url:
                    try:
                        lang_res = requests.get(languages_url)
                        
                        if lang_res.status_code == 200:
                            lang_data = lang_res.json() 
                            
                            for lang_name in lang_data.keys():
                                category = get_skill_category(lang_name)
                                Skill.objects.get_or_create(
                                    name=lang_name,
                                    defaults={'category': category}
                                )
                        elif lang_res.status_code == 403:
                            print(f"Rate limit reached trying to fetch languages for {repo['name']}")
                            print("WARNING: GitHub API Rate Limit Reached. Skills may be incomplete.")
                            
                    except Exception as e:
                        print(f"Error fetching detailed languages for {repo['name']}: {e}")
            
            return Response({
                "message": f"Sync Complete. Added {count_new} new projects. Updated {count_updated} existing. Skills updated with all languages found."
            }, status=status.HTTP_200_OK)
            
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
    # 1. Handle GitHub "Ping" (GET request) - Used to verify the URL is valid
    if request.method == 'GET':
        return HttpResponse('OK', status=200)

    # 2. Handle GitHub "Push" (POST request) - Updates your portfolio
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            
            if 'repository' in payload and 'pusher' in payload:
                repo_data = payload['repository']
                repo_name = repo_data['name']
                repo_url = repo_data['html_url']
                repo_description = repo_data.get('description', "No description provided.")
                
                # 1. Sync Project Info
                project, created = Project.objects.get_or_create(
                    github_url=repo_url,
                    defaults={
                        'title': repo_name,
                        'description': repo_description,
                        'stars': 0, 
                        'tags': 'GitHub, Auto-Synced',
                        'is_synced': True
                    }
                )
                
                if created:
                    print(f"Webhook: New project added - {repo_name}")
                else:
                    if project.description != repo_description:
                        project.description = repo_description
                        project.save()
                    print(f"Webhook: Project updated - {repo_name}")

                # 2. SYNC SKILLS AUTOMATICALLY (Deep Sync Logic)
                languages_url = repo_data.get('languages_url')
                
                if languages_url:
                    try:
                        # Fetch the specific languages for THIS repo
                        lang_res = requests.get(languages_url)
                        
                        if lang_res.status_code == 200:
                            lang_data = lang_res.json()
                            
                            for lang_name in lang_data.keys():
                                category = get_skill_category(lang_name)
                                Skill.objects.get_or_create(
                                    name=lang_name,
                                    defaults={'category': category}
                                )
                    except Exception as e:
                        print(f"Webhook Skill Sync Error: {e}")

                return JsonResponse({'status': 'success', 'message': 'Project synced via Webhook'})

        except Exception as e:
            print(f"Webhook Error: {e}")
            return HttpResponse(str(e), status=400)

    return HttpResponse('Method not allowed', status=405)