from django.shortcuts import render

# Create your views here.
# comptabilite/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta

from core.permissions import (
    CanViewComptabilite, CanEditComptabilite,
    CanValidateFactures,
    IsPDG, IsComptable,
)
from core.pagination import StandardPagination

from .models import (
    CompteComptable, Journal,
    Facture, LigneFacture,
    Devis, LigneDevis,
    EcritureComptable, LigneEcriture,
    Lettrage, DeclarationFiscale,
)
from .serializers import (
    CompteComptableSerializer, CompteComptableListSerializer,
    JournalSerializer, JournalListSerializer,
    FactureSerializer, FactureListSerializer, LigneFactureSerializer,
    DevisSerializer, DevisListSerializer, LigneDevisSerializer,
    EcritureComptableSerializer, EcritureComptableListSerializer,
    LigneEcritureSerializer,
    LettrageSerializer,
    DeclarationFiscaleSerializer, DeclarationFiscaleListSerializer,
)


# ============================================================
# COMPTE COMPTABLE
# ============================================================

class CompteComptableViewset(viewsets.ModelViewSet):
    """CRUD Plan comptable."""
    queryset = CompteComptable.objects.all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'libelle']
    filterset_fields = ['classe', 'type_compte', 'actif']
    ordering_fields = ['numero', 'libelle']

    def get_serializer_class(self):
        if self.action == 'list':
            return CompteComptableListSerializer
        return CompteComptableSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def par_classe(self, request):
        """Comptes groupés par classe."""
        data = {}
        for classe, label in CompteComptable.CLASSE_CHOICES:
            comptes = CompteComptable.objects.filter(classe=classe, actif=True)
            data[classe] = {
                'label': label,
                'comptes': CompteComptableListSerializer(comptes, many=True).data,
            }
        return Response(data)


# ============================================================
# JOURNAL
# ============================================================

class JournalViewset(viewsets.ModelViewSet):
    """CRUD Journaux comptables."""
    queryset = Journal.objects.all()
    pagination_class = StandardPagination
    search_fields = ['code', 'libelle']
    filterset_fields = ['type', 'actif']
    ordering_fields = ['code', 'libelle']

    def get_serializer_class(self):
        if self.action == 'list':
            return JournalListSerializer
        return JournalSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# FACTURE
# ============================================================

