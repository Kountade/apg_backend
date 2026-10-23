# achats/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FournisseurViewset,
    EvaluationFournisseurViewset,
    DemandeAchatViewset,
    LigneDemandeAchatViewset,
    DevisFournisseurViewset,
    LigneDevisFournisseurViewset,
    BonCommandeViewset,
    LigneBonCommandeViewset,
    ReceptionViewset,
    LigneReceptionViewset,
    FactureFournisseurViewset,
    PaiementFournisseurViewset,
)

router = DefaultRouter()

# Référentiels
router.register('fournisseurs', FournisseurViewset, basename='fournisseurs')
router.register('evaluations-fournisseurs',
                EvaluationFournisseurViewset, basename='evaluations-fournisseurs')

# Demandes d'achat
router.register('demandes-achat', DemandeAchatViewset,
                basename='demandes-achat')
router.register('lignes-demande-achat', LigneDemandeAchatViewset,
                basename='lignes-demande-achat')

# Devis fournisseurs
router.register('devis-fournisseurs', DevisFournisseurViewset,
                basename='devis-fournisseurs')
router.register('lignes-devis-fournisseur',
                LigneDevisFournisseurViewset, basename='lignes-devis-fournisseur')

# Bons de commande
router.register('bons-commande', BonCommandeViewset, basename='bons-commande')
router.register('lignes-bon-commande', LigneBonCommandeViewset,
                basename='lignes-bon-commande')

# Réceptions
router.register('receptions', ReceptionViewset, basename='receptions')
router.register('lignes-reception', LigneReceptionViewset,
                basename='lignes-reception')

# Factures fournisseurs
router.register('factures-fournisseurs', FactureFournisseurViewset,
                basename='factures-fournisseurs')

# Paiements fournisseurs
router.register('paiements-fournisseurs',
                PaiementFournisseurViewset, basename='paiements-fournisseurs')

urlpatterns = router.urls
