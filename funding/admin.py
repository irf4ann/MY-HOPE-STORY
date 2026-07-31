from django.contrib import admin
from .models import Donation, CrowdfundingCampaign, CrowdfundingReward, InvestorInterest, Grant

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('story', 'donor', 'amount', 'status', 'anonymous', 'created_at')
    list_filter = ('status', 'anonymous', 'created_at')
    search_fields = ('story__title', 'donor__username', 'message')
    readonly_fields = ('created_at', 'completed_at')
    fieldsets = (
        ('Donation Info', {'fields': ('story', 'donor', 'amount', 'message', 'anonymous')}),
        ('Payment', {'fields': ('status', 'stripe_payment_id')}),
        ('Timestamps', {'fields': ('created_at', 'completed_at')}),
    )


@admin.register(CrowdfundingCampaign)
class CrowdfundingCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'goal_amount', 'status', 'target_deadline', 'created_at')
    list_filter = ('status', 'created_at', 'target_deadline')
    search_fields = ('title', 'creator__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Campaign Info', {'fields': ('story', 'title', 'description', 'creator')}),
        ('Funding', {'fields': ('goal_amount', 'target_deadline')}),
        ('Settings', {'fields': ('status', 'banner_image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CrowdfundingReward)
class CrowdfundingRewardAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'title', 'minimum_amount', 'quantity_available', 'quantity_claimed')
    list_filter = ('campaign', 'minimum_amount')
    search_fields = ('campaign__title', 'title', 'description')
    fieldsets = (
        ('Reward Info', {'fields': ('campaign', 'title', 'description')}),
        ('Constraints', {'fields': ('minimum_amount', 'quantity_available', 'quantity_claimed')}),
    )


@admin.register(InvestorInterest)
class InvestorInterestAdmin(admin.ModelAdmin):
    list_display = ('story', 'investor', 'investment_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('story__title', 'investor__username', 'message')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Interest Info', {'fields': ('story', 'investor', 'investment_amount', 'message')}),
        ('Status', {'fields': ('status',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'amount', 'deadline')
    list_filter = ('deadline', 'amount')
    search_fields = ('title', 'organization', 'description')
    fieldsets = (
        ('Grant Info', {'fields': ('title', 'organization', 'description')}),
        ('Funding', {'fields': ('amount', 'deadline')}),
        ('Details', {'fields': ('eligibility_criteria', 'website')}),
    )
