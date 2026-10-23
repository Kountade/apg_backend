# vehicules/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TricycleViewset,
    VehiculeViewset,
    ConducteurViewset,
    AffectationVehiculeViewset,
    DocumentVehiculeViewset,
    AssuranceViewset,
    SuiviGPSViewset,
    PleinCarburantViewset,
)

router = DefaultRouter()

# Tricycles & Véhicules
router.register('tricycles', TricycleViewset, basename='tricycles')
router.register('vehicules', VehiculeViewset, basename='vehicules')

# Conducteurs
router.register('conducteurs', ConducteurViewset, basename='conducteurs')

# Affectations
router.register('affectations-vehicules',
                AffectationVehiculeViewset, basename='affectations-vehicules')

# Documents
router.register('documents-vehicules', DocumentVehiculeViewset,
                basename='documents-vehicules')

# Assurances
router.register('assurances', AssuranceViewset, basename='assurances')

# GPS
router.register('suivi-gps', SuiviGPSViewset, basename='suivi-gps')

# Carburant
router.register('pleins-carburant', PleinCarburantViewset,
                basename='pleins-carburant')

urlpatterns = router.urls
