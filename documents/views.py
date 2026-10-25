from django.shortcuts import render

# Create your views here.
# documents/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import date, timedelta

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination

from .models import (
    CategorieDocument, Document, DocumentVersion,
    AccesDocument, TelechargementDocument, PartageDocument,
)
from .serializers import (
    CategorieDocumentSerializer, CategorieDocumentListSerializer,
    DocumentSerializer, DocumentListSerializer, DocumentWriteSerializer,
    DocumentVersionSerializer, DocumentVersionListSerializer,
    AccesDocumentSerializer,
    TelechargementDocumentSerializer,
    PartageDocumentSerializer, PartageDocumentPublicSerializer,
)


# ============================================================
# HELPERS
# ============================================================

def est_pdg_ou_admin(user):
    """Vérifie si l'utilisateur est PDG ou admin."""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) in ['pdg', 'admin']


def peut_voir_document(user, document):
    """
    Vérifie si l'utilisateur peut voir un document selon sa confidentialité.
    - 'public' : tout le monde
    - 'interne' : utilisateurs authentifiés
    - 'confidentiel' : PDG, admin + accès explicite
    - 'secret' : PDG, admin uniquement
    """
    if not user or not user.is_authenticated:
        return document.confidentialite == 'public'

    if est_pdg_ou_admin(user):
        return True

    if document.confidentialite == 'public':
        return True
    if document.confidentialite == 'interne':
        return True
    if document.confidentialite in ['confidentiel', 'secret']:
        # Vérifier un accès explicite
        return AccesDocument.objects.filter(
            document=document, utilisateur=user
        ).exists()

    return False


def filtrer_documents_visibles(queryset, user):
    """Filtre les documents selon les droits de l'utilisateur."""
    if est_pdg_ou_admin(user):
        return queryset

    if not user or not user.is_authenticated:
        return queryset.filter(confidentialite='public')

    # Documents publics + internes + ceux avec accès explicite
    documents_avec_acces = AccesDocument.objects.filter(
        utilisateur=user
    ).values_list('document_id', flat=True)

    return queryset.filter(
        Q(confidentialite__in=['public', 'interne']) |
        Q(id__in=documents_avec_acces)
    )


# ============================================================
# CATÉGORIE DOCUMENT
# ============================================================

