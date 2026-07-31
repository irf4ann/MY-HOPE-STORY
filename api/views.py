from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from accounts.models import User
from stories.models import Story, Category
from community.models import Comment, Like, Bookmark, Follow, Discussion, Report
from mentorship.models import MentorProfile, MentorshipRequest
from funding.models import Donation, CrowdfundingCampaign, InvestorInterest
from notifications.models import Notification

from .serializers import (
    UserSerializer, UserDetailSerializer, StoryListSerializer, StoryDetailSerializer,
    CommentSerializer, LikeSerializer, BookmarkSerializer, FollowSerializer, DiscussionSerializer,
    ReportSerializer, MentorProfileSerializer, MentorshipRequestSerializer,
    DonationSerializer, CrowdfundingCampaignSerializer, InvestorInterestSerializer,
    NotificationSerializer
)


# ===========================
# Permission Classes
# ===========================

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or obj.user == request.user


# ===========================
# User ViewSets
# ===========================

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        if user_to_follow == request.user:
            return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            return Response({'status': 'now following'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already following'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        return Response({'status': 'unfollowed'})


# ===========================
# Story ViewSets
# ===========================

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.filter(status='published')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'visibility', 'status']
    search_fields = ['title', 'summary', 'failure_reason', 'startup__startup_name']
    ordering_fields = ['created_at', 'published_date']
    ordering = ['-published_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoryDetailSerializer
        return StoryListSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        story = self.get_object()
        like, created = Like.objects.get_or_create(story=story, user=request.user)
        
        if created:
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        like.delete()
        return Response({'status': 'unliked'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def bookmark(self, request, pk=None):
        story = self.get_object()
        bookmark, created = Bookmark.objects.get_or_create(story=story, user=request.user)
        
        if created:
            return Response({'status': 'bookmarked'}, status=status.HTTP_201_CREATED)
        bookmark.delete()
        return Response({'status': 'unbookmarked'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        story = self.get_object()
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(story=story, reporter=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===========================
# Community ViewSets
# ===========================

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['story']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class BookmarkListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['read', 'notification_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'marked as read'})


# ===========================
# Mentorship ViewSets
# ===========================

class MentorProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MentorProfile.objects.filter(verified=True)
    serializer_class = MentorProfileSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['expertise_areas', 'user__username']
    ordering_fields = ['years_experience', 'hourly_rate']


class MentorshipRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'mentor']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return MentorshipRequest.objects.filter(founder=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(founder=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        request_obj = self.get_object()
        if request_obj.mentor.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        request_obj.status = 'accepted'
        request_obj.started_at = timezone.now()
        request_obj.save()
        return Response({'status': 'accepted'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        request_obj = self.get_object()
        if request_obj.mentor.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        request_obj.status = 'rejected'
        request_obj.save()
        return Response({'status': 'rejected'})


# ===========================
# Funding ViewSets
# ===========================

class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.filter(status='completed')
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['story']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)


class CrowdfundingCampaignViewSet(viewsets.ModelViewSet):
    queryset = CrowdfundingCampaign.objects.filter(status__in=['active', 'completed'])
    serializer_class = CrowdfundingCampaignSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']


class InvestorInterestViewSet(viewsets.ModelViewSet):
    serializer_class = InvestorInterestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return InvestorInterest.objects.filter(investor=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)


from django.utils import timezone
