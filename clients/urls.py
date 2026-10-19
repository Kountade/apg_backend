# clients/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClientViewset,
    ContratClientViewset,
    PrestationViewset,
    RelanceViewset,
    TypeContratViewset
)


router = DefaultRouter()

# ============================================================
# CLIENTS & MODULE COMMERCIAL
# ============================================================
router.register('clients', ClientViewset, basename='clients')
router.register('contrats-clients', ContratClientViewset,
                basename='contrats-clients')
router.register('prestations', PrestationViewset, basename='prestations')
router.register('relances', RelanceViewset, basename='relances')

# ============================================================
# RÉFÉRENTIEL DES TYPES DE CONTRATS
# ============================================================
router.register('types-contrats', TypeContratViewset,
                basename='types-contrats')


urlpatterns = router.urls
