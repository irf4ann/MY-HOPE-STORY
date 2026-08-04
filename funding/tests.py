from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from funding.models import Donation
from stories.models import Startup, Story

User = get_user_model()


class MentorshipPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='payer', password='secret123')
        self.client.force_login(self.user)

        startup = Startup.objects.create(
            founder=self.user,
            startup_name='Northstar Labs',
            industry='Fintech',
        )
        self.story = Story.objects.create(
            author=self.user,
            startup=startup,
            title='A resilient rebuild story',
            summary='An overview of our lessons.',
            problem_solved='We learned from a failed launch.',
            timeline_content='We iterated quickly.',
            challenges='We had low retention.',
            failure_reason='We ignored customer feedback.',
            lessons='We now focus on product-market fit.',
        )

    def test_checkout_page_renders(self):
        response = self.client.get(reverse('checkout_session', kwargs={'story_id': self.story.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book a mentorship session')

    def test_checkout_creates_pending_donation(self):
        response = self.client.post(
            reverse('checkout_session', kwargs={'story_id': self.story.id}),
            {'amount': '120.00', 'message': 'I want a session.'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Donation.objects.filter(donor=self.user, story=self.story, status='pending').exists())
