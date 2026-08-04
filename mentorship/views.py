from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import OperationalError
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.conf import settings

from core.utils import retry_on_db_lock, send_notification_email
from .models import MentorProfile, MentorshipRequest
from notifications.models import Notification, NotificationPreference


def mentors_view(request):
    mentors = MentorProfile.objects.select_related('user').all()
    mentor_requests = []
    mentor_profile = None

    if request.user.is_authenticated:
        mentor_profile = MentorProfile.objects.filter(user=request.user).first()
        if mentor_profile:
            mentor_requests = mentor_profile.requests.select_related('founder').all()

    if request.method == 'POST':
        if 'become_mentor' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Please sign in to become a mentor.')
                return redirect('login')

            def create_or_update_profile():
                profile, created = MentorProfile.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'expertise_areas': request.POST.get('expertise_areas', ''),
                        'years_experience': int(request.POST.get('years_experience', 0) or 0),
                        'languages': request.POST.get('languages', ''),
                        'bio': request.POST.get('bio', ''),
                        'availability': request.POST.get('availability', 'available'),
                        'hourly_rate': request.POST.get('hourly_rate') or None,
                    },
                )

                if not created:
                    profile.expertise_areas = request.POST.get('expertise_areas', profile.expertise_areas)
                    profile.years_experience = int(request.POST.get('years_experience', profile.years_experience) or profile.years_experience)
                    profile.languages = request.POST.get('languages', profile.languages)
                    profile.bio = request.POST.get('bio', profile.bio)
                    profile.availability = request.POST.get('availability', profile.availability)
                    profile.hourly_rate = request.POST.get('hourly_rate') or profile.hourly_rate
                    profile.save()

                return profile

            retry_on_db_lock(create_or_update_profile)

            messages.success(request, 'Your mentor profile is ready for founders to discover.')
            return redirect('mentors')

        if 'request_mentor' in request.POST and request.user.is_authenticated:
            mentor_id = request.POST.get('mentor_id')
            mentor_profile = MentorProfile.objects.filter(id=mentor_id).first()
            if mentor_profile:
                def create_request_and_notification():
                    mentorship_request = MentorshipRequest.objects.create(
                        mentor=mentor_profile,
                        founder=request.user,
                        message=request.POST.get('message', ''),
                    )

                    Notification.objects.create(
                        recipient=mentor_profile.user,
                        actor=request.user,
                        notification_type='mentorship_request',
                        title='New mentorship request',
                        message=f'{request.user.get_full_name() or request.user.username} requested mentorship for your expertise.',
                        action_url='/mentors/',
                    )
                    return mentorship_request

                try:
                    retry_on_db_lock(create_request_and_notification)
                except OperationalError:
                    messages.error(request, 'We could not process your mentorship request right now. Please try again.')
                    return redirect('mentors')

                if mentor_profile.user.email:
                    email_sent = send_notification_email(
                        'New mentorship request',
                        f'{request.user.get_full_name() or request.user.username} requested mentorship from you.\n\nMessage: {request.POST.get("message", "")}',
                        mentor_profile.user.email,
                    )
                    if not email_sent:
                        messages.warning(request, 'Your request was saved, but the email notification could not be delivered. Please verify your SMTP settings.')

                messages.success(request, 'Your mentorship request has been sent.')
            else:
                messages.error(request, 'That mentor could not be found.')
            return redirect('mentors')

        if 'update_request_status' in request.POST and request.user.is_authenticated:
            request_id = request.POST.get('request_id')
            status = request.POST.get('status', 'pending')
            mentorship_request = MentorshipRequest.objects.filter(id=request_id).first()
            if mentorship_request and mentorship_request.mentor.user == request.user:
                def update_request_status():
                    mentorship_request.status = status
                    mentorship_request.save()

                    Notification.objects.create(
                        recipient=mentorship_request.founder,
                        actor=request.user,
                        notification_type='mentorship_accepted' if status == 'accepted' else 'mentorship_rejected',
                        title='Mentorship request update',
                        message=f'Your mentorship request was marked as {status}.',
                        action_url='/mentors/',
                    )

                try:
                    retry_on_db_lock(update_request_status)
                except OperationalError:
                    messages.error(request, 'We could not update the mentorship request right now. Please try again.')
                    return redirect('mentors')

                if mentorship_request.founder.email:
                    email_sent = send_notification_email(
                        'Mentorship request update',
                        f'Your mentorship request was updated to status: {status}.',
                        mentorship_request.founder.email,
                    )
                    if not email_sent:
                        messages.warning(request, 'The request status was updated, but the email notification could not be delivered.')

                messages.success(request, 'The request status was updated.')
            else:
                messages.error(request, 'You can only update your own mentor requests.')
            return redirect('mentors')

    context = {
        'mentors': mentors,
        'mentor_profile': mentor_profile,
        'mentor_requests': mentor_requests,
    }
    return render(request, 'mentorship/mentors.html', context)
