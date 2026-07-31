from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Startup(models.Model):
    founder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='startups')
    startup_name = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    founded_year = models.IntegerField(null=True, blank=True)
    team_size = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.startup_name

class Story(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    )

    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
        ('anonymous', 'Anonymous'),
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='stories')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='stories')
    
    title = models.CharField(max_length=200)
    summary = models.TextField(help_text="Short summary of the story")
    
    # Detailed Content mapped from Wizard
    problem_solved = models.TextField(blank=True)
    business_model = models.TextField(blank=True)
    timeline_content = models.TextField(help_text="Timeline from idea to launch to growth")
    challenges = models.TextField(help_text="What went wrong?")
    failure_reason = models.TextField(help_text="Core reason for failure")
    lessons = models.TextField(help_text="What worked and didn't")
    future_plans = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.title}"
