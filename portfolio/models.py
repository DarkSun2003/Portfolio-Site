from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, default="Your Name")
    role = models.CharField(max_length=150, default="Developer")
    bio = models.TextField()
    profile_pic = models.URLField(default='https://via.placeholder.com/300', blank=True)
    email = models.EmailField()
    linkedin_url = models.URLField(blank=True)
    discord_url = models.URLField(blank=True, verbose_name="Discord Link")
    instagram_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True, verbose_name="WhatsApp Number")

    def __str__(self): return self.full_name

class Project(models.Model):
    github_url = models.URLField(unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.CharField(max_length=500, blank=True)
    stars = models.IntegerField(default=0)
    is_synced = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

class Certificate(models.Model):
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    credential_url = models.URLField(blank=True)
    credential_file = models.URLField(blank=True)
    issue_date = models.DateField()
    source = models.CharField(max_length=50, default="Manual")

    def __str__(self): return f"{self.name} - {self.issuer}"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, default='Soft')

    def __str__(self): return f"{self.name} ({self.category})"