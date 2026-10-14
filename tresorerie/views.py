from django.shortcuts import render

# Create your views here.
# tresorerie/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta

from core.permissions import (
    CanViewTresorerie, CanEditTresorerie, CanValidatePaiements,
    IsPDG, IsComptable,
)
from core.pagination import StandardPagination

from .models import (
    Caisse, CompteBancaire, MouvementTresorerie,
    Encaissement, Decaissement, MouvementCaisse,
    PrevisionTresorerie, AlerteTresorerie, RapprochementBancaire
)
# Ajouter dans les imports


from .serializers import (
    CaisseSerializer, CaisseListSerializer,
    CompteBancaireSerializer, CompteBancaireListSerializer,
    MouvementTresorerieSerializer,
    EncaissementSerializer, EncaissementListSerializer,
    DecaissementSerializer, DecaissementListSerializer,
    MouvementCaisseSerializer,
    PrevisionTresorerieSerializer,
    AlerteTresorerieSerializer,
    RapprochementBancaireSerializer
)


# ============================================================
# CAISSE
# ============================================================

class CaisseViewset(viewsets.ModelViewSet):
    """CRUD Caisses."""
    queryset = Caisse.objects.select_related('responsable').all()
    pagination_class = StandardPagination
    search_fields = ['code', 'nom']
    filterset_fields = ['actif', 'devise']
    ordering_fields = ['code', 'nom', 'solde_theorique']

    def get_serializer_class(self):
        if self.action == 'list':
            return CaisseListSerializer
        return CaisseSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'recalculer_solde', 'ajuster_solde']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def recalculer_solde(self, request, pk=None):
        """Recalcule le solde théorique."""
        caisse = self.get_object()
        caisse.calculer_solde()
        return Response(CaisseSerializer(caisse).data)

    @action(detail=True, methods=['post'])
    def ajuster_solde(self, request, pk=None):
        """Ajuste le solde physique."""
        caisse = self.get_object()
        solde_physique = request.data.get('solde_physique')
        if solde_physique is not None:
            caisse.solde_physique = solde_physique
            caisse.save()
        return Response(CaisseSerializer(caisse).data)


# ============================================================
# COMPTE BANCAIRE
# ============================================================

class CompteBancaireViewset(viewsets.ModelViewSet):
    """CRUD Comptes bancaires."""
    queryset = CompteBancaire.objects.all()
    pagination_class = StandardPagination
    search_fields = ['code', 'nom', 'banque', 'numero_compte']
    filterset_fields = ['type', 'actif']
    ordering_fields = ['code', 'nom', 'solde_actuel']

    def get_serializer_class(self):
        if self.action == 'list':
            return CompteBancaireListSerializer
        return CompteBancaireSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# MOUVEMENT DE TRÉSORERIE
# ============================================================

class MouvementTresorerieViewset(viewsets.ModelViewSet):
    """CRUD Mouvements de trésorerie."""
    queryset = MouvementTresorerie.objects.select_related(
        'caisse', 'compte_bancaire').all()
    serializer_class = MouvementTresorerieSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'origine', 'reference']
    filterset_fields = ['type', 'caisse', 'compte_bancaire']
    ordering_fields = ['date_mouvement', 'montant']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# ENCAISSEMENT
# ============================================================

