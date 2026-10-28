# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from knox import views as knox_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('config.urls')),
    path('', include('rh.urls')),
    path('', include('clients.urls')),
    path('', include('comptabilite.urls')),
    path('', include('tresorerie.urls')),
    path('', include('paie.urls')),
    path('', include('stocks.urls')),
    path('', include('achats.urls')),
    path('', include('exploitation.urls')),
    path('', include('vehicules.urls')),
    path('', include('documents.urls')),
    path('', include('alertes.urls')),
    path('', include('dashboard.urls')),






    path('api/auth/', include('knox.urls')),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
    path('api/password_reset/',
         include('django_rest_passwordreset.urls', namespace='password_reset')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
