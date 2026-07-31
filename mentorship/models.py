from django.db import models
from django.conf import settings
from django.utils import timezone

class MentorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise_areas = models.CharField(max_length=500, help_text="Comma-separated areas of expertise")
    years_experience = models.IntegerField()
    languages = models.CharField(max_length=200, blank=True)
    availability = models.CharField(max_length=50, choices=[
        ('available', 'Available'),
        ('limited', 'Limited Availability'),
        ('unavailable', 'Not Available'),
    ], default='available')
    hourly_rate = models.IntegerField(null=True, blank=True, help_text="In USD, 0 for free")
    bio = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Mentor - {self.user.username}"


class MentorshipRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='requests')
    founder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_requests')
    story = models.ForeignKey('stories.Story', on_delete=models.CASCADE, null=True, blank=True, related_name='mentorship_requests')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Mentorship Request - {self.founder.username} → {self.mentor.user.username}"


class MentorshipSession(models.Model):
    request = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='sessions')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    notes = models.TextField(blank=True)
    feedback_from_mentor = models.TextField(blank=True)
    feedback_from_founder = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"Session - {self.request.mentor.user.username} & {self.request.founder.username}"


class MentorReview(models.Model):
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.mentor.user.username} - {self.rating}★"
