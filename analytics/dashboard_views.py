"""
Analytics dashboard views and API endpoints.
Provides comprehensive metrics, visualizations, and insights.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging

logger = logging.getLogger(__name__)


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """
    Comprehensive analytics dashboard with metrics and visualizations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview metrics."""
        try:
            from accounts.models import User
            from stories.models import Story
            from community.models import Like, Comment
            from funding.models import Donation
            
            today = timezone.now().date()
            this_month = timezone.now().date().replace(day=1)
            
            # User metrics
            total_users = User.objects.count()
            new_users_today = User.objects.filter(date_joined__date=today).count()
            new_users_this_month = User.objects.filter(date_joined__date__gte=this_month).count()
            
            # Content metrics
            total_stories = Story.objects.count()
            new_stories_today = Story.objects.filter(created_at__date=today).count()
            new_stories_this_month = Story.objects.filter(created_at__date__gte=this_month).count()
            published_stories = Story.objects.filter(status='published').count()
            
            # Engagement metrics
            total_likes = Like.objects.count()
            new_likes_today = Like.objects.filter(created_at__date=today).count()
            total_comments = Comment.objects.count()
            new_comments_today = Comment.objects.filter(created_at__date=today).count()
            
            # Funding metrics
            total_donations = Donation.objects.aggregate(Sum('amount'))['amount__sum'] or 0
            total_donation_count = Donation.objects.count()
            
            return Response({
                'users': {
                    'total': total_users,
                    'new_today': new_users_today,
                    'new_this_month': new_users_this_month,
                },
                'stories': {
                    'total': total_stories,
                    'published': published_stories,
                    'new_today': new_stories_today,
                    'new_this_month': new_stories_this_month,
                },
                'engagement': {
                    'total_likes': total_likes,
                    'new_likes_today': new_likes_today,
                    'total_comments': total_comments,
                    'new_comments_today': new_comments_today,
                },
                'funding': {
                    'total_donations': float(total_donations),
                    'total_donation_count': total_donation_count,
                    'average_donation': float(total_donations / total_donation_count) if total_donation_count > 0 else 0,
                },
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return Response(
                {'error': 'Failed to load overview'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def user_growth(self, request):
        """Get user growth metrics over time."""
        try:
            from accounts.models import User
            
            days = int(request.query_params.get('days', 30))
            
            # Get daily user signups
            data_points = []
            for i in range(days, -1, -1):
                date = timezone.now().date() - timedelta(days=i)
                count = User.objects.filter(date_joined__date=date).count()
                data_points.append({
                    'date': date.isoformat(),
                    'count': count,
                    'cumulative': User.objects.filter(date_joined__date__lte=date).count()
                })
            
            return Response({
                'period_days': days,
                'data': data_points,
                'trend': calculate_trend([d['count'] for d in data_points]),
            })
            
        except Exception as e:
            logger.error(f"Error getting user growth: {e}")
            return Response(
                {'error': 'Failed to load user growth'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def content_analytics(self, request):
        """Get content creation and engagement analytics."""
        try:
            from stories.models import Story
            from community.models import Like, Comment
            
            days = int(request.query_params.get('days', 30))
            
            # Daily metrics
            data_points = []
            for i in range(days, -1, -1):
                date = timezone.now().date() - timedelta(days=i)
                
                stories_count = Story.objects.filter(created_at__date=date).count()
                likes_count = Like.objects.filter(created_at__date=date).count()
                comments_count = Comment.objects.filter(created_at__date=date).count()
                
                data_points.append({
                    'date': date.isoformat(),
                    'stories': stories_count,
                    'likes': likes_count,
                    'comments': comments_count,
                    'total_engagement': likes_count + comments_count,
                })
            
            # Top performing stories
            top_stories = Story.objects.annotate(
                like_count=Count('likes'),
                comment_count=Count('comments')
            ).order_by('-like_count')[:10].values(
                'id', 'title', 'like_count', 'comment_count', 'views_count'
            )
            
            return Response({
                'period_days': days,
                'daily_metrics': data_points,
                'top_stories': list(top_stories),
            })
            
        except Exception as e:
            logger.error(f"Error getting content analytics: {e}")
            return Response(
                {'error': 'Failed to load content analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def funding_analytics(self, request):
        """Get funding and donation analytics."""
        try:
            from funding.models import Donation, Campaign
            
            days = int(request.query_params.get('days', 30))
            
            # Daily donation metrics
            data_points = []
            for i in range(days, -1, -1):
                date = timezone.now().date() - timedelta(days=i)
                
                donations = Donation.objects.filter(
                    created_at__date=date,
                    status='completed'
                )
                
                amount = donations.aggregate(Sum('amount'))['amount__sum'] or 0
                count = donations.count()
                
                data_points.append({
                    'date': date.isoformat(),
                    'amount': float(amount),
                    'count': count,
                    'average': float(amount / count) if count > 0 else 0,
                })
            
            # Top fundraising campaigns
            top_campaigns = Campaign.objects.annotate(
                total_raised=Sum('donations__amount'),
                donor_count=Count('donations', distinct=True)
            ).order_by('-total_raised')[:10].values(
                'id', 'title', 'total_raised', 'donor_count', 'goal'
            )
            
            return Response({
                'period_days': days,
                'daily_metrics': data_points,
                'top_campaigns': list(top_campaigns),
            })
            
        except Exception as e:
            logger.error(f"Error getting funding analytics: {e}")
            return Response(
                {'error': 'Failed to load funding analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get user activity analytics."""
        try:
            from accounts.models import User
            from stories.models import Story
            from community.models import Like, Comment
            
            # Most active users
            active_users = User.objects.annotate(
                stories_count=Count('stories'),
                likes_count=Count('likes'),
                comments_count=Count('comments')
            ).filter(
                Q(stories_count__gt=0) | Q(likes_count__gt=0) | Q(comments_count__gt=0)
            ).order_by('-stories_count')[:20].values(
                'id', 'first_name', 'last_name', 'email',
                'stories_count', 'likes_count', 'comments_count'
            )
            
            # User retention
            days_ago_7 = timezone.now() - timedelta(days=7)
            days_ago_30 = timezone.now() - timedelta(days=30)
            
            new_users_7d = User.objects.filter(date_joined__gte=days_ago_7).count()
            returning_users_7d = User.objects.filter(
                date_joined__lt=days_ago_7,
                last_login__gte=days_ago_7
            ).count()
            
            return Response({
                'active_users': list(active_users),
                'retention': {
                    'new_7d': new_users_7d,
                    'returning_7d': returning_users_7d,
                    'retention_rate': f"{(returning_users_7d / (new_users_7d + returning_users_7d) * 100) if (new_users_7d + returning_users_7d) > 0 else 0:.1f}%"
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return Response(
                {'error': 'Failed to load user activity'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def category_insights(self, request):
        """Get insights by category."""
        try:
            from stories.models import Story
            from community.models import Like, Comment
            
            categories = Story.objects.values('category').annotate(
                story_count=Count('id'),
                like_count=Count('likes'),
                comment_count=Count('comments'),
                avg_views=Avg('views_count')
            ).order_by('-story_count')
            
            return Response({
                'categories': list(categories)
            })
            
        except Exception as e:
            logger.error(f"Error getting category insights: {e}")
            return Response(
                {'error': 'Failed to load category insights'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    @action(detail=False, methods=['get'])
    def user_profile_analytics(self, request):
        """Get analytics for logged-in user's profile."""
        try:
            from stories.models import Story
            from community.models import Like, Comment
            
            user = request.user
            
            # User's stories
            user_stories = Story.objects.filter(author=user)
            
            total_views = user_stories.aggregate(Sum('views_count'))['views_count__sum'] or 0
            total_likes = Like.objects.filter(story__author=user).count()
            total_comments = Comment.objects.filter(story__author=user).count()
            
            # Best performing story
            best_story = user_stories.annotate(
                like_count=Count('likes')
            ).order_by('-like_count').first()
            
            # Recent activity
            recent_likes = Like.objects.filter(story__author=user).order_by('-created_at')[:10]
            recent_comments = Comment.objects.filter(story__author=user).order_by('-created_at')[:10]
            
            return Response({
                'stories_count': user_stories.count(),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'best_story': {
                    'id': best_story.id,
                    'title': best_story.title,
                    'likes': best_story.like_count,
                    'views': best_story.views_count
                } if best_story else None,
                'engagement_rate': f"{(total_likes / total_views * 100) if total_views > 0 else 0:.2f}%"
            })
            
        except Exception as e:
            logger.error(f"Error getting user profile analytics: {e}")
            return Response(
                {'error': 'Failed to load profile analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def calculate_trend(data):
    """Calculate trend direction and percentage."""
    if len(data) < 2:
        return "neutral"
    
    first_half = sum(data[:len(data)//2])
    second_half = sum(data[len(data)//2:])
    
    if first_half == 0:
        return "new"
    
    change = ((second_half - first_half) / first_half) * 100
    
    if change > 10:
        return f"↑ {change:.1f}%"
    elif change < -10:
        return f"↓ {abs(change):.1f}%"
    else:
        return "stable"