class CategorieDocumentViewset(viewsets.ModelViewSet):
    """CRUD Catégories de documents."""
    queryset = CategorieDocument.objects.all()
    pagination_class = StandardPagination
    search_fields = ['code', 'nom', 'description']
    filterset_fields = ['type', 'actif', 'parent']
    ordering_fields = ['ordre', 'nom', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategorieDocumentListSerializer
        return CategorieDocumentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        return Response({'code': CategorieDocument.proposer_code()})

    @action(detail=False, methods=['get'])
    def arbre(self, request):
        """Retourne les catégories racines avec leurs enfants."""
        racines = CategorieDocument.objects.filter(
            parent__isnull=True, actif=True
        ).prefetch_related('sous_categories')

        def serialiser_categorie(cat):
            return {
                'id': cat.id,
                'code': cat.code,
                'nom': cat.nom,
                'type': cat.type,
                'type_display': cat.get_type_display(),
                'nombre_documents': cat.documents.filter(is_deleted=False).count(),
                'enfants': [serialiser_categorie(enfant) for enfant in cat.sous_categories.filter(actif=True)],
            }

        data = [serialiser_categorie(cat) for cat in racines]
        return Response(data)

    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """Catégories groupées par type."""
        data = {}
        for type_val, type_label in CategorieDocument.TYPE_CHOICES:
            categories = CategorieDocument.objects.filter(
                type=type_val, actif=True
            )
            data[type_val] = {
                'label': type_label,
                'categories': CategorieDocumentListSerializer(categories, many=True).data,
            }
        return Response(data)


# ============================================================
# DOCUMENT
# ============================================================

class DocumentViewset(viewsets.ModelViewSet):
    """CRUD Documents."""
    queryset = Document.objects.filter(is_deleted=False).select_related(
        'categorie', 'uploade_par'
    ).prefetch_related('versions')
    pagination_class = StandardPagination
    search_fields = ['numero', 'titre', 'description', 'mots_cles', 'nom_fichier_original']
    filterset_fields = ['categorie', 'statut', 'confidentialite', 'est_version_active']
    ordering_fields = ['titre', 'created_at', 'date_document', 'date_expiration']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DocumentWriteSerializer
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtrer par confidentialité
        return filtrer_documents_visibles(qs, self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            uploade_par=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        return Response({'numero': Document.proposer_numero()})

    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        """
        Télécharge un document et trace le téléchargement.
        Retourne l'URL du fichier.
        """
        document = self.get_object()

        # Vérifier les droits
        if not peut_voir_document(request.user, document):
            return Response(
                {"error": "Vous n'avez pas accès à ce document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Créer la trace
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        TelechargementDocument.objects.create(
            document=document,
            utilisateur=request.user if request.user.is_authenticated else None,
            adresse_ip=ip,
            user_agent=user_agent,
            created_by=request.user if request.user.is_authenticated else None,
        )

        # Retourner l'URL
        if not document.fichier:
            return Response(
                {"error": "Aucun fichier associé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        fichier_url = request.build_absolute_uri(document.fichier.url)
        return Response({
            'fichier_url': fichier_url,
            'nom_fichier': document.nom_fichier_original,
            'taille_formatee': document.taille_formatee,
            'type_mime': document.type_mime,
        })

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Liste les versions d'un document."""
        document = self.get_object()
        versions = document.versions.select_related('uploade_par').all()
        serializer = DocumentVersionListSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def acces(self, request, pk=None):
        """Liste les utilisateurs ayant un accès explicite au document."""
        document = self.get_object()
        acces = document.acces.select_related('utilisateur').all()
        serializer = AccesDocumentSerializer(acces, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def telechargements(self, request, pk=None):
        """Liste les téléchargements d'un document."""
        document = self.get_object()
        telechargements = document.telechargements.select_related(
            'utilisateur'
        ).order_by('-date_telechargement')[:100]
        serializer = TelechargementDocumentSerializer(telechargements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expirent(self, request):
        """Documents qui expirent dans les 30 jours (param ?jours=30)."""
        jours = int(request.query_params.get('jours', 30))
        seuil = date.today() + timedelta(days=jours)
        qs = self.get_queryset().filter(
            date_expiration__isnull=False,
            date_expiration__lte=seuil,
            date_expiration__gte=date.today(),
        ).order_by('date_expiration')
        serializer = DocumentListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expires(self, request):
        """Documents déjà expirés."""
        qs = self.get_queryset().filter(
            date_expiration__isnull=False,
            date_expiration__lt=date.today(),
        ).order_by('-date_expiration')
        serializer = DocumentListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales des documents."""
        qs = self.get_queryset()

        data = {
            'total': qs.count(),
            'par_statut': list(
                qs.values('statut').annotate(total=Count('id')).order_by('-total')
            ),
            'par_confidentialite': list(
                qs.values('confidentialite').annotate(total=Count('id')).order_by('-total')
            ),
            'par_categorie': list(
                qs.values('categorie__nom').annotate(total=Count('id')).order_by('-total')[:10]
            ),
            'taille_totale': qs.aggregate(t=Sum('taille_octets'))['t'] or 0,
            'expires': qs.filter(
                date_expiration__isnull=False,
                date_expiration__lt=date.today(),
            ).count(),
            'expirent_bientot': qs.filter(
                date_expiration__isnull=False,
                date_expiration__lte=date.today() + timedelta(days=30),
                date_expiration__gte=date.today(),
            ).count(),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def par_objet_lie(self, request):
        """
        Récupère les documents liés à un objet spécifique.
        Paramètres : ?type=vehicules.Tricycle&id=42
        """
        type_objet = request.query_params.get('type')
        id_objet = request.query_params.get('id')

        if not type_objet or not id_objet:
            return Response(
                {"error": "Paramètres 'type' et 'id' requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(
            objet_lie_type=type_objet,
            objet_lie_id=str(id_objet),
        )
        serializer = DocumentListSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# VERSION DE DOCUMENT
# ============================================================

class DocumentVersionViewset(viewsets.ModelViewSet):
    """CRUD Versions de documents."""
    queryset = DocumentVersion.objects.select_related(
        'document', 'uploade_par'
    ).all()
    pagination_class = StandardPagination
    filterset_fields = ['document']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentVersionListSerializer
        return DocumentVersionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        version = serializer.save(
            created_by=self.request.user,
            uploade_par=self.request.user,
        )

        # Désactiver les anciennes versions si c'est la nouvelle version active
        if version.document_id:
            DocumentVersion.objects.filter(
                document_id=version.document_id,
                est_version_active=True,
            ).exclude(pk=version.pk).update(est_version_active=False)

        return version


# ============================================================
# ACCÈS DOCUMENT
# ============================================================

class AccesDocumentViewset(viewsets.ModelViewSet):
    """CRUD Accès documents."""
    queryset = AccesDocument.objects.select_related(
        'document', 'utilisateur'
    ).all()
    serializer_class = AccesDocumentSerializer
    pagination_class = StandardPagination
    filterset_fields = ['document', 'utilisateur', 'niveau']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# TÉLÉCHARGEMENT DOCUMENT (lecture seule)
# ============================================================

class TelechargementDocumentViewset(viewsets.ReadOnlyModelViewSet):
    """Lecture seule — les téléchargements sont créés via l'action telecharger."""
    queryset = TelechargementDocument.objects.select_related(
        'document', 'utilisateur'
    ).all()
    serializer_class = TelechargementDocumentSerializer
    pagination_class = StandardPagination
    filterset_fields = ['document', 'utilisateur']
    ordering_fields = ['date_telechargement']

    def get_permissions(self):
        return [CanViewPersonnel()]


# ============================================================
# PARTAGE DOCUMENT
# ============================================================

class PartageDocumentViewset(viewsets.ModelViewSet):
    """CRUD Partages de documents."""
    queryset = PartageDocument.objects.select_related(
        'document', 'cree_par'
    ).all()
    serializer_class = PartageDocumentSerializer
    pagination_class = StandardPagination
    filterset_fields = ['document', 'actif']
    ordering_fields = ['date_expiration', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            cree_par=self.request.user,
        )

    # ============================================================
    # ACTIONS PUBLIQUES (via token)
    # ============================================================

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<token>[^/.]+)',
        permission_classes=[AllowAny],
    )
    def verifier_token(self, request, token=None):
        """
        Vérifie un token de partage (accès PUBLIC).
        Retourne les infos minimales du document partagé.
        """
        partage = get_object_or_404(PartageDocument, token=token)

        if not partage.est_valide:
            return Response(
                {"error": "Ce lien de partage est expiré ou désactivé."},
                status=status.HTTP_410_GONE,
            )

        serializer = PartageDocumentPublicSerializer(
            partage, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='public/(?P<token>[^/.]+)/telecharger',
        permission_classes=[AllowAny],
    )
    def telecharger_public(self, request, token=None):
        """
        Télécharge un document via un lien de partage (accès PUBLIC).
        Incrémente le compteur de téléchargements.
        """
        partage = get_object_or_404(PartageDocument, token=token)

        if not partage.est_valide:
            return Response(
                {"error": "Ce lien de partage est expiré ou désactivé."},
                status=status.HTTP_410_GONE,
            )

        # Vérifier le mot de passe si requis
        if partage.mot_de_passe:
            from django.contrib.auth.hashers import check_password
            mot_de_passe_fourni = request.query_params.get('mot_de_passe', '')
            if not check_password(mot_de_passe_fourni, partage.mot_de_passe):
                return Response(
                    {"error": "Mot de passe incorrect."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        document = partage.document
        if not document or not document.fichier:
            return Response(
                {"error": "Aucun fichier associé à ce partage."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Incrémenter le compteur
        partage.nombre_telechargements += 1
        partage.save(update_fields=['nombre_telechargements'])

        # Tracer le téléchargement
        TelechargementDocument.objects.create(
            document=document,
            utilisateur=None,  # anonyme
            adresse_ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        # Retourner l'URL
        fichier_url = request.build_absolute_uri(document.fichier.url)
        return Response({
            'fichier_url': fichier_url,
            'nom_fichier': document.nom_fichier_original,
            'taille_formatee': document.taille_formatee,
        })