class FactureViewset(viewsets.ModelViewSet):
    """CRUD Factures clients."""
    queryset = Facture.objects.select_related(
        'client', 'contrat', 'emise_par').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom', 'objet']
    filterset_fields = ['statut', 'type', 'client']
    ordering_fields = ['date_emission', 'date_echeance', 'montant_ttc']

    def get_serializer_class(self):
        if self.action == 'list':
            return FactureListSerializer
        return FactureSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'emettre', 'valider', 'annuler']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            emise_par=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro de facture proposé."""
        numero = Facture.proposer_numero()
        return Response({'numero': numero})

    @action(detail=False, methods=['get'])
    def impayees(self, request):
        """Factures impayées (non payées et non annulées)."""
        qs = Facture.objects.filter(
            statut__in=['emise', 'envoyee',
                        'partiellement_payee', 'en_retard', 'litige']
        ).select_related('client')
        serializer = FactureListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def echues(self, request):
        """Factures échues (en retard)."""
        qs = Facture.objects.filter(
            statut__in=['emise', 'envoyee',
                        'partiellement_payee', 'en_retard'],
            date_echeance__lt=date.today()
        ).select_related('client')
        serializer = FactureListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def non_echues(self, request):
        """Factures non échues."""
        qs = Facture.objects.filter(
            statut__in=['emise', 'envoyee', 'partiellement_payee'],
            date_echeance__gte=date.today()
        ).select_related('client')
        serializer = FactureListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def emettre(self, request, pk=None):
        """Émettre une facture (brouillon → émise)."""
        facture = self.get_object()
        if facture.statut != 'brouillon':
            return Response(
                {"error": "Seule une facture en brouillon peut être émise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facture.statut = 'emise'
        facture.save()
        return Response(FactureSerializer(facture).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider une facture."""
        facture = self.get_object()
        facture.statut = 'envoyee'
        facture.save()
        return Response(FactureSerializer(facture).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler une facture."""
        facture = self.get_object()
        if facture.statut == 'payee':
            return Response(
                {"error": "Impossible d'annuler une facture déjà payée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facture.statut = 'annulee'
        facture.save()
        return Response(FactureSerializer(facture).data)

    @action(detail=True, methods=['post'])
    def enregistrer_paiement(self, request, pk=None):
        """Enregistrer un paiement sur une facture."""
        facture = self.get_object()
        montant = request.data.get('montant')
        if not montant:
            return Response(
                {"error": "Le montant est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            montant = float(montant)
        except (ValueError, TypeError):
            return Response(
                {"error": "Montant invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facture.montant_paye += montant
        if facture.montant_paye >= facture.montant_ttc:
            facture.statut = 'payee'
        else:
            facture.statut = 'partiellement_payee'
        facture.save()
        return Response(FactureSerializer(facture).data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales factures."""
        qs = Facture.objects.all()
        data = {
            'total': qs.count(),
            'payees': qs.filter(statut='payee').count(),
            'impayees': qs.filter(
                statut__in=['emise', 'envoyee',
                            'partiellement_payee', 'en_retard']
            ).count(),
            'en_retard': qs.filter(
                statut__in=['emise', 'envoyee',
                            'partiellement_payee', 'en_retard'],
                date_echeance__lt=date.today()
            ).count(),
            'montant_total': qs.aggregate(t=Sum('montant_ttc'))['t'] or 0,
            'montant_paye': qs.aggregate(t=Sum('montant_paye'))['t'] or 0,
            'par_statut': list(
                qs.values('statut').annotate(
                    total=Count('id')).order_by('-total')
            ),
        }
        data['montant_impaye'] = float(
            data['montant_total']) - float(data['montant_paye'])
        return Response(data)


# ============================================================
# DEVIS
# ============================================================

class DevisViewset(viewsets.ModelViewSet):
    """CRUD Devis."""
    queryset = Devis.objects.select_related('client', 'facture_generee').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom', 'objet']
    filterset_fields = ['statut', 'client']
    ordering_fields = ['date_emission', 'date_validite', 'montant_ttc']

    def get_serializer_class(self):
        if self.action == 'list':
            return DevisListSerializer
        return DevisSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'transformer_en_facture']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro de devis proposé."""
        numero = Devis.proposer_numero()
        return Response({'numero': numero})

    @action(detail=True, methods=['post'])
    def transformer_en_facture(self, request, pk=None):
        """Transforme un devis accepté en facture."""
        devis = self.get_object()
        if devis.statut != 'accepte':
            return Response(
                {"error": "Seul un devis accepté peut être transformé en facture."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if devis.facture_generee:
            return Response(
                {"error": "Ce devis a déjà été transformé en facture."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Créer la facture
        facture = Facture.objects.create(
            client=devis.client,
            type='definitive',
            date_echeance=date.today() + timedelta(days=30),
            montant_ht=devis.montant_ht,
            taux_tva=devis.taux_tva,
            objet=devis.objet,
            statut='emise',
            emise_par=request.user,
            created_by=request.user,
        )
        # Copier les lignes
        for ligne in devis.lignes.all():
            LigneFacture.objects.create(
                facture=facture,
                designation=ligne.designation,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
            )
        # Mettre à jour le devis
        devis.facture_generee = facture
        devis.statut = 'transforme'
        devis.save()
        return Response({
            'message': 'Devis transformé en facture avec succès.',
            'facture': FactureSerializer(facture).data,
        })


# ============================================================
# ÉCRITURE COMPTABLE
# ============================================================

class EcritureComptableViewset(viewsets.ModelViewSet):
    """CRUD Écritures comptables."""
    queryset = EcritureComptable.objects.select_related(
        'journal', 'validee_par').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'libelle', 'reference']
    filterset_fields = ['journal', 'statut']
    ordering_fields = ['date_ecriture', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return EcritureComptableListSerializer
        return EcritureComptableSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'valider', 'annuler']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider une écriture comptable."""
        ecriture = self.get_object()
        if not ecriture.est_equilibree:
            return Response(
                {"error": "L'écriture n'est pas équilibrée (débit ≠ crédit)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ecriture.statut = 'validee'
        ecriture.validee_par = request.user
        ecriture.date_validation = timezone.now()
        ecriture.save()
        return Response(EcritureComptableSerializer(ecriture).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annuler une écriture comptable."""
        ecriture = self.get_object()
        ecriture.statut = 'annulee'
        ecriture.save()
        return Response(EcritureComptableSerializer(ecriture).data)

    @action(detail=False, methods=['get'])
    def grand_livre(self, request):
        """Grand livre : toutes les lignes d'écriture par compte."""
        compte_id = request.query_params.get('compte')
        qs = LigneEcriture.objects.select_related('ecriture', 'compte')
        if compte_id:
            qs = qs.filter(compte_id=compte_id)
        serializer = LigneEcritureSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# LETTRAGE
# ============================================================

class LettrageViewset(viewsets.ModelViewSet):
    """CRUD Lettrages."""
    queryset = Lettrage.objects.select_related('compte').all()
    serializer_class = LettrageSerializer
    pagination_class = StandardPagination
    search_fields = ['code_lettrage']
    filterset_fields = ['compte']
    ordering_fields = ['date_lettrage']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# DÉCLARATION FISCALE
# ============================================================

class DeclarationFiscaleViewset(viewsets.ModelViewSet):
    """CRUD Déclarations fiscales."""
    queryset = DeclarationFiscale.objects.all()
    pagination_class = StandardPagination
    search_fields = ['periode']
    filterset_fields = ['type', 'statut']
    ordering_fields = ['date_echeance', 'montant']

    def get_serializer_class(self):
        if self.action == 'list':
            return DeclarationFiscaleListSerializer
        return DeclarationFiscaleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
