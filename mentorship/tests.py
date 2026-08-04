from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse

from mentorship.models import MentorProfile, MentorshipRequest

User = get_user_model()


class MentorshipViewsTests(TestCase):
    def setUp(self):
        self.founder = User.objects.create_user(username='founder', password='secret123')
        self.mentor = User.objects.create_user(username='mentor', password='secret123')
        self.client.force_login(self.founder)

    def test_becoming_a_mentor_creates_profile(self):
        response = self.client.post(
            reverse('mentors'),
            {
                'become_mentor': '1',
                'expertise_areas': 'Product strategy',
                'years_experience': '6',
                'languages': 'English',
                'bio': 'I help founders sharpen their story and strategy.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(MentorProfile.objects.filter(user=self.founder).exists())

    def test_requesting_mentor_creates_request(self):
        mentor_profile = MentorProfile.objects.create(
            user=self.mentor,
            expertise_areas='Growth',
            years_experience=5,
        )

        response = self.client.post(
            reverse('mentors'),
            {
                'request_mentor': '1',
                'mentor_id': mentor_profile.id,
                'message': 'I would love guidance on fundraising.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            MentorshipRequest.objects.filter(founder=self.founder, mentor=mentor_profile).exists()
        )

    def test_mentor_can_update_request_status(self):
        mentor_profile = MentorProfile.objects.create(
            user=self.mentor,
            expertise_areas='Growth',
            years_experience=5,
        )
        request = MentorshipRequest.objects.create(
            mentor=mentor_profile,
            founder=self.founder,
            message='Please help me.',
        )

        self.client.force_login(self.mentor)

        response = self.client.post(
            reverse('mentors'),
            {
                'update_request_status': '1',
                'request_id': request.id,
                'status': 'accepted',
            },
        )

        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, 'accepted')

    @patch('mentorship.views.MentorshipRequest.objects.create')
    def test_requesting_mentor_retries_on_transient_database_lock(self, mock_create):
        mentor_profile = MentorProfile.objects.create(
            user=self.mentor,
            expertise_areas='Growth',
            years_experience=5,
        )
        calls = {'count': 0}

        def flaky_create(*args, **kwargs):
            if calls['count'] == 0:
                calls['count'] += 1
                raise OperationalError('database is locked')
            return MentorshipRequest._base_manager.create(*args, **kwargs)

        mock_create.side_effect = flaky_create

        response = self.client.post(
            reverse('mentors'),
            {
                'request_mentor': '1',
                'mentor_id': mentor_profile.id,
                'message': 'I would love guidance on fundraising.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            MentorshipRequest.objects.filter(founder=self.founder, mentor=mentor_profile).exists()
        )
