# stocks/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from datetime import date, timedelta

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination

from .models import (
    CategorieMateriel, Magasin, Article, StockMagasin,
    Equipement, AffectationEquipement, MouvementStock,
    MaintenanceEquipement, Inventaire, LigneInventaire,
)
from .serializers import (
    CategorieMaterielSerializer, CategorieMaterielListSerializer,
    MagasinSerializer, MagasinListSerializer,
    ArticleSerializer, ArticleListSerializer, ArticleWriteSerializer,
    StockMagasinSerializer,
    EquipementSerializer, EquipementListSerializer,
    AffectationEquipementSerializer,
    MouvementStockSerializer, MouvementStockListSerializer,
    MaintenanceEquipementSerializer,
    InventaireSerializer, InventaireListSerializer,
    LigneInventaireSerializer,
)


# ============================================================
# CATÉGORIE MATÉRIEL
# ============================================================

class CategorieMaterielViewset(viewsets.ModelViewSet):
    """CRUD Catégories de matériel."""
    queryset = CategorieMateriel.objects.all()
    pagination_class = StandardPagination
    search_fields = ['nom', 'code']
    filterset_fields = ['type', 'actif']
    ordering_fields = ['nom', 'type']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategorieMaterielListSerializer
        return CategorieMaterielSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code proposé."""
        return Response({'code': CategorieMateriel.proposer_code()})

    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """Catégories groupées par type."""
        data = {}
        for type_val, type_label in CategorieMateriel.TYPE_CHOICES:
            categories = CategorieMateriel.objects.filter(
                type=type_val, actif=True)
            data[type_val] = {
                'label': type_label,
                'categories': CategorieMaterielListSerializer(categories, many=True).data,
            }
        return Response(data)


# ============================================================
# MAGASIN
# ============================================================

class MagasinViewset(viewsets.ModelViewSet):
    """CRUD Magasins / Dépôts."""
    queryset = Magasin.objects.select_related('responsable').all()
    pagination_class = StandardPagination
    search_fields = ['code', 'nom', 'zone']
    filterset_fields = ['type', 'actif']
    ordering_fields = ['nom', 'code']

    def get_serializer_class(self):
        if self.action == 'list':
            return MagasinListSerializer
        return MagasinSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code proposé."""
        return Response({'code': Magasin.proposer_code()})


# ============================================================
# ARTICLE
# ============================================================

class ArticleViewset(viewsets.ModelViewSet):
    """CRUD Articles (consommables)."""
    queryset = Article.objects.filter(is_deleted=False).select_related(
        'categorie').prefetch_related('stocks_magasins')
    pagination_class = StandardPagination
    search_fields = ['code', 'designation', 'description']
    filterset_fields = ['categorie', 'actif', 'unite']
    ordering_fields = ['designation', 'code', 'prix_achat']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ArticleWriteSerializer
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code proposé."""
        return Response({'code': Article.proposer_code()})

    @action(detail=False, methods=['get'])
    def stock_critique(self, request):
        """Articles en stock critique."""
        articles = Article.objects.filter(is_deleted=False)
        critiques = [a for a in articles if a.est_critique]
        serializer = ArticleListSerializer(critiques, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def en_alerte(self, request):
        """Articles en alerte (seuil dépassé)."""
        articles = Article.objects.filter(is_deleted=False)
        alertes = [a for a in articles if a.est_en_alerte and not a.est_critique]
        serializer = ArticleListSerializer(alertes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales articles."""
        qs = Article.objects.filter(is_deleted=False)
        all_articles = list(qs)
        data = {
            'total': len(all_articles),
            'actifs': qs.filter(actif=True).count(),
            'en_alerte': len([a for a in all_articles if a.est_en_alerte]),
            'critiques': len([a for a in all_articles if a.est_critique]),
            'par_categorie': list(
                qs.values('categorie__nom').annotate(
                    total=Count('id')).order_by('-total')
            ),
        }
        return Response(data)

    @action(detail=True, methods=['get'])
    def stocks(self, request, pk=None):
        """Stocks par magasin pour un article."""
        article = self.get_object()
        stocks = article.stocks_magasins.select_related('magasin').all()
        serializer = StockMagasinSerializer(stocks, many=True)
        return Response(serializer.data)


