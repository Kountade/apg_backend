# stocks/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategorieMaterielViewset,
    MagasinViewset,
    ArticleViewset,
    StockMagasinViewset,
    EquipementViewset,
    AffectationEquipementViewset,
    MouvementStockViewset,
    MaintenanceEquipementViewset,
    InventaireViewset,
    LigneInventaireViewset,
)

router = DefaultRouter()

# Référentiels
router.register('categories-materiel', CategorieMaterielViewset,
                basename='categories-materiel')
router.register('magasins', MagasinViewset, basename='magasins')

# Articles & stocks
router.register('articles', ArticleViewset, basename='articles')
router.register('stocks-magasins', StockMagasinViewset,
                basename='stocks-magasins')

# Équipements
router.register('equipements', EquipementViewset, basename='equipements')
router.register('affectations-equipements',
                AffectationEquipementViewset, basename='affectations-equipements')

# Mouvements
router.register('mouvements-stock', MouvementStockViewset,
                basename='mouvements-stock')

# Maintenance
router.register('maintenances', MaintenanceEquipementViewset,
                basename='maintenances')

# Inventaires
router.register('inventaires', InventaireViewset, basename='inventaires')
router.register('lignes-inventaire', LigneInventaireViewset,
                basename='lignes-inventaire')

urlpatterns = router.urls
