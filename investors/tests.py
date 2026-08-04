from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse

from funding.models import InvestorInterest
from stories.models import Startup, Story

User = get_user_model()


class InvestorsViewsTests(TestCase):
    def setUp(self):
        self.founder = User.objects.create_user(username='founder2', password='secret123')
        self.investor = User.objects.create_user(username='investor2', password='secret123')
        self.client.force_login(self.investor)

        startup = Startup.objects.create(
            founder=self.founder,
            startup_name='Northstar Labs',
            industry='Fintech',
        )
        self.story = Story.objects.create(
            author=self.founder,
            startup=startup,
            title='A failed launch story',
            summary='A concise overview of our lessons.',
            problem_solved='We built a product for the wrong customer.',
            timeline_content='We launched quickly and learned from it.',
            challenges='We had low retention.',
            failure_reason='We ignored customer feedback.',
            lessons='We now focus on product-market fit.',
        )

    def test_expressing_interest_creates_investor_interest(self):
        response = self.client.post(
            reverse('investors'),
            {
                'express_interest': '1',
                'story_id': self.story.id,
                'investment_amount': '25000',
                'message': 'I would love to learn more about this story.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            InvestorInterest.objects.filter(investor=self.investor, story=self.story).exists()
        )

    def test_investor_can_update_interest_status(self):
        interest = InvestorInterest.objects.create(
            story=self.story,
            investor=self.investor,
            investment_amount='25000',
            message='Interested in this story.',
        )

        response = self.client.post(
            reverse('investors'),
            {
                'update_interest_status': '1',
                'interest_id': interest.id,
                'status': 'discussing',
            },
        )

        self.assertEqual(response.status_code, 302)
        interest.refresh_from_db()
        self.assertEqual(interest.status, 'discussing')

    @patch('investors.views.InvestorInterest.objects.update_or_create')
    def test_expressing_interest_retries_on_transient_database_lock(self, mock_update_or_create):
        calls = {'count': 0}

        def flaky_update_or_create(*args, **kwargs):
            if calls['count'] == 0:
                calls['count'] += 1
                raise OperationalError('database is locked')
            return InvestorInterest._base_manager.update_or_create(*args, **kwargs)

        mock_update_or_create.side_effect = flaky_update_or_create

        response = self.client.post(
            reverse('investors'),
            {
                'express_interest': '1',
                'story_id': self.story.id,
                'investment_amount': '25000',
                'message': 'I would love to learn more about this story.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            InvestorInterest.objects.filter(investor=self.investor, story=self.story).exists()
        )
