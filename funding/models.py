from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

class Donation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    story = models.ForeignKey('stories.Story', on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    message = models.TextField(blank=True)
    anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"${self.amount} donation to {self.story.title}"


class CrowdfundingCampaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    story = models.OneToOneField('stories.Story', on_delete=models.CASCADE, related_name='crowdfunding')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(100)])
    target_deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    banner_image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def current_amount(self):
        return sum([d.amount for d in self.story.donations.filter(status='completed')])
    
    def completion_percentage(self):
        current = self.current_amount()
        return (current / self.goal_amount * 100) if self.goal_amount > 0 else 0
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class CrowdfundingReward(models.Model):
    campaign = models.ForeignKey(CrowdfundingCampaign, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)
    description = models.TextField()
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_available = models.IntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    quantity_claimed = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.campaign.title} - {self.title}"


class InvestorInterest(models.Model):
    STATUS_CHOICES = (
        ('interested', 'Interested'),
        ('discussing', 'Discussing'),
        ('funded', 'Funded'),
        ('declined', 'Declined'),
    )
    
    story = models.ForeignKey('stories.Story', on_delete=models.CASCADE, related_name='investor_interests')
    investor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interests')
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('story', 'investor')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Investment Interest - {self.investor.username} in {self.story.title}"


class Grant(models.Model):
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    eligibility_criteria = models.TextField()
    deadline = models.DateTimeField()
    website = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['deadline']
    
    def __str__(self):
        return self.title
