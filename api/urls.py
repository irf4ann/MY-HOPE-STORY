from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, StoryViewSet, CommentViewSet, BookmarkListViewSet,
    NotificationViewSet, MentorProfileViewSet, MentorshipRequestViewSet,
    DonationViewSet, CrowdfundingCampaignViewSet, InvestorInterestViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'bookmarks', BookmarkListViewSet, basename='bookmark')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'mentors', MentorProfileViewSet, basename='mentor')
router.register(r'mentorship-requests', MentorshipRequestViewSet, basename='mentorship-request')
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'campaigns', CrowdfundingCampaignViewSet, basename='campaign')
router.register(r'investor-interests', InvestorInterestViewSet, basename='investor-interest')

urlpatterns = [
    path('', include(router.urls)),
]
