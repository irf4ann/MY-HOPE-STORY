"""
Celery tasks for notifications app.
Handles email delivery, notification scheduling, and cleanup.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5)
def send_email_notification(self, notification_id):
    """Send email notification with retry logic."""
    try:
        from notifications.models import Notification
        
        notification = Notification.objects.get(id=notification_id)
        
        # Render email template
        context = {
            'user': notification.recipient.get_full_name(),
            'title': notification.title,
            'message': notification.message,
            'action_url': notification.action_url,
        }
        
        html_content = render_to_string('emails/notification.html', context)
        text_content = render_to_string('emails/notification.txt', context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=notification.title,
            body=text_content,
            from_email='noreply@myhopestory.com',
            to=[notification.recipient.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        
        # Mark as sent
        notification.sent_at = timezone.now()
        notification.is_sent = True
        notification.save()
        
        logger.info(f"Notification {notification_id} sent successfully")
        
    except Exception as exc:
        logger.error(f"Error sending notification {notification_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user."""
    try:
        from accounts.models import User
        
        user = User.objects.get(id=user_id)
        context = {'user': user}
        
        html_content = render_to_string('emails/welcome.html', context)
        text_content = render_to_string('emails/welcome.txt', context)
        
        email = EmailMultiAlternatives(
            subject='Welcome to My Hope Story!',
            body=text_content,
            from_email='noreply@myhopestory.com',
            to=[user.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        
    except Exception as exc:
        logger.error(f"Error sending welcome email: {exc}")


@shared_task
def send_story_published_notification(story_id, subscriber_ids):
    """Notify followers when a story is published."""
    try:
        from stories.models import Story
        from notifications.models import Notification
        
        story = Story.objects.get(id=story_id)
        
        # Create notifications for all subscribers
        notifications = [
            Notification(
                recipient_id=subscriber_id,
                title=f"New story: {story.title}",
                message=f"{story.author.get_full_name()} published a new story",
                notification_type='story_published',
                related_story=story,
                action_url=f'/stories/{story.id}/'
            )
            for subscriber_id in subscriber_ids
        ]
        
        Notification.objects.bulk_create(notifications)
        logger.info(f"Published notification sent to {len(subscriber_ids)} users")
        
    except Exception as exc:
        logger.error(f"Error sending story published notification: {exc}")


@shared_task
def send_mentorship_request_notification(request_id):
    """Notify mentor about new mentorship request."""
    try:
        from mentorship.models import MentorshipRequest
        from notifications.models import Notification
        
        mentorship_request = MentorshipRequest.objects.get(id=request_id)
        
        notification = Notification.objects.create(
            recipient=mentorship_request.mentor,
            title="New mentorship request",
            message=f"{mentorship_request.entrepreneur.get_full_name()} requested mentorship",
            notification_type='mentorship_request',
            action_url=f'/mentorship/requests/{request_id}/'
        )
        
        send_email_notification.delay(notification.id)
        
    except Exception as exc:
        logger.error(f"Error sending mentorship request notification: {exc}")


@shared_task
def send_donation_thank_you(donation_id):
    """Send thank you email for donation."""
    try:
        from funding.models import Donation
        
        donation = Donation.objects.get(id=donation_id)
        context = {
            'donor_name': donation.donor.get_full_name(),
            'amount': donation.amount,
            'campaign': donation.campaign.title,
        }
        
        html_content = render_to_string('emails/donation_thank_you.html', context)
        text_content = render_to_string('emails/donation_thank_you.txt', context)
        
        email = EmailMultiAlternatives(
            subject='Thank you for your donation!',
            body=text_content,
            from_email='noreply@myhopestory.com',
            to=[donation.donor.email]
        )
        email.attach_alternative(html_content, 'text/html')
        email.send()
        
        logger.info(f"Thank you email sent for donation {donation_id}")
        
    except Exception as exc:
        logger.error(f"Error sending donation thank you: {exc}")


@shared_task
def send_pending_notifications():
    """Send all pending notifications (called by Celery beat)."""
    try:
        from notifications.models import Notification
        
        pending = Notification.objects.filter(
            is_sent=False,
            created_at__lte=timezone.now() - timedelta(minutes=1)
        )
        
        for notification in pending:
            send_email_notification.delay(notification.id)
        
        logger.info(f"Sent {pending.count()} pending notifications")
        
    except Exception as exc:
        logger.error(f"Error sending pending notifications: {exc}")


@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 90 days."""
    try:
        from notifications.models import Notification
        
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_sent=True
        ).delete()
        
        logger.info(f"Deleted {deleted_count} old notifications")
        
    except Exception as exc:
        logger.error(f"Error cleaning up notifications: {exc}")


@shared_task
def send_batch_digest_email():
    """Send daily digest emails to users."""
    try:
        from accounts.models import User
        from notifications.models import Notification, NotificationPreference
        
        # Get users who prefer digest emails
        digest_users = User.objects.filter(
            notification_preferences__digest_frequency='daily'
        )
        
        for user in digest_users:
            # Get unread notifications from last 24 hours
            notifications = Notification.objects.filter(
                recipient=user,
                created_at__gte=timezone.now() - timedelta(hours=24),
                is_sent=False
            )
            
            if notifications.exists():
                context = {
                    'user': user,
                    'notifications': notifications,
                }
                
                html_content = render_to_string('emails/digest.html', context)
                text_content = render_to_string('emails/digest.txt', context)
                
                email = EmailMultiAlternatives(
                    subject='Your My Hope Story Daily Digest',
                    body=text_content,
                    from_email='noreply@myhopestory.com',
                    to=[user.email]
                )
                email.attach_alternative(html_content, 'text/html')
                email.send()
        
        logger.info(f"Digest emails sent to {digest_users.count()} users")
        
    except Exception as exc:
        logger.error(f"Error sending digest emails: {exc}")
