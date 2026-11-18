from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from accounts.permissions import active_chama_member_required, role_required
from .forms import AnnouncementForm
from .models import Announcement


@active_chama_member_required
def announcement_list_view(request):
    category_filter = request.GET.get('category', 'ALL')
    items = Announcement.objects.filter(chama=request.user.chama).select_related('author')
    if category_filter != 'ALL':
        items = items.filter(category=category_filter)

    return render(request, 'announcements/list.html', {
        'announcements': items,
        'category_filter': category_filter,
        'categories': Announcement.Category.choices,
        'can_post': request.user.role in (User.Role.CHAIRPERSON, User.Role.SECRETARY),
    })


@active_chama_member_required
def announcement_detail_view(request, pk):
    item = get_object_or_404(Announcement, pk=pk, chama=request.user.chama)
    return render(request, 'announcements/detail.html', {'announcement': item})


@role_required(User.Role.CHAIRPERSON, User.Role.SECRETARY)
def create_announcement_view(request):
    form = AnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ann = form.save(commit=False)
        ann.chama = request.user.chama
        ann.author = request.user
        ann.save()
        messages.success(request, f'Announcement "{ann.title}" published to all chama members.')
        if request.user.role == User.Role.SECRETARY:
            return redirect('meetings:secretary_dashboard')
        return redirect('announcements:list')

    return render(request, 'announcements/create.html', {'form': form})
