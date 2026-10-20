# comptabilite/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CompteComptableViewset,
    JournalViewset,
    FactureViewset,
    DevisViewset,
    AvoirViewset,
    PaiementClientViewset,
    LitigeViewset,
    EcritureComptableViewset,
    LettrageViewset,
    DeclarationFiscaleViewset,
    ClotureComptableViewset,  
)

router = DefaultRouter()

router.register('comptes-comptables', CompteComptableViewset, basename='comptes-comptables')
router.register('journaux', JournalViewset, basename='journaux')
router.register('factures', FactureViewset, basename='factures')
router.register('devis', DevisViewset, basename='devis')
router.register('avoirs', AvoirViewset, basename='avoirs')
router.register('paiements-clients', PaiementClientViewset, basename='paiements-clients')
router.register('litiges', LitigeViewset, basename='litiges')
router.register('ecritures-comptables', EcritureComptableViewset, basename='ecritures-comptables')
router.register('lettrages', LettrageViewset, basename='lettrages')
router.register('declarations-fiscales', DeclarationFiscaleViewset, basename='declarations-fiscales')
router.register('clotures', ClotureComptableViewset, basename='clotures')  

urlpatterns = router.urls