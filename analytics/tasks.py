"""
Celery tasks for analytics app.
Handles report generation, data aggregation, and metrics computation.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Sum, Q, Avg
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_report():
    """Generate daily analytics report (called by Celery beat)."""
    try:
        from stories.models import Story
        from community.models import Like, Comment
        from notifications.models import Notification
        from analytics.models import DailyMetrics
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Count new stories
        new_stories = Story.objects.filter(
            created_at__date=yesterday
        ).count()
        
        # Count engagements
        new_likes = Like.objects.filter(
            created_at__date=yesterday
        ).count()
        
        new_comments = Comment.objects.filter(
            created_at__date=yesterday
        ).count()
        
        # Count new users
        from accounts.models import User
        new_users = User.objects.filter(
            date_joined__date=yesterday
        ).count()
        
        # Get top stories
        top_stories = Story.objects.filter(
            created_at__date__lte=yesterday
        ).annotate(
            like_count=Count('likes')
        ).order_by('-like_count')[:10]
        
        # Create metrics record
        metrics = DailyMetrics.objects.create(
            date=yesterday,
            new_stories_count=new_stories,
            new_likes_count=new_likes,
            new_comments_count=new_comments,
            new_users_count=new_users,
            total_stories_count=Story.objects.count(),
            total_users_count=User.objects.count(),
            total_engagements=new_likes + new_comments,
        )
        
        logger.info(f"Daily metrics generated for {yesterday}")
        return metrics.id
        
    except Exception as exc:
        logger.error(f"Error generating daily report: {exc}")


@shared_task
def generate_weekly_investor_report():
    """Generate weekly report for investors (called by Celery beat)."""
    try:
        from stories.models import Story
        from funding.models import Donation, Campaign
        from mentorship.models import MentorshipSession
        from analytics.models import WeeklyReport
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Get stats for the week
        stories_this_week = Story.objects.filter(
            created_at__date__gte=week_ago,
            created_at__date__lt=today
        ).count()
        
        donations_this_week = Donation.objects.filter(
            created_at__date__gte=week_ago,
            created_at__date__lt=today
        )
        
        total_donations = donations_this_week.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        donation_count = donations_this_week.count()
        
        # Campaign metrics
        active_campaigns = Campaign.objects.filter(
            status='active',
            created_at__date__lte=today
        ).count()
        
        # Mentorship sessions
        sessions_this_week = MentorshipSession.objects.filter(
            date__date__gte=week_ago,
            date__date__lt=today,
            status='completed'
        ).count()
        
        # Create weekly report
        report = WeeklyReport.objects.create(
            week_start=week_ago,
            week_end=today,
            stories_published=stories_this_week,
            donations_received=donation_count,
            total_donation_amount=total_donations,
            active_campaigns=active_campaigns,
            mentorship_sessions=sessions_this_week,
        )
        
        logger.info(f"Weekly investor report generated for week ending {today}")
        return report.id
        
    except Exception as exc:
        logger.error(f"Error generating weekly investor report: {exc}")


@shared_task
def generate_user_analytics(user_id):
    """Generate personalized analytics for a user."""
    try:
        from accounts.models import User
        from stories.models import Story
        from community.models import Like, Comment
        
        user = User.objects.get(id=user_id)
        
        # Get user's stories
        user_stories = Story.objects.filter(author=user)
        
        # Calculate engagement metrics
        total_likes = Like.objects.filter(
            story__author=user
        ).count()
        
        total_comments = Comment.objects.filter(
            story__author=user
        ).count()
        
        avg_views = user_stories.aggregate(
            avg_views=Avg('views_count')
        )['avg_views'] or 0
        
        data = {
            'user_id': user_id,
            'total_stories': user_stories.count(),
            'total_likes_received': total_likes,
            'total_comments_received': total_comments,
            'average_views_per_story': avg_views,
            'generated_at': timezone.now(),
        }
        
        logger.info(f"User analytics generated for {user.email}")
        return data
        
    except Exception as exc:
        logger.error(f"Error generating user analytics: {exc}")


@shared_task
def calculate_trending_stories():
    """Calculate trending stories based on recent engagement."""
    try:
        from stories.models import Story
        from community.models import Like
        
        # Last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        trending = Story.objects.annotate(
            recent_likes=Count(
                'likes',
                filter=Q(likes__created_at__gte=week_ago)
            )
        ).filter(
            recent_likes__gt=0
        ).order_by('-recent_likes')[:20]
        
        logger.info(f"Calculated trending stories: {len(list(trending))}")
        return list(trending.values_list('id', flat=True))
        
    except Exception as exc:
        logger.error(f"Error calculating trending stories: {exc}")


@shared_task
def generate_export_report(user_id, report_type):
    """Generate exportable report for user (CSV/PDF)."""
    try:
        from accounts.models import User
        from stories.models import Story
        import csv
        from io import StringIO
        
        user = User.objects.get(id=user_id)
        
        if report_type == 'stories':
            stories = Story.objects.filter(author=user)
            data = []
            
            for story in stories:
                data.append({
                    'title': story.title,
                    'created_at': story.created_at,
                    'views': story.views_count,
                    'status': story.status,
                })
        
        logger.info(f"Export report generated for {user.email}")
        return len(data) if isinstance(data, list) else 0
        
    except Exception as exc:
        logger.error(f"Error generating export report: {exc}")


@shared_task
def update_user_ranking():
    """Update user rankings based on contribution and engagement."""
    try:
        from accounts.models import User
        from stories.models import Story
        from community.models import Like
        
        users = User.objects.all()
        
        for user in users:
            # Calculate points
            stories = Story.objects.filter(author=user).count()
            likes_received = Like.objects.filter(
                story__author=user
            ).count()
            
            # Simple ranking formula
            points = (stories * 10) + (likes_received * 1)
            
            # Update user rank field if exists
            if hasattr(user, 'ranking_points'):
                user.ranking_points = points
                user.save(update_fields=['ranking_points'])
        
        logger.info(f"Updated rankings for {users.count()} users")
        
    except Exception as exc:
        logger.error(f"Error updating user ranking: {exc}")
