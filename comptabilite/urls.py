# comptabilite/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CompteComptableViewset,
    JournalViewset,
    FactureViewset,
    DevisViewset,
    EcritureComptableViewset,
    LettrageViewset,
    DeclarationFiscaleViewset,
)

router = DefaultRouter()
router.register('comptes-comptables', CompteComptableViewset,
                basename='comptes-comptables')
router.register('journaux', JournalViewset, basename='journaux')
router.register('factures', FactureViewset, basename='factures')
router.register('devis', DevisViewset, basename='devis')
router.register('ecritures-comptables', EcritureComptableViewset,
                basename='ecritures-comptables')
router.register('lettrages', LettrageViewset, basename='lettrages')
router.register('declarations-fiscales', DeclarationFiscaleViewset,
                basename='declarations-fiscales')

urlpatterns = router.urls
