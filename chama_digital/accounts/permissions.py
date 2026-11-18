from functools import wraps
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


def active_chama_member_required(view_func):
    """
    Blocks unauthenticated, pending-approval, and rejected users at the server level.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access your Chama Digital account.')
            return redirect('accounts:login')

        if request.user.approval_status == 'PENDING':
            return redirect('accounts:pending_approval')

        if request.user.approval_status == 'REJECTED':
            logout(request)
            messages.error(
                request,
                'Your membership application was declined by the Chairperson. Access is disabled.',
            )
            return redirect('accounts:login')

        if not request.user.chama:
            messages.error(request, 'Your account is not assigned to a Chama group.')
            return redirect('home')

        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*allowed_roles):
    """
    Enforces role-based permissions in Django views (in addition to active approval).
    """

    def decorator(view_func):
        @wraps(view_func)
        @active_chama_member_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    'You do not have permission to view that role dashboard.',
                )
                return redirect(request.user.get_dashboard_url_name())
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
