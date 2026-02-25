from django.contrib import admin
from .models import Profile, Project, Certificate, Skill
from django import forms
import cloudinary.uploader

class ProfileAdminForm(forms.ModelForm):
    profile_pic_upload = forms.ImageField(required=False, label="Upload New Profile Picture")
    class Meta:
        model = Profile
        fields = '__all__'
    def clean(self):
        cleaned_data = super().clean()
        if self.files.get('profile_pic_upload'):
            try:
                res = cloudinary.uploader.upload(self.files.get('profile_pic_upload'), folder='portfolio/profiles', resource_type='image')
                cleaned_data['profile_pic'] = res['secure_url']
            except Exception as e: raise forms.ValidationError(f"Upload Failed: {e}")
        return cleaned_data

class CertificateAdminForm(forms.ModelForm):
    credential_file_upload = forms.FileField(required=False, label="Upload Certificate File")
    class Meta:
        model = Certificate
        fields = '__all__'
    def clean(self):
        cleaned_data = super().clean()
        if self.files.get('credential_file_upload'):
            try:
                res = cloudinary.uploader.upload(self.files.get('credential_file_upload'), folder='portfolio/certificates', resource_type='auto')
                cleaned_data['credential_file'] = res['secure_url']
            except Exception as e: raise forms.ValidationError(f"Upload Failed: {e}")
        return cleaned_data

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ('full_name', 'role', 'email')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    form = CertificateAdminForm
    list_display = ('name', 'issuer', 'issue_date')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'stars', 'is_synced')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')