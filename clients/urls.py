# clients/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClientViewset,
    ContratClientViewset,
    PrestationViewset,
    RelanceViewset,
)

router = DefaultRouter()
router.register('clients', ClientViewset, basename='clients')
router.register('contrats-clients', ContratClientViewset,
                basename='contrats-clients')
router.register('prestations', PrestationViewset, basename='prestations')
router.register('relances', RelanceViewset, basename='relances')

urlpatterns = router.urls
