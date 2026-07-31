from django.contrib import admin
from .models import Comment, Like, Bookmark, Follow, Report, Badge, UserBadge, Discussion

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'story', 'created_at', 'parent_comment')
    list_filter = ('created_at', 'story__category')
    search_fields = ('author__username', 'content', 'story__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Comment Info', {'fields': ('story', 'author', 'content', 'parent_comment')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'story', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'story__title')
    readonly_fields = ('created_at',)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'story', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'story__title')
    readonly_fields = ('created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    readonly_fields = ('created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('story', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('story__title', 'description')
    readonly_fields = ('created_at', 'resolved_at')
    fieldsets = (
        ('Report Info', {'fields': ('story', 'reporter', 'reason', 'description')}),
        ('Resolution', {'fields': ('status', 'resolved_by', 'resolution_notes', 'resolved_at')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('earned_at', 'badge')
    search_fields = ('user__username', 'badge__name')
    readonly_fields = ('earned_at',)


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'story', 'author', 'created_at', 'is_pinned')
    list_filter = ('created_at', 'is_pinned', 'story__category')
    search_fields = ('title', 'author__username', 'story__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Discussion Info', {'fields': ('story', 'title', 'description', 'author')}),
        ('Settings', {'fields': ('is_pinned',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
