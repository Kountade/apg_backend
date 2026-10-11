# tresorerie/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CaisseViewset,
    CompteBancaireViewset,
    MouvementTresorerieViewset,
    EncaissementViewset,
    DecaissementViewset,
    MouvementCaisseViewset,
    PrevisionTresorerieViewset,
    AlerteTresorerieViewset,
)

router = DefaultRouter()
router.register('caisses', CaisseViewset, basename='caisses')
router.register('comptes-bancaires', CompteBancaireViewset,
                basename='comptes-bancaires')
router.register('mouvements-tresorerie',
                MouvementTresorerieViewset, basename='mouvements-tresorerie')
router.register('encaissements', EncaissementViewset, basename='encaissements')
router.register('decaissements', DecaissementViewset, basename='decaissements')
router.register('mouvements-caisse', MouvementCaisseViewset,
                basename='mouvements-caisse')
router.register('previsions', PrevisionTresorerieViewset,
                basename='previsions')
router.register('alertes-tresorerie', AlerteTresorerieViewset,
                basename='alertes-tresorerie')

urlpatterns = router.urls
