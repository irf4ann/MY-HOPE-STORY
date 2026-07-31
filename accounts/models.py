from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('guest', 'Guest'),
        ('entrepreneur', 'Entrepreneur'),
        ('mentor', 'Mentor'),
        ('investor', 'Investor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
