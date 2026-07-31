from django.contrib import admin
from .models import Notification, NotificationPreference, EmailLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    fieldsets = (
        ('Notification Info', {'fields': ('recipient', 'notification_type', 'actor', 'story')}),
        ('Content', {'fields': ('title', 'message', 'icon_url', 'action_url')}),
        ('Status', {'fields': ('read', 'read_at')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_digest', 'email_digest_frequency', 'updated_at')
    list_filter = ('email_digest_frequency', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Email Notifications', {
            'fields': ('email_on_comment', 'email_on_like', 'email_on_mention', 'email_on_mentorship',
                      'email_on_donation', 'email_on_investor_interest', 'email_on_follower_story',
                      'email_digest', 'email_digest_frequency')
        }),
        ('Push Notifications', {
            'fields': ('push_on_comment', 'push_on_like', 'push_on_mentorship',
                      'push_on_donation', 'push_on_investor_interest')
        }),
        ('SMS Notifications', {'fields': ('sms_on_important', 'sms_phone')}),
        ('Timestamps', {'fields': ('updated_at',)}),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'email_type', 'status', 'sent_at')
    list_filter = ('status', 'email_type', 'sent_at')
    search_fields = ('recipient__username', 'subject')
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Email Info', {'fields': ('recipient', 'subject', 'email_type')}),
        ('Status', {'fields': ('status', 'error_message')}),
        ('Timestamps', {'fields': ('sent_at',)}),
    )
