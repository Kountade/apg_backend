# rh/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DepartementViewset,
    PosteViewset,
    EmployeViewset,
    ContratViewset,
    PresenceViewset,
    JoursTravaillesViewset,
    CongeViewset,
    SoldeCongeViewset,
    AbsenceViewset,
    EvaluationViewset,
    FormationViewset,
)

router = DefaultRouter()
router.register('departements', DepartementViewset, basename='departements')
router.register('postes', PosteViewset, basename='postes')
router.register('employes', EmployeViewset, basename='employes')
router.register('contrats', ContratViewset, basename='contrats')
router.register('presences', PresenceViewset, basename='presences')
router.register('jours-travailles', JoursTravaillesViewset,
                basename='jours-travailles')
router.register('conges', CongeViewset, basename='conges')
router.register('soldes-conges', SoldeCongeViewset, basename='soldes-conges')
router.register('absences', AbsenceViewset, basename='absences')
router.register('evaluations', EvaluationViewset, basename='evaluations')
router.register('formations', FormationViewset, basename='formations')

urlpatterns = router.urls
