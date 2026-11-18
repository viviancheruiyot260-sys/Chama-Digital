from django.conf import settings


def chama_navigation_context(request):
    """Provides shared role badge counts and USSD code across templates."""
    context = {
        'ussd_shortcode': getattr(settings, 'USSD_SHORTCODE', '*384*240#'),
        'pending_applications_count': 0,
        'unread_treasurer_notifications_count': 0,
    }
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and getattr(user, 'chama', None):
        if user.role == 'CHAIRPERSON' and user.is_approved_member:
            context['pending_applications_count'] = user.chama.members.filter(
                approval_status='PENDING'
            ).count()
        elif user.role == 'TREASURER' and user.is_approved_member:
            from notifications.models import TreasurerNotification
            context['unread_treasurer_notifications_count'] = TreasurerNotification.objects.filter(
                chama=user.chama,
                is_read=False,
            ).count()
    return context
