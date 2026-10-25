# documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategorieDocumentViewset,
    DocumentViewset,
    DocumentVersionViewset,
    AccesDocumentViewset,
    TelechargementDocumentViewset,
    PartageDocumentViewset,
)

router = DefaultRouter()

# Catégories
router.register('categories-documents', CategorieDocumentViewset,
                basename='categories-documents')

# Documents
router.register('documents', DocumentViewset, basename='documents')

# Versions
router.register('documents-versions', DocumentVersionViewset,
                basename='documents-versions')

# Accès
router.register('documents-acces', AccesDocumentViewset,
                basename='documents-acces')

# Téléchargements
router.register('documents-telechargements',
                TelechargementDocumentViewset, basename='documents-telechargements')

# Partages
router.register('documents-partages', PartageDocumentViewset,
                basename='documents-partages')

urlpatterns = router.urls
