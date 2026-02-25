from rest_framework import serializers
from .models import Profile, Project, Certificate, Skill

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    tags_list = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'tags_list', 'github_url', 'stars', 'created_at']
    def get_tags_list(self, obj):
        return [tag.strip() for tag in obj.tags.split(',') if tag]

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'name', 'issuer', 'issue_date', 'credential_url', 'credential_file']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category']