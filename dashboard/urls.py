# dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardViewset,
    StatistiquesViewset,
    AnalysesViewset,
)

router = DefaultRouter()

# ============================================================
# 3 ROUTES PRINCIPALES
# ============================================================
router.register('dashboard', DashboardViewset, basename='dashboard')
router.register('statistiques', StatistiquesViewset, basename='statistiques')
router.register('analyses', AnalysesViewset, basename='analyses')

urlpatterns = router.urls
