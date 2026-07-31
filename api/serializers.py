from rest_framework import serializers
from accounts.models import User
from stories.models import Story, Startup, Category
from community.models import Comment, Like, Bookmark, Follow, Discussion, Report, Badge
from mentorship.models import MentorProfile, MentorshipRequest
from funding.models import Donation, CrowdfundingCampaign, InvestorInterest
from notifications.models import Notification

# ===========================
# User Serializers
# ===========================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                  'profile_image', 'verified', 'bio', 'website', 'location', 'industry', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'verified')


class UserDetailSerializer(UserSerializer):
    stories_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('stories_count', 'followers_count', 'following_count')
    
    def get_stories_count(self, obj):
        return obj.stories.filter(status='published').count()
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()


# ===========================
# Story Serializers
# ===========================

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class StartupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Startup
        fields = ('id', 'founder', 'startup_name', 'industry', 'website', 'founded_year', 'team_size')
        read_only_fields = ('id', 'founder')


class StoryListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = ('id', 'title', 'summary', 'author', 'startup', 'category', 'status', 
                  'visibility', 'created_at', 'published_date', 'likes_count', 'comments_count')
        read_only_fields = ('id', 'author', 'created_at', 'published_date')
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(parent_comment__isnull=True).count()


class StoryDetailSerializer(StoryListSerializer):
    class Meta(StoryListSerializer.Meta):
        fields = StoryListSerializer.Meta.fields + ('problem_solved', 'business_model', 'timeline_content',
                                                      'challenges', 'failure_reason', 'lessons', 'future_plans',
                                                      'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'published_date', 'updated_at')


# ===========================
# Community Serializers
# ===========================

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'story', 'author', 'content', 'created_at', 'updated_at', 'parent_comment', 'replies_count')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')
    
    def get_replies_count(self, obj):
        return obj.replies.count()


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'story', 'user', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class BookmarkSerializer(serializers.ModelSerializer):
    story = StoryListSerializer(read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ('id', 'story', 'user', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class FollowSerializer(serializers.ModelSerializer):
    following_user = UserSerializer(source='following', read_only=True)
    
    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following_user', 'created_at')
        read_only_fields = ('id', 'follower', 'created_at')


class DiscussionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Discussion
        fields = ('id', 'story', 'title', 'description', 'author', 'created_at', 'updated_at', 'is_pinned')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'story', 'reason', 'description', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')


# ===========================
# Mentorship Serializers
# ===========================

class MentorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorProfile
        fields = ('id', 'user', 'expertise_areas', 'years_experience', 'languages', 'availability',
                  'hourly_rate', 'bio', 'verified', 'average_rating')
        read_only_fields = ('id', 'user', 'verified', 'verification_date')
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return sum([r.rating for r in reviews]) / reviews.count()
        return None


class MentorshipRequestSerializer(serializers.ModelSerializer):
    mentor = MentorProfileSerializer(read_only=True)
    founder = UserSerializer(read_only=True)
    
    class Meta:
        model = MentorshipRequest
        fields = ('id', 'mentor', 'founder', 'story', 'message', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'founder', 'created_at', 'updated_at')


# ===========================
# Funding Serializers
# ===========================

class DonationSerializer(serializers.ModelSerializer):
    donor = UserSerializer(read_only=True)
    
    class Meta:
        model = Donation
        fields = ('id', 'story', 'donor', 'amount', 'message', 'anonymous', 'status', 'created_at')
        read_only_fields = ('id', 'donor', 'status', 'created_at')


class CrowdfundingCampaignSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    current_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CrowdfundingCampaign
        fields = ('id', 'story', 'creator', 'title', 'description', 'goal_amount', 'target_deadline',
                  'status', 'current_amount', 'completion_percentage', 'created_at')
        read_only_fields = ('id', 'creator', 'created_at')
    
    def get_current_amount(self, obj):
        return obj.current_amount()
    
    def get_completion_percentage(self, obj):
        return obj.completion_percentage()


class InvestorInterestSerializer(serializers.ModelSerializer):
    investor = UserSerializer(read_only=True)
    
    class Meta:
        model = InvestorInterest
        fields = ('id', 'story', 'investor', 'investment_amount', 'status', 'message', 'created_at')
        read_only_fields = ('id', 'investor', 'created_at')


# ===========================
# Notification Serializers
# ===========================

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ('id', 'notification_type', 'actor', 'title', 'message', 'action_url', 'read', 'created_at')
        read_only_fields = ('id', 'created_at')
