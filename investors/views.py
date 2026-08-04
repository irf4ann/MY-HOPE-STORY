from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import OperationalError
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.conf import settings

from core.utils import retry_on_db_lock, send_notification_email
from funding.models import InvestorInterest
from stories.models import Story
from notifications.models import Notification


@login_required
def investors_view(request):
    stories = Story.objects.filter(status='published').select_related('startup', 'author')[:12]
    investor_interests = InvestorInterest.objects.filter(investor=request.user).select_related('story', 'story__startup').all()

    if request.method == 'POST':
        if 'express_interest' in request.POST:
            story_id = request.POST.get('story_id')
            story = Story.objects.filter(id=story_id).first()
            if story:
                def save_interest():
                    interest, _ = InvestorInterest.objects.update_or_create(
                        story=story,
                        investor=request.user,
                        defaults={
                            'investment_amount': request.POST.get('investment_amount') or None,
                            'message': request.POST.get('message', ''),
                            'status': 'interested',
                        },
                    )

                    Notification.objects.create(
                        recipient=story.author,
                        actor=request.user,
                        notification_type='investor_interested',
                        title='New investor interest',
                        message=f'{request.user.get_full_name() or request.user.username} expressed interest in your story.',
                        action_url='/investors/',
                    )
                    return interest

                try:
                    retry_on_db_lock(save_interest)
                except OperationalError:
                    messages.error(request, 'We could not save your investor interest right now. Please try again.')
                    return redirect('investors')

                if story.author.email:
                    email_sent = send_notification_email(
                        'New investor interest',
                        f'{request.user.get_full_name() or request.user.username} expressed interest in your story.\n\nMessage: {request.POST.get("message", "")}',
                        story.author.email,
                    )
                    if not email_sent:
                        messages.warning(request, 'Your interest was saved, but the email notification could not be delivered. Please verify your SMTP settings.')

                messages.success(request, 'Your investor interest has been recorded.')
            else:
                messages.error(request, 'That story could not be found.')
            return redirect('investors')

        if 'update_interest_status' in request.POST:
            interest_id = request.POST.get('interest_id')
            status = request.POST.get('status', 'interested')
            interest = InvestorInterest.objects.filter(id=interest_id, investor=request.user).first()
            if interest:
                def update_interest_status():
                    interest.status = status
                    interest.save()

                    Notification.objects.create(
                        recipient=interest.investor,
                        actor=request.user,
                        notification_type='investor_interested',
                        title='Investor interest update',
                        message=f'Your interest status was updated to {status}.',
                        action_url='/investors/',
                    )

                try:
                    retry_on_db_lock(update_interest_status)
                except OperationalError:
                    messages.error(request, 'We could not update the interest status right now. Please try again.')
                    return redirect('investors')

                if interest.investor.email:
                    email_sent = send_notification_email(
                        'Investor interest update',
                        f'Your interest status was updated to {status}.',
                        interest.investor.email,
                    )
                    if not email_sent:
                        messages.warning(request, 'The status update was saved, but the email notification could not be delivered.')

                messages.success(request, 'The interest status was updated.')
            else:
                messages.error(request, 'You can only update your own interest entries.')
            return redirect('investors')

    return render(request, 'investors/investors.html', {
        'stories': stories,
        'investor_interests': investor_interests,
    })
