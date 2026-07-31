"""
Create test/demo users and starter content for development.
"""
from django.core.management.base import BaseCommand

from accounts.models import User
from funding.models import InvestorInterest
from mentorship.models import MentorProfile
from stories.models import Category, Startup, Story


class Command(BaseCommand):
    help = 'Create demo users and starter content for testing'

    def handle(self, *args, **options):
        roles = [
            ('entrepreneur1', 'Entrepreneur 1', 'entrepreneur'),
            ('mentor1', 'Mentor 1', 'mentor'),
            ('investor1', 'Investor 1', 'investor'),
            ('admin_user', 'Admin', 'admin'),
        ]

        users = {}
        for username, name, role in roles:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@myhopestory.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1] if len(name.split()) > 1 else '',
                    'role': role,
                },
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username} ({role})'))
            else:
                self.stdout.write(f'User {username} already exists')
            users[username] = user

        category, _ = Category.objects.get_or_create(
            slug='ai',
            defaults={'name': 'AI'},
        )

        startup, _ = Startup.objects.get_or_create(
            founder=users['entrepreneur1'],
            startup_name='Demo Startup',
            defaults={
                'industry': 'AI',
                'website': 'https://example.com',
                'founded_year': 2024,
                'team_size': 5,
            },
        )

        story, created_story = Story.objects.get_or_create(
            title='Demo Story',
            defaults={
                'author': users['entrepreneur1'],
                'startup': startup,
                'category': category,
                'summary': 'A demo story for testing mentorship and investor interest flows.',
                'problem_solved': 'Helping founders share lessons and attract support.',
                'business_model': 'Community-driven support and investment readiness.',
                'timeline_content': 'Idea, launch, growth, and lessons learned.',
                'challenges': 'Limited visibility and support.',
                'failure_reason': 'Lack of funding and mentorship.',
                'lessons': 'Consistency and founder-led storytelling matter.',
                'future_plans': 'Expand the platform and grow the community.',
                'status': 'published',
                'visibility': 'public',
            },
        )
        if created_story:
            self.stdout.write(self.style.SUCCESS('Created demo story'))
        else:
            self.stdout.write('Demo story already exists')

        mentor_profile, created_mentor = MentorProfile.objects.get_or_create(
            user=users['mentor1'],
            defaults={
                'expertise_areas': 'Product strategy, fundraising, leadership',
                'years_experience': 8,
                'languages': 'English, Arabic',
                'availability': 'available',
                'hourly_rate': 75,
                'bio': 'Experienced mentor helping founders grow.',
                'verified': True,
            },
        )
        if created_mentor:
            self.stdout.write(self.style.SUCCESS('Created demo mentor profile'))
        else:
            self.stdout.write('Demo mentor profile already exists')

        investor_interest, created_interest = InvestorInterest.objects.get_or_create(
            story=story,
            investor=users['investor1'],
            defaults={
                'investment_amount': 50000,
                'status': 'interested',
                'message': 'Interested in supporting this story.',
            },
        )
        if created_interest:
            self.stdout.write(self.style.SUCCESS('Created demo investor interest'))
        else:
            self.stdout.write('Demo investor interest already exists')

        self.stdout.write(self.style.SUCCESS('Demo users and starter content created successfully'))
