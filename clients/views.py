# clients/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta

from core.permissions import (
    CanViewClients, CanEditClients,
    IsPDG, IsComptable,
)
from core.pagination import StandardPagination

from .models import Client, ContratClient, Prestation, Relance, TypeContrat
from .serializers import (
    ClientSerializer, ClientListSerializer, ClientWriteSerializer,
    ContratClientSerializer, ContratClientListSerializer,
    ContratClientValidationSerializer,
    PrestationSerializer,
    RelanceSerializer,
    TypeContratSerializer, TypeContratListSerializer,
)


# ============================================================
# TYPE DE CONTRAT (référentiel)
# ============================================================

class TypeContratViewset(viewsets.ModelViewSet):
    """CRUD des types de contrats (référentiel)."""
    queryset = TypeContrat.objects.all()
    pagination_class = StandardPagination
    search_fields = ['code', 'titre', 'description', 'reference_legale']
    filterset_fields = ['categorie', 'statut']
    ordering_fields = ['titre', 'ordre', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TypeContratListSerializer
        return TypeContratSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditClients()]
        return [CanViewClients()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code proposé (sans l'enregistrer)."""
        code = TypeContrat.proposer_code()
        return Response({'code': code})

    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Liste les types de contrats actifs (pour les formulaires)."""
        qs = TypeContrat.objects.filter(statut='actif')
        serializer = TypeContratListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """Retourne les types de contrats groupés par catégorie."""
        qs = TypeContrat.objects.filter(statut='actif')
        categories = {}
        for t in qs:
            if t.categorie not in categories:
                categories[t.categorie] = {
                    'categorie': t.categorie,
                    'label': t.get_categorie_display(),
                    'types': [],
                }
            categories[t.categorie]['types'].append(
                TypeContratListSerializer(t).data
            )
        return Response(list(categories.values()))

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des types de contrats."""
        qs = TypeContrat.objects.all()
        data = {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'par_categorie': list(
                qs.values('categorie').annotate(
                    total=Count('id')
                ).order_by('-total')
            ),
        }
        return Response(data)


# ============================================================
# CLIENT
# ============================================================

class ClientViewset(viewsets.ModelViewSet):
    """CRUD Clients APG."""
    queryset = Client.objects.filter(is_deleted=False)
    pagination_class = StandardPagination
    search_fields = ['code', 'nom', 'prenom', 'telephone', 'email', 'zone']
    filterset_fields = ['type', 'statut', 'zone']
    ordering_fields = ['nom', 'code']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ClientWriteSerializer
        if self.action == 'list':
            return ClientListSerializer
        return ClientSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditClients()]
        return [CanViewClients()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete."""
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def contrats(self, request, pk=None):
        """Liste les contrats d'un client."""
        client = self.get_object()
        contrats = client.contrats.select_related('type_contrat').all()
        serializer = ContratClientSerializer(contrats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def factures(self, request, pk=None):
        """Liste les factures d'un client (vide tant que comptabilite n'existe pas)."""
        return Response([])

    @action(detail=True, methods=['get'])
    def relances(self, request, pk=None):
        """Liste les relances d'un client."""
        client = self.get_object()
        relances = client.relances.all()
        serializer = RelanceSerializer(relances, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales clients."""
        qs = Client.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'par_type': list(
                qs.values('type').annotate(
                    total=Count('id')).order_by('-total')
            ),
            'par_zone': list(
                qs.values('zone').annotate(
                    total=Count('id')).order_by('-total')
            ),
            'nouveaux_ce_mois': qs.filter(
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year,
            ).count(),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def avec_solde(self, request):
        """Clients avec solde dû (retourne vide tant que comptabilite n'existe pas)."""
        return Response([])


# ============================================================
# CONTRAT CLIENT
# ============================================================

class ContratClientViewset(viewsets.ModelViewSet):
    """CRUD Contrats clients."""
    queryset = ContratClient.objects.select_related(
        'client', 'equipe', 'type_contrat'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom',
                     'prestation', 'type_contrat__titre']
    filterset_fields = ['statut', 'client', 'frequence', 'type_contrat']
    ordering_fields = ['date_debut', 'date_fin', 'tarif']

    def get_serializer_class(self):
        if self.action == 'list':
            return ContratClientListSerializer
        return ContratClientSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'valider', 'resilier', 'suspendre']:
            return [CanEditClients()]
        return [CanViewClients()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro de contrat proposé (sans l'enregistrer)."""
        numero = ContratClient.proposer_numero()
        return Response({'numero': numero})

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider un contrat."""
        contrat = self.get_object()
        if contrat.statut not in ['brouillon', 'suspendu']:
            return Response(
                {"error": "Ce contrat ne peut pas être validé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contrat.statut = 'actif'
        contrat.valide_par = request.user
        contrat.date_validation = timezone.now()
        contrat.save()
        return Response(ContratClientSerializer(contrat).data)

    @action(detail=True, methods=['post'])
    def resilier(self, request, pk=None):
        """Résilier un contrat."""
        contrat = self.get_object()
        contrat.statut = 'resilie'
        contrat.save()
        return Response(ContratClientSerializer(contrat).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        """Suspendre un contrat."""
        contrat = self.get_object()
        contrat.statut = 'suspendu'
        contrat.save()
        return Response(ContratClientSerializer(contrat).data)

    @action(detail=False, methods=['get'])
    def expirant(self, request):
        """Contrats qui expirent dans les 30 prochains jours."""
        seuil = date.today() + timedelta(days=30)
        qs = ContratClient.objects.filter(
            statut='actif',
            date_fin__lte=seuil,
            date_fin__gte=date.today()
        ).select_related('client', 'type_contrat')
        serializer = ContratClientListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Contrats actifs."""
        qs = ContratClient.objects.filter(
            statut='actif'
        ).select_related('client', 'type_contrat')
        serializer = ContratClientListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """Contrats groupés par type de contrat."""
        qs = ContratClient.objects.select_related(
            'client', 'type_contrat'
        ).all()
        types = {}
        for c in qs:
            key = c.type_contrat_id or 'sans_type'
            if key not in types:
                types[key] = {
                    'type_contrat': c.type_contrat_id,
                    'type_contrat_titre': (
                        c.type_contrat.titre if c.type_contrat else 'Sans type'
                    ),
                    'contrats': [],
                }
            types[key]['contrats'].append(
                ContratClientListSerializer(c).data
            )
        return Response(list(types.values()))


# ============================================================
# PRESTATION
# ============================================================

class PrestationViewset(viewsets.ModelViewSet):
    """CRUD Prestations."""
    queryset = Prestation.objects.all()
    serializer_class = PrestationSerializer
    pagination_class = StandardPagination
    search_fields = ['code', 'nom']
    filterset_fields = ['actif']
    ordering_fields = ['nom', 'tarif_base']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditClients()]
        return [CanViewClients()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_code(self, request):
        """Retourne le prochain code prestation proposé (sans l'enregistrer)."""
        code = Prestation.proposer_code()
        return Response({'code': code})


# ============================================================
# RELANCE
# ============================================================

class RelanceViewset(viewsets.ModelViewSet):
    """CRUD Relances."""
    queryset = Relance.objects.select_related('client').all()
    serializer_class = RelanceSerializer
    pagination_class = StandardPagination
    filterset_fields = ['client', 'type']
    ordering_fields = ['date_relance']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditClients()]
        return [CanViewClients()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def par_client(self, request):
        """Relances d'un client donné."""
        client_id = request.query_params.get('client_id')
        qs = Relance.objects.all()
        if client_id:
            qs = qs.filter(client_id=client_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
