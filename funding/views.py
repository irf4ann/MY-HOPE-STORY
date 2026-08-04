from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Donation
from stories.models import Story


@login_required
def checkout_session_view(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        message = request.POST.get('message', '').strip()

        try:
            amount_value = float(amount)
        except (TypeError, ValueError):
            messages.error(request, 'Please enter a valid session amount.')
            return redirect('checkout_session', story_id=story.id)

        if amount_value <= 0:
            messages.error(request, 'Amount must be greater than zero.')
            return redirect('checkout_session', story_id=story.id)

        Donation.objects.create(
            story=story,
            donor=request.user,
            amount=amount_value,
            message=message,
            status='pending',
        )
        messages.success(request, 'Your mentorship session request is ready for payment confirmation.')
        return redirect('checkout_session', story_id=story.id)

    return render(request, 'funding/checkout_session.html', {'story': story})