class EncaissementViewset(viewsets.ModelViewSet):
    """CRUD Encaissements."""
    queryset = Encaissement.objects.select_related(
        'client', 'caisse', 'compte_bancaire', 'valide_par').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'origine', 'reference', 'facture_reference']
    filterset_fields = ['type', 'statut',
                        'client', 'caisse', 'compte_bancaire']
    ordering_fields = ['date_encaissement', 'montant', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return EncaissementListSerializer
        return EncaissementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'valider', 'annuler']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        numero = Encaissement.proposer_numero()
        return Response({'numero': numero})

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider un encaissement."""
        encaissement = self.get_object()
        if encaissement.statut != 'en_attente':
            return Response(
                {"error": "Cet encaissement a déjà été traité."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        encaissement.statut = 'valide'
        encaissement.valide_par = request.user
        encaissement.date_validation = timezone.now()
        encaissement.save()

        # Créer un mouvement dans la caisse
        if encaissement.caisse:
            MouvementCaisse.objects.create(
                caisse=encaissement.caisse,
                type='entree',
                montant=encaissement.montant,
                libelle=f"Encaissement {encaissement.numero}",
                encaissement=encaissement,
                created_by=request.user,
            )
            encaissement.caisse.calculer_solde()

        return Response(EncaissementSerializer(encaissement).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler un encaissement."""
        encaissement = self.get_object()
        encaissement.statut = 'annule'
        encaissement.save()
        return Response(EncaissementSerializer(encaissement).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = Encaissement.objects.filter(
            statut='en_attente').select_related('client')
        serializer = EncaissementListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Encaissement.objects.all()
        data = {
            'total': qs.count(),
            'valides': qs.filter(statut='valide').count(),
            'en_attente': qs.filter(statut='en_attente').count(),
            'montant_total': qs.filter(statut='valide').aggregate(t=Sum('montant'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# DÉCAISSEMENT
# ============================================================

class DecaissementViewset(viewsets.ModelViewSet):
    """CRUD Décaissements."""
    queryset = Decaissement.objects.select_related(
        'caisse', 'compte_bancaire',
        'demande_par', 'valide_par', 'paye_par'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'beneficiaire', 'motif', 'reference']
    filterset_fields = ['type', 'statut', 'caisse', 'compte_bancaire']
    ordering_fields = ['date_demande', 'date_paiement', 'montant', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return DecaissementListSerializer
        return DecaissementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditTresorerie()]
        if self.action in ['valider', 'refuser', 'marquer_paye']:
            return [CanValidatePaiements()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            demande_par=self.request.user,
        )

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        numero = Decaissement.proposer_numero()
        return Response({'numero': numero})

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider un décaissement."""
        decaissement = self.get_object()
        if decaissement.statut not in ['en_attente']:
            return Response(
                {"error": "Ce décaissement ne peut pas être validé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        decaissement.statut = 'valide'
        decaissement.valide_par = request.user
        decaissement.save()
        return Response(DecaissementSerializer(decaissement).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """Refuser un décaissement."""
        decaissement = self.get_object()
        decaissement.statut = 'refuse'
        decaissement.save()
        return Response(DecaissementSerializer(decaissement).data)

    @action(detail=True, methods=['post'])
    def marquer_paye(self, request, pk=None):
        """Marquer comme payé."""
        decaissement = self.get_object()
        if decaissement.statut not in ['valide', 'en_attente']:
            return Response(
                {"error": "Ce décaissement ne peut pas être marqué payé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        decaissement.statut = 'paye'
        decaissement.date_paiement = date.today()
        decaissement.paye_par = request.user
        decaissement.save()

        # Créer un mouvement dans la caisse
        if decaissement.caisse:
            MouvementCaisse.objects.create(
                caisse=decaissement.caisse,
                type='sortie',
                montant=decaissement.montant,
                libelle=f"Décaissement {decaissement.numero}",
                decaissement=decaissement,
                created_by=request.user,
            )
            decaissement.caisse.calculer_solde()

        return Response(DecaissementSerializer(decaissement).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler un décaissement."""
        decaissement = self.get_object()
        decaissement.statut = 'annule'
        decaissement.save()
        return Response(DecaissementSerializer(decaissement).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = Decaissement.objects.filter(statut='en_attente')
        serializer = DecaissementListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Decaissement.objects.all()
        data = {
            'total': qs.count(),
            'en_attente': qs.filter(statut='en_attente').count(),
            'valides': qs.filter(statut='valide').count(),
            'payes': qs.filter(statut='paye').count(),
            'montant_paye': qs.filter(statut='paye').aggregate(t=Sum('montant'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# MOUVEMENT DE CAISSE
# ============================================================

class MouvementCaisseViewset(viewsets.ModelViewSet):
    """CRUD Mouvements de caisse."""
    queryset = MouvementCaisse.objects.select_related('caisse').all()
    serializer_class = MouvementCaisseSerializer
    pagination_class = StandardPagination
    filterset_fields = ['caisse', 'type']
    ordering_fields = ['date_mouvement', 'montant']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# PRÉVISION DE TRÉSORERIE
# ============================================================

class PrevisionTresorerieViewset(viewsets.ModelViewSet):
    """CRUD Prévisions de trésorerie."""
    queryset = PrevisionTresorerie.objects.all()
    serializer_class = PrevisionTresorerieSerializer
    pagination_class = StandardPagination
    filterset_fields = ['type', 'realise']
    ordering_fields = ['date_prevue', 'montant']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# ALERTE TRÉSORERIE
# ============================================================

class AlerteTresorerieViewset(viewsets.ModelViewSet):
    """CRUD Alertes trésorerie."""
    queryset = AlerteTresorerie.objects.all()
    serializer_class = AlerteTresorerieSerializer
    pagination_class = StandardPagination
    filterset_fields = ['niveau', 'resolue', 'caisse', 'compte_bancaire']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'resoudre']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        alerte = self.get_object()
        alerte.resolue = True
        alerte.date_resolution = timezone.now()
        alerte.save()
        return Response(AlerteTresorerieSerializer(alerte).data)


class RapprochementBancaireViewset(viewsets.ModelViewSet):
    """CRUD Rapprochements bancaires."""
    queryset = RapprochementBancaire.objects.select_related(
        'compte_bancaire', 'cloture_par'
    ).all()
    serializer_class = RapprochementBancaireSerializer
    pagination_class = StandardPagination
    search_fields = ['notes']
    filterset_fields = ['statut', 'compte_bancaire', 'mois', 'annee']
    ordering_fields = ['annee', 'mois']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'cloturer']:
            return [CanEditTresorerie()]
        return [CanViewTresorerie()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        rapprochement = self.get_object()
        rapprochement.statut = 'cloture'
        rapprochement.cloture_par = request.user
        rapprochement.date_cloture = timezone.now()
        rapprochement.save()
        return Response(RapprochementBancaireSerializer(rapprochement).data)
