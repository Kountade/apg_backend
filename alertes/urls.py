# alertes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AlertesViewset,
    ConfigAlerteViewset,
    CanalNotificationViewset,
)

router = DefaultRouter()

# Agrégateur (pas de CRUD, que des actions GET)
router.register('alertes', AlertesViewset, basename='alertes')

# Config & canaux (CRUD standards)
router.register('alertes-config', ConfigAlerteViewset, basename='alertes-config')
router.register('alertes-canaux', CanalNotificationViewset, basename='alertes-canaux')

urlpatterns = router.urls