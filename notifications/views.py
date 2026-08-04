from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Notification


@login_required
def notifications_inbox_view(request):
    notifications = Notification.objects.filter(recipient=request.user).select_related('actor').all()

    if request.method == 'POST':
        if 'mark_all_read' in request.POST:
            notifications.update(read=True)
            messages.success(request, 'All notifications marked as read.')
            return redirect('notifications_inbox')

        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = notifications.filter(id=notification_id).first()
            if notification:
                notification.read = True
                notification.save()
                messages.success(request, 'Notification marked as read.')
            return redirect('notifications_inbox')

    unread_count = notifications.filter(read=False).count()
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/inbox.html', context)
