# paie/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PeriodePaieViewset,
    BulletinPaieViewset,
    LigneBulletinViewset,
    PrimeViewset,
    RetenueViewset,
    AvanceSalaireViewset,
    FichePaieViewset,
)

router = DefaultRouter()
router.register('periodes-paie', PeriodePaieViewset, basename='periodes-paie')
router.register('bulletins-paie', BulletinPaieViewset, basename='bulletins-paie')
router.register('lignes-bulletin', LigneBulletinViewset, basename='lignes-bulletin')
router.register('primes', PrimeViewset, basename='primes')
router.register('retenues', RetenueViewset, basename='retenues')
router.register('avances-salaire', AvanceSalaireViewset, basename='avances-salaire')
router.register('fiches-paie', FichePaieViewset, basename='fiches-paie')

urlpatterns = router.urls