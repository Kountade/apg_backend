from django.shortcuts import render

# Create your views here.
# paie/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta

from core.permissions import (
    CanViewPaie, CanPreparePaie, CanValidatePaie,
    IsPDG, IsRH, IsComptable,
)
from core.pagination import StandardPagination

from .models import (
    PeriodePaie, BulletinPaie, LigneBulletin,
    Prime, Retenue, AvanceSalaire, FichePaie,
)
from .serializers import (
    PeriodePaieSerializer, PeriodePaieListSerializer,
    BulletinPaieSerializer, BulletinPaieListSerializer,
    LigneBulletinSerializer,
    PrimeSerializer,
    RetenueSerializer,
    AvanceSalaireSerializer, AvanceSalaireListSerializer,
    FichePaieSerializer,
)


# ============================================================
# PÉRIODE DE PAIE
# ============================================================

class PeriodePaieViewset(viewsets.ModelViewSet):
    """CRUD Périodes de paie."""
    queryset = PeriodePaie.objects.all()
    pagination_class = StandardPagination
    search_fields = ['libelle']
    filterset_fields = ['statut', 'mois', 'annee']
    ordering_fields = ['-annee', '-mois', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PeriodePaieListSerializer
        return PeriodePaieSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        if self.action in ['valider', 'rejeter']:
            return [CanValidatePaie()]
        if self.action in ['calculer', 'controler']:
            return [CanPreparePaie()]
        return [CanViewPaie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def calculer(self, request, pk=None):
        """Calcule tous les bulletins de la période."""
        periode = self.get_object()
        if periode.statut not in ['ouverte', 'en_preparation']:
            return Response(
                {"error": "La période ne peut pas être calculée dans son état actuel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Logique de calcul (à adapter selon vos règles métier)
        # Pour l'instant on marque juste comme calculée
        periode.statut = 'calculee'
        periode.preparee_par = request.user
        periode.save()

        return Response(PeriodePaieSerializer(periode).data)

    @action(detail=True, methods=['post'])
    def controler(self, request, pk=None):
        """Contrôle la période."""
        periode = self.get_object()
        if periode.statut != 'calculee':
            return Response(
                {"error": "La période doit être calculée avant d'être contrôlée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        periode.statut = 'controlee'
        periode.controlee_par = request.user
        periode.date_controle = timezone.now()
        periode.save()

        return Response(PeriodePaieSerializer(periode).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide la période."""
        periode = self.get_object()
        if periode.statut != 'controlee':
            return Response(
                {"error": "La période doit être contrôlée avant d'être validée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        periode.statut = 'validee'
        periode.validee_par = request.user
        periode.date_validation = timezone.now()
        periode.save()

        return Response(PeriodePaieSerializer(periode).data)

    @action(detail=True, methods=['post'])
    def marquer_payee(self, request, pk=None):
        """Marque la période comme payée."""
        periode = self.get_object()
        if periode.statut not in ['validee', 'en_attente_paiement']:
            return Response(
                {"error": "La période doit être validée avant d'être payée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        periode.statut = 'payee'
        periode.payee_par = request.user
        periode.date_paiement = timezone.now()
        periode.save()

        # Marquer les bulletins comme payés
        periode.bulletins.update(
            statut='paye',
            date_paiement=date.today(),
        )

        return Response(PeriodePaieSerializer(periode).data)

    @action(detail=True, methods=['post'])
    def recalculer_totaux(self, request, pk=None):
        """Recalcule les totaux depuis les bulletins."""
        periode = self.get_object()
        periode.recalculer_totaux()
        return Response(PeriodePaieSerializer(periode).data)

    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        """Périodes en cours (non clôturées ni annulées)."""
        qs = PeriodePaie.objects.exclude(statut__in=['cloturee', 'annulee'])
        serializer = PeriodePaieListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales paie."""
        qs = PeriodePaie.objects.all()
        data = {
            'total': qs.count(),
            'ouvertes': qs.filter(statut='ouverte').count(),
            'en_preparation': qs.filter(statut='en_preparation').count(),
            'calculees': qs.filter(statut='calculee').count(),
            'validees': qs.filter(statut='validee').count(),
            'payees': qs.filter(statut='payee').count(),
            'masse_salariale_totale': qs.aggregate(t=Sum('total_net'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# BULLETIN DE PAIE
# ============================================================

class BulletinPaieViewset(viewsets.ModelViewSet):
    """CRUD Bulletins de paie."""
    queryset = BulletinPaie.objects.select_related(
        'periode', 'employe', 'decaissement'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'employe__nom',
                     'employe__prenom', 'matricule_snapshot']
    filterset_fields = ['statut', 'periode', 'employe']
    ordering_fields = ['numero', 'salaire_net', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BulletinPaieListSerializer
        return BulletinPaieSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        if self.action in ['valider', 'marquer_paye']:
            return [CanValidatePaie()]
        return [CanViewPaie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def calculer(self, request, pk=None):
        """Calcule le bulletin."""
        bulletin = self.get_object()
        bulletin.calculer()
        return Response(BulletinPaieSerializer(bulletin).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un bulletin."""
        bulletin = self.get_object()
        bulletin.statut = 'valide'
        bulletin.save()
        return Response(BulletinPaieSerializer(bulletin).data)

    @action(detail=True, methods=['post'])
    def marquer_paye(self, request, pk=None):
        """Marque un bulletin comme payé."""
        bulletin = self.get_object()
        bulletin.statut = 'paye'
        bulletin.date_paiement = date.today()
        bulletin.save()
        return Response(BulletinPaieSerializer(bulletin).data)

    @action(detail=False, methods=['get'])
    def par_periode(self, request):
        """Bulletins d'une période donnée."""
        periode_id = request.query_params.get('periode_id')
        qs = BulletinPaie.objects.all()
        if periode_id:
            qs = qs.filter(periode_id=periode_id)
        serializer = BulletinPaieListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_employe(self, request):
        """Bulletins d'un employé donné."""
        employe_id = request.query_params.get('employe_id')
        qs = BulletinPaie.objects.all()
        if employe_id:
            qs = qs.filter(employe_id=employe_id)
        serializer = BulletinPaieListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """Bulletins en attente de paiement."""
        qs = BulletinPaie.objects.filter(
            statut__in=['calcule', 'controle', 'valide', 'en_attente_paiement']
        )
        serializer = BulletinPaieListSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# LIGNE BULLETIN
# ============================================================

class LigneBulletinViewset(viewsets.ModelViewSet):
    """CRUD Lignes de bulletin."""
    queryset = LigneBulletin.objects.select_related('bulletin').all()
    serializer_class = LigneBulletinSerializer
    pagination_class = StandardPagination
    filterset_fields = ['bulletin', 'type']
    ordering_fields = ['type', 'ordre']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        return [CanViewPaie()]


# ============================================================
# PRIME
# ============================================================

class PrimeViewset(viewsets.ModelViewSet):
    """CRUD Primes & Indemnités."""
    queryset = Prime.objects.all()
    serializer_class = PrimeSerializer
    pagination_class = StandardPagination
    search_fields = ['code', 'nom']
    filterset_fields = ['type', 'actif', 'imposable']
    ordering_fields = ['nom', 'montant_fixe']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        return [CanViewPaie()]


# ============================================================
# RETENUE
# ============================================================

class RetenueViewset(viewsets.ModelViewSet):
    """CRUD Retenues."""
    queryset = Retenue.objects.all()
    serializer_class = RetenueSerializer
    pagination_class = StandardPagination
    search_fields = ['code', 'nom']
    filterset_fields = ['type', 'actif']
    ordering_fields = ['nom', 'pourcentage']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        return [CanViewPaie()]


# ============================================================
# AVANCE SUR SALAIRE
# ============================================================

class AvanceSalaireViewset(viewsets.ModelViewSet):
    """CRUD Avances sur salaire."""
    queryset = AvanceSalaire.objects.select_related(
        'employe', 'validee_par').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'employe__nom', 'employe__prenom']
    filterset_fields = ['statut', 'employe',
                        'mois_deduction', 'annee_deduction']
    ordering_fields = ['date_demande', 'montant']

    def get_serializer_class(self):
        if self.action == 'list':
            return AvanceSalaireListSerializer
        return AvanceSalaireSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        if self.action in ['valider', 'refuser', 'marquer_payee']:
            return [CanValidatePaie()]
        return [CanViewPaie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide une avance."""
        avance = self.get_object()
        if avance.statut != 'demandee':
            return Response(
                {"error": "Cette avance a déjà été traitée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        avance.statut = 'validee'
        avance.validee_par = request.user
        avance.date_validation = timezone.now()
        avance.save()
        return Response(AvanceSalaireSerializer(avance).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """Refuse une avance."""
        avance = self.get_object()
        if avance.statut != 'demandee':
            return Response(
                {"error": "Cette avance a déjà été traitée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        avance.statut = 'refusee'
        avance.validee_par = request.user
        avance.date_validation = timezone.now()
        avance.save()
        return Response(AvanceSalaireSerializer(avance).data)

    @action(detail=True, methods=['post'])
    def marquer_payee(self, request, pk=None):
        """Marque une avance comme payée."""
        avance = self.get_object()
        avance.statut = 'payee'
        avance.payee = True
        avance.date_paiement = date.today()
        avance.save()
        return Response(AvanceSalaireSerializer(avance).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """Avances en attente de validation."""
        qs = AvanceSalaire.objects.filter(statut='demandee')
        serializer = AvanceSalaireListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques avances."""
        qs = AvanceSalaire.objects.all()
        data = {
            'total': qs.count(),
            'demandees': qs.filter(statut='demandee').count(),
            'validees': qs.filter(statut='validee').count(),
            'payees': qs.filter(statut='payee').count(),
            'montant_total': qs.filter(statut='payee').aggregate(t=Sum('montant'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# FICHE DE PAIE
# ============================================================

class FichePaieViewset(viewsets.ModelViewSet):
    """CRUD Fiches de paie."""
    queryset = FichePaie.objects.select_related('employe', 'bulletin').all()
    serializer_class = FichePaieSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'annee', 'mois']
    ordering_fields = ['-annee', '-mois']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanPreparePaie()]
        return [CanViewPaie()]

    @action(detail=False, methods=['get'])
    def par_employe(self, request):
        """Fiches de paie d'un employé."""
        employe_id = request.query_params.get('employe_id')
        qs = FichePaie.objects.all()
        if employe_id:
            qs = qs.filter(employe_id=employe_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
