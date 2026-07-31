from django.contrib import admin
from .models import MentorProfile, MentorshipRequest, MentorshipSession, MentorReview

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'years_experience', 'availability', 'verified', 'created_at')
    list_filter = ('verified', 'availability', 'created_at')
    search_fields = ('user__username', 'expertise_areas')
    readonly_fields = ('created_at', 'verification_date')
    fieldsets = (
        ('User Info', {'fields': ('user', 'verified', 'verification_date')}),
        ('Profile Details', {'fields': ('expertise_areas', 'years_experience', 'languages', 'bio')}),
        ('Settings', {'fields': ('availability', 'hourly_rate')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'founder', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('mentor__user__username', 'founder__username', 'message')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Request Info', {'fields': ('mentor', 'founder', 'story', 'message')}),
        ('Status', {'fields': ('status',)}),
        ('Timings', {'fields': ('started_at', 'completed_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(MentorshipSession)
class MentorshipSessionAdmin(admin.ModelAdmin):
    list_display = ('request', 'scheduled_at', 'duration_minutes', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('request__mentor__user__username', 'request__founder__username')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Session Info', {'fields': ('request', 'scheduled_at', 'duration_minutes', 'completed')}),
        ('Feedback', {'fields': ('notes', 'feedback_from_mentor', 'feedback_from_founder')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(MentorReview)
class MentorReviewAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('mentor__user__username', 'reviewer__username', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Review Info', {'fields': ('mentor', 'reviewer', 'rating', 'comment')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