# ============================================================
# STOCK PAR MAGASIN
# ============================================================

class StockMagasinViewset(viewsets.ModelViewSet):
    """CRUD Stocks par magasin."""
    queryset = StockMagasin.objects.select_related('article', 'magasin').all()
    serializer_class = StockMagasinSerializer
    pagination_class = StandardPagination
    filterset_fields = ['article', 'magasin']
    ordering_fields = ['quantite']


# ============================================================
# ÉQUIPEMENT
# ============================================================

class EquipementViewset(viewsets.ModelViewSet):
    """CRUD Équipements durables."""
    queryset = Equipement.objects.filter(is_deleted=False).select_related(
        'categorie', 'magasin', 'responsable')
    pagination_class = StandardPagination
    search_fields = ['code', 'designation', 'numero_serie', 'marque', 'modele']
    filterset_fields = ['categorie', 'etat', 'magasin', 'actif']
    ordering_fields = ['designation', 'code', 'date_acquisition']

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipementListSerializer
        return EquipementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code proposé."""
        return Response({'code': Equipement.proposer_code()})

    @action(detail=False, methods=['get'])
    def sous_garantie(self, request):
        """Équipements encore sous garantie."""
        equipements = Equipement.objects.filter(is_deleted=False)
        sous_garantie = [e for e in equipements if e.est_sous_garantie]
        serializer = EquipementListSerializer(sous_garantie, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques équipements."""
        qs = Equipement.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'actifs': qs.filter(actif=True).count(),
            'par_etat': list(
                qs.values('etat').annotate(
                    total=Count('id')).order_by('-total')
            ),
            'valeur_totale': qs.aggregate(t=Sum('cout_acquisition'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# AFFECTATION ÉQUIPEMENT
# ============================================================

class AffectationEquipementViewset(viewsets.ModelViewSet):
    """CRUD Affectations d'équipements."""
    queryset = AffectationEquipement.objects.select_related(
        'equipement', 'employe').all()
    serializer_class = AffectationEquipementSerializer
    pagination_class = StandardPagination
    search_fields = ['equipement__designation', 'employe__nom', 'equipe_nom']
    filterset_fields = ['equipement', 'employe']
    ordering_fields = ['date_affectation', 'date_retour']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def retour(self, request, pk=None):
        """Marquer une affectation comme retournée."""
        affectation = self.get_object()
        if affectation.date_retour:
            return Response(
                {"error": "Cet équipement a déjà été retourné."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        affectation.date_retour = date.today()
        affectation.etat_apres = request.data.get('etat_apres', '')
        affectation.observation = request.data.get(
            'observation', affectation.observation)
        affectation.save()
        return Response(AffectationEquipementSerializer(affectation).data)

    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """Affectations en cours (non retournées)."""
        qs = AffectationEquipement.objects.filter(
            date_retour__isnull=True
        ).select_related('equipement', 'employe')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# MOUVEMENT DE STOCK
# ============================================================

class MouvementStockViewset(viewsets.ModelViewSet):
    """CRUD Mouvements de stock."""
    queryset = MouvementStock.objects.select_related(
        'article', 'magasin_source', 'magasin_destination', 'employe_beneficiaire'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'article__designation',
                     'beneficiaire', 'reference']
    filterset_fields = ['type', 'motif', 'article',
                        'magasin_source', 'magasin_destination']
    ordering_fields = ['date_mouvement', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return MouvementStockListSerializer
        return MouvementStockSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro proposé."""
        return Response({'numero': MouvementStock.proposer_numero()})

    @action(detail=False, methods=['get'])
    def entrees(self, request):
        """Mouvements d'entrée."""
        qs = MouvementStock.objects.filter(
            type='entree'
        ).select_related('article', 'magasin_destination')
        serializer = MouvementStockListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sorties(self, request):
        """Mouvements de sortie."""
        qs = MouvementStock.objects.filter(
            type='sortie'
        ).select_related('article', 'magasin_source')
        serializer = MouvementStockListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def transferts(self, request):
        """Mouvements de transfert."""
        qs = MouvementStock.objects.filter(
            type='transfert'
        ).select_related('article', 'magasin_source', 'magasin_destination')
        serializer = MouvementStockListSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# MAINTENANCE ÉQUIPEMENT
# ============================================================

class MaintenanceEquipementViewset(viewsets.ModelViewSet):
    """CRUD Maintenances d'équipements."""
    queryset = MaintenanceEquipement.objects.select_related('equipement').all()
    serializer_class = MaintenanceEquipementSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'equipement__code',
                     'equipement__designation', 'technicien']
    filterset_fields = ['equipement', 'type', 'statut']
    ordering_fields = ['date_debut', 'numero']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro proposé."""
        return Response({'numero': MaintenanceEquipement.proposer_numero()})

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """Marquer une maintenance comme terminée."""
        maintenance = self.get_object()
        if maintenance.statut == 'terminee':
            return Response(
                {"error": "Cette maintenance est déjà terminée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        maintenance.statut = 'terminee'
        maintenance.date_fin = request.data.get('date_fin', date.today())
        maintenance.save()
        return Response(MaintenanceEquipementSerializer(maintenance).data)


# ============================================================
# INVENTAIRE
# ============================================================

class InventaireViewset(viewsets.ModelViewSet):
    """CRUD Inventaires."""
    queryset = Inventaire.objects.select_related(
        'magasin', 'responsable').prefetch_related('lignes').all()
    pagination_class = StandardPagination
    search_fields = ['reference', 'magasin__nom']
    filterset_fields = ['magasin', 'statut']
    ordering_fields = ['date_inventaire', 'reference']

    def get_serializer_class(self):
        if self.action == 'list':
            return InventaireListSerializer
        return InventaireSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            responsable=self.request.user,
        )

    @action(detail=False, methods=['get'])
    def prochaine_reference(self, request):
        """Retourne la prochaine référence proposée."""
        return Response({'reference': Inventaire.proposer_reference()})

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider un inventaire et ajuster les stocks."""
        inventaire = self.get_object()
        if inventaire.statut == 'valide':
            return Response(
                {"error": "Cet inventaire est déjà validé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inventaire.statut = 'valide'
        inventaire.save()

        # Créer les mouvements d'ajustement pour les écarts
        for ligne in inventaire.lignes.all():
            if ligne.ecart != 0:
                MouvementStock.objects.create(
                    type='ajustement',
                    motif='correction',
                    article=ligne.article,
                    quantite=abs(ligne.ecart),
                    magasin_source=inventaire.magasin if ligne.ecart < 0 else None,
                    magasin_destination=inventaire.magasin if ligne.ecart > 0 else None,
                    reference=inventaire.reference,
                    observation=f"Ajustement suite à inventaire {inventaire.reference}",
                    created_by=request.user,
                )

        return Response(InventaireSerializer(inventaire).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler un inventaire."""
        inventaire = self.get_object()
        if inventaire.statut == 'valide':
            return Response(
                {"error": "Impossible d'annuler un inventaire validé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inventaire.statut = 'annule'
        inventaire.save()
        return Response(InventaireSerializer(inventaire).data)


# ============================================================
# LIGNE INVENTAIRE
# ============================================================

class LigneInventaireViewset(viewsets.ModelViewSet):
    """CRUD Lignes d'inventaire."""
    queryset = LigneInventaire.objects.select_related(
        'inventaire', 'article').all()
    serializer_class = LigneInventaireSerializer
    pagination_class = StandardPagination
    filterset_fields = ['inventaire', 'article']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]
