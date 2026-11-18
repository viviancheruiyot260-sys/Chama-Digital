from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from accounts.permissions import active_chama_member_required, role_required
from announcements.forms import AnnouncementForm
from announcements.models import Announcement
from .forms import ChamaEventForm
from .models import ChamaEvent


@role_required(User.Role.SECRETARY)
def secretary_dashboard_view(request):
    chama = request.user.chama
    event_form = ChamaEventForm()
    announcement_form = AnnouncementForm()

    if request.method == 'POST':
        action = request.POST.get('form_action')
        if action == 'create_event':
            event_form = ChamaEventForm(request.POST)
            if event_form.is_valid():
                ev = event_form.save(commit=False)
                ev.chama = chama
                ev.organizer = request.user
                ev.save()
                messages.success(request, f'Scheduled "{ev.title}" for {ev.event_date}.')
                return redirect('meetings:secretary_dashboard')
        elif action == 'create_announcement':
            announcement_form = AnnouncementForm(request.POST, request.FILES)
            if announcement_form.is_valid():
                ann = announcement_form.save(commit=False)
                ann.chama = chama
                ann.author = request.user
                ann.save()
                messages.success(request, f'Announcement "{ann.title}" posted.')
                return redirect('meetings:secretary_dashboard')

    members_directory = chama.members.all().order_by('full_name')
    events = ChamaEvent.objects.filter(chama=chama).prefetch_related('attendance_records')
    announcements = Announcement.objects.filter(chama=chama).select_related('author')

    return render(request, 'meetings/secretary_dashboard.html', {
        'chama': chama,
        'members_directory': members_directory,
        'events': events,
        'announcements': announcements,
        'event_form': event_form,
        'announcement_form': announcement_form,
    })


@active_chama_member_required
def meetings_list_view(request):
    chama = request.user.chama
    today = timezone.localdate()
    upcoming = ChamaEvent.objects.filter(
        chama=chama,
        is_cancelled=False,
        event_date__gte=today,
    ).select_related('organizer')
    next_meeting = upcoming.filter(
        event_type__in=[ChamaEvent.EventType.REGULAR_MEETING, ChamaEvent.EventType.AGM]
    ).first() or upcoming.first()
    past_events = ChamaEvent.objects.filter(chama=chama, event_date__lt=today).order_by('-event_date')[:6]

    return render(request, 'meetings/list.html', {
        'next_meeting': next_meeting,
        'upcoming_events': upcoming,
        'past_events': past_events,
        'is_secretary': request.user.role == User.Role.SECRETARY,
    })


@role_required(User.Role.SECRETARY)
def edit_event_view(request, pk):
    ev = get_object_or_404(ChamaEvent, pk=pk, chama=request.user.chama)
    form = ChamaEventForm(request.POST or None, instance=ev)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Updated "{ev.title}".')
        return redirect('meetings:secretary_dashboard')
    return render(request, 'meetings/edit_event.html', {'form': form, 'event': ev})


@role_required(User.Role.SECRETARY)
def cancel_event_view(request, pk):
    if request.method == 'POST':
        ev = get_object_or_404(ChamaEvent, pk=pk, chama=request.user.chama)
        ev.is_cancelled = not ev.is_cancelled
        ev.save()
        state_word = 'cancelled' if ev.is_cancelled else 're-activated'
        messages.warning(request, f'Event "{ev.title}" has been {state_word}.')
    return redirect('meetings:secretary_dashboard')
