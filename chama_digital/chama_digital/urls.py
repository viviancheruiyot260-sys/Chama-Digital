from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('members/', include('members.urls')),
    path('savings/', include('savings.urls')),
    path('payments/', include('payments.urls')),
    path('loans/', include('loans.urls')),
    path('announcements/', include('announcements.urls')),
    path('meetings/', include('meetings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
