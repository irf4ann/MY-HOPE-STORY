"""
Utility functions for notifications
"""
from notifications.models import Notification, NotificationPreference
from django.utils import timezone

def create_notification(recipient, notification_type, title, message, actor=None, story=None, 
                       icon_url=None, action_url=None):
    """
    Create a notification for a user
    """
    # Check user preferences
    try:
        pref = recipient.notification_preference
    except NotificationPreference.DoesNotExist:
        pref = NotificationPreference.objects.create(user=recipient)
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        actor=actor,
        story=story,
        icon_url=icon_url,
        action_url=action_url,
    )
    
    return notification


def notify_on_comment(comment):
    """Notify story author when a new comment is made"""
    if comment.story.author != comment.author:
        create_notification(
            recipient=comment.story.author,
            notification_type='story_commented',
            title=f'{comment.author.get_full_name() or comment.author.username} commented',
            message=f'on your story: {comment.story.title}',
            actor=comment.author,
            story=comment.story,
        )


def notify_on_like(like):
    """Notify story author when a story is liked"""
    if like.story.author != like.user:
        create_notification(
            recipient=like.story.author,
            notification_type='story_liked',
            title=f'{like.user.get_full_name() or like.user.username} liked your story',
            message=f'{like.story.title}',
            actor=like.user,
            story=like.story,
        )


def notify_on_follow(follow):
    """Notify user when they get a new follower"""
    if follow.following != follow.follower:
        create_notification(
            recipient=follow.following,
            notification_type='follower_story',
            title=f'{follow.follower.get_full_name() or follow.follower.username} started following you',
            message='',
            actor=follow.follower,
        )


def notify_on_story_published(story):
    """Notify followers when a user publishes a new story"""
    followers = story.author.followers.all()
    for follow in followers:
        create_notification(
            recipient=follow.follower,
            notification_type='follower_story',
            title=f'{story.author.get_full_name() or story.author.username} published a new story',
            message=f'{story.title}',
            actor=story.author,
            story=story,
        )


def notify_on_mentorship_request(request_obj):
    """Notify mentor of a new mentorship request"""
    create_notification(
        recipient=request_obj.mentor.user,
        notification_type='mentorship_request',
        title='New mentorship request',
        message=f'from {request_obj.founder.get_full_name() or request_obj.founder.username}',
        actor=request_obj.founder,
        story=request_obj.story,
    )


def notify_on_donation(donation):
    """Notify story author of a new donation"""
    if not donation.anonymous:
        create_notification(
            recipient=donation.story.author,
            notification_type='donation_received',
            title='You received a donation!',
            message=f'${donation.amount} from {donation.donor.get_full_name() or donation.donor.username}',
            actor=donation.donor,
            story=donation.story,
        )
    else:
        create_notification(
            recipient=donation.story.author,
            notification_type='donation_received',
            title='You received an anonymous donation!',
            message=f'${donation.amount}',
            story=donation.story,
        )


def notify_on_investor_interest(investor_interest):
    """Notify story author of investor interest"""
    create_notification(
        recipient=investor_interest.story.author,
        notification_type='investor_interested',
        title=f'{investor_interest.investor.get_full_name() or investor_interest.investor.username} is interested',
        message=f'in your startup: {investor_interest.story.startup.startup_name}',
        actor=investor_interest.investor,
        story=investor_interest.story,
    )
