from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification

User = get_user_model()


class NotificationInboxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notifyuser', password='secret123')
        self.client.force_login(self.user)

    def test_inbox_lists_unread_notifications(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type='mentorship_request',
            title='New mentorship request',
            message='A founder wants your guidance.',
            action_url='/mentors/',
        )

        response = self.client.get(reverse('notifications_inbox'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New mentorship request')
        self.assertContains(response, 'A founder wants your guidance.')

    def test_mark_all_read_marks_notifications_as_read(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type='investor_interested',
            title='New investor interest',
            message='An investor is interested in your story.',
            action_url='/investors/',
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type='mentorship_accepted',
            title='Mentorship accepted',
            message='Your mentor request was accepted.',
            action_url='/mentors/',
        )

        response = self.client.post(reverse('notifications_inbox'), {'mark_all_read': '1'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.notifications.filter(read=False).count(), 0)
