"""
Celery tasks for moderation app.
Handles content flagging, AI moderation, and spam detection.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_flagged_content():
    """Process flagged content in moderation queue (called by Celery beat)."""
    try:
        from moderation.models import ContentFlag
        
        # Get pending flags
        pending_flags = ContentFlag.objects.filter(
            status='pending',
            created_at__lte=timezone.now() - timedelta(hours=1)
        )
        
        for flag in pending_flags:
            # Run automated moderation
            run_content_moderation.delay(
                content_id=flag.content_id,
                content_type=flag.content_type
            )
        
        logger.info(f"Processing {pending_flags.count()} flagged content items")
        
    except Exception as exc:
        logger.error(f"Error processing flagged content: {exc}")


@shared_task
def run_content_moderation(content_id, content_type, use_ai=True):
    """Run moderation checks on content (text, image, etc)."""
    try:
        from moderation.models import ContentFlag
        
        if use_ai:
            # Use AI moderation (placeholder for ML integration)
            moderation_score = perform_ai_moderation(content_id, content_type)
            
            if moderation_score > 0.7:  # High confidence issue
                flag = ContentFlag.objects.create(
                    content_id=content_id,
                    content_type=content_type,
                    reason='ai_flagged',
                    confidence_score=moderation_score,
                    status='pending'
                )
                logger.warning(f"Content {content_id} flagged by AI (score: {moderation_score})")
        
    except Exception as exc:
        logger.error(f"Error running content moderation: {exc}")


def perform_ai_moderation(content_id, content_type):
    """
    Run AI-based content moderation.
    
    Integration points:
    - OpenAI Moderation API
    - AWS Rekognition (for images)
    - Custom ML models for domain-specific moderation
    """
    try:
        # TODO: Integrate with AI moderation service
        # For now, return dummy score
        
        if content_type == 'story':
            from stories.models import Story
            story = Story.objects.get(id=content_id)
            
            # Check for spam keywords, offensive language, etc.
            # This is simplified - real implementation would use ML
            offensive_keywords = ['spam', 'abuse', 'hate']
            content = (story.title + ' ' + story.content).lower()
            
            score = 0.0
            for keyword in offensive_keywords:
                if keyword in content:
                    score += 0.3
            
            return min(score, 1.0)
        
        return 0.0
        
    except Exception as exc:
        logger.error(f"Error in AI moderation: {exc}")
        return 0.0


@shared_task
def flag_spam_content(content_id, content_type, reason):
    """Flag content as spam manually or automatically."""
    try:
        from moderation.models import ContentFlag
        
        flag = ContentFlag.objects.create(
            content_id=content_id,
            content_type=content_type,
            reason=reason,
            status='pending'
        )
        
        logger.info(f"Content {content_id} flagged as spam: {reason}")
        
    except Exception as exc:
        logger.error(f"Error flagging spam content: {exc}")


@shared_task
def detect_duplicate_stories():
    """Detect potential duplicate or plagiarized stories."""
    try:
        from stories.models import Story
        from difflib import SequenceMatcher
        
        published_stories = Story.objects.filter(status='published')
        
        duplicates = []
        for i, story1 in enumerate(published_stories):
            for story2 in published_stories[i+1:]:
                # Simple similarity check (would use advanced NLP in production)
                similarity = SequenceMatcher(
                    None,
                    story1.content[:100],
                    story2.content[:100]
                ).ratio()
                
                if similarity > 0.9:  # More than 90% similar
                    duplicates.append({
                        'story1': story1.id,
                        'story2': story2.id,
                        'similarity': similarity
                    })
        
        logger.info(f"Found {len(duplicates)} potential duplicates")
        return duplicates
        
    except Exception as exc:
        logger.error(f"Error detecting duplicate stories: {exc}")


@shared_task
def check_for_spam_accounts():
    """Detect and flag potentially spammy user accounts."""
    try:
        from accounts.models import User
        from django.db.models import Count
        from stories.models import Story
        
        # Find accounts that create many stories quickly
        recent_users = User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).annotate(
            story_count=Count('stories')
        ).filter(
            story_count__gt=10  # More than 10 stories in first week
        )
        
        for user in recent_users:
            # Flag for review
            from moderation.models import ContentFlag
            
            ContentFlag.objects.get_or_create(
                content_id=user.id,
                content_type='user_account',
                defaults={
                    'reason': 'suspicious_activity',
                    'status': 'pending'
                }
            )
        
        logger.info(f"Flagged {recent_users.count()} accounts for review")
        
    except Exception as exc:
        logger.error(f"Error checking for spam accounts: {exc}")


@shared_task
def approve_flagged_content(flag_id):
    """Approve flagged content after manual review."""
    try:
        from moderation.models import ContentFlag
        
        flag = ContentFlag.objects.get(id=flag_id)
        flag.status = 'approved'
        flag.reviewed_at = timezone.now()
        flag.save()
        
        logger.info(f"Flag {flag_id} approved")
        
    except Exception as exc:
        logger.error(f"Error approving flagged content: {exc}")


@shared_task
def reject_flagged_content(flag_id, rejection_reason):
    """Reject flagged content and take action."""
    try:
        from moderation.models import ContentFlag
        from stories.models import Story
        
        flag = ContentFlag.objects.get(id=flag_id)
        flag.status = 'rejected'
        flag.reviewed_at = timezone.now()
        flag.rejection_reason = rejection_reason
        flag.save()
        
        # Take action based on content type
        if flag.content_type == 'story':
            story = Story.objects.get(id=flag.content_id)
            story.status = 'rejected'
            story.save()
            
            # Notify author
            from notifications.tasks import send_email_notification
            # TODO: Create notification for author
        
        logger.info(f"Flag {flag_id} rejected: {rejection_reason}")
        
    except Exception as exc:
        logger.error(f"Error rejecting flagged content: {exc}")


@shared_task
def ban_user(user_id, reason):
    """Ban a user from the platform."""
    try:
        from accounts.models import User
        
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        
        # Log action
        logger.warning(f"User {user_id} banned: {reason}")
        
    except Exception as exc:
        logger.error(f"Error banning user: {exc}")


@shared_task
def send_moderation_report():
    """Send daily moderation report to moderators."""
    try:
        from moderation.models import ContentFlag
        from accounts.models import User
        from django.core.mail import send_mail
        
        # Get today's flags
        today_flags = ContentFlag.objects.filter(
            created_at__date=timezone.now().date()
        )
        
        # Get moderators
        moderators = User.objects.filter(
            groups__name='Moderators'
        )
        
        if today_flags.count() > 0 and moderators.count() > 0:
            message = f"""
            Daily Moderation Report
            
            Total Flagged Items: {today_flags.count()}
            Pending Review: {today_flags.filter(status='pending').count()}
            Approved: {today_flags.filter(status='approved').count()}
            Rejected: {today_flags.filter(status='rejected').count()}
            """
            
            for moderator in moderators:
                send_mail(
                    'Daily Moderation Report',
                    message,
                    'noreply@myhopestory.com',
                    [moderator.email]
                )
        
        logger.info(f"Moderation report sent to {moderators.count()} moderators")
        
    except Exception as exc:
        logger.error(f"Error sending moderation report: {exc}")
