from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('story_published', 'Story Published'),
        ('story_commented', 'Story Commented'),
        ('story_liked', 'Story Liked'),
        ('follower_story', 'Follower Posted Story'),
        ('mentorship_request', 'Mentorship Request'),
        ('mentorship_accepted', 'Mentorship Accepted'),
        ('mentorship_rejected', 'Mentorship Rejected'),
        ('donation_received', 'Donation Received'),
        ('investor_interested', 'Investor Interested'),
        ('story_approved', 'Story Approved'),
        ('story_rejected', 'Story Rejected'),
        ('comment_reply', 'Comment Reply'),
        ('achievement_unlocked', 'Achievement Unlocked'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_created')
    story = models.ForeignKey('stories.Story', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon_url = models.URLField(blank=True)
    action_url = models.URLField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'read']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Email notifications
    email_on_comment = models.BooleanField(default=True)
    email_on_like = models.BooleanField(default=True)
    email_on_mention = models.BooleanField(default=True)
    email_on_mentorship = models.BooleanField(default=True)
    email_on_donation = models.BooleanField(default=True)
    email_on_investor_interest = models.BooleanField(default=True)
    email_on_follower_story = models.BooleanField(default=True)
    email_digest = models.BooleanField(default=True)
    email_digest_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='weekly')
    
    # In-app notifications
    push_on_comment = models.BooleanField(default=True)
    push_on_like = models.BooleanField(default=True)
    push_on_mentorship = models.BooleanField(default=True)
    push_on_donation = models.BooleanField(default=True)
    push_on_investor_interest = models.BooleanField(default=True)
    
    # SMS notifications (optional)
    sms_on_important = models.BooleanField(default=False)
    sms_phone = models.CharField(max_length=20, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class EmailLog(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_logs')
    subject = models.CharField(max_length=200)
    email_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ], default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Email to {self.recipient.username} - {self.subject}"
