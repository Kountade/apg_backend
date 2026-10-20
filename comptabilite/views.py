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
    Avoir,
    PaiementClient,
    Litige,
    EcritureComptable, LigneEcriture,
    Lettrage, DeclarationFiscale,
    ClotureComptable,  # ✅ NOUVEAU
)
from .serializers import (
    CompteComptableSerializer, CompteComptableListSerializer,
    JournalSerializer, JournalListSerializer,
    FactureSerializer, FactureListSerializer, LigneFactureSerializer,
    DevisSerializer, DevisListSerializer, LigneDevisSerializer,
    AvoirSerializer,
    PaiementClientSerializer,
    LitigeSerializer,
    EcritureComptableSerializer, EcritureComptableListSerializer,
    LigneEcritureSerializer,
    LettrageSerializer,
    DeclarationFiscaleSerializer, DeclarationFiscaleListSerializer,
    ClotureComptableSerializer, ClotureComptableListSerializer,  # ✅ NOUVEAU
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
                           'emettre', 'valider', 'annuler',
                           'enregistrer_paiement']:
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

    @action(detail=False, methods=['get'])
    def creances(self, request):
        """Créances clients : factures avec solde restant > 0."""
        qs = Facture.objects.filter(
            statut__in=['emise', 'envoyee',
                        'partiellement_payee', 'en_retard']
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
        """Valider une facture (émise → envoyée)."""
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
        for ligne in devis.lignes.all():
            LigneFacture.objects.create(
                facture=facture,
                designation=ligne.designation,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
            )
        devis.facture_generee = facture
        devis.statut = 'transforme'
        devis.save()
        return Response({
            'message': 'Devis transformé en facture avec succès.',
            'facture': FactureSerializer(facture).data,
        })


# ============================================================
# AVOIR
# ============================================================

class AvoirViewset(viewsets.ModelViewSet):
    """CRUD Avoirs clients."""
    queryset = Avoir.objects.select_related(
        'client', 'facture_origine').all()
    serializer_class = AvoirSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom', 'objet', 'motif']
    filterset_fields = ['statut', 'client']
    ordering_fields = ['date_avoir', 'montant_ttc']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ============================================================
# PAIEMENT CLIENT
# ============================================================

class PaiementClientViewset(viewsets.ModelViewSet):
    """CRUD Paiements clients."""
    queryset = PaiementClient.objects.select_related(
        'client', 'facture').all()
    serializer_class = PaiementClientSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom', 'facture__numero', 'reference']
    filterset_fields = ['statut', 'mode', 'client', 'facture']
    ordering_fields = ['date_paiement', 'montant']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ============================================================
# LITIGE
# ============================================================

class LitigeViewset(viewsets.ModelViewSet):
    """CRUD Litiges."""
    queryset = Litige.objects.select_related(
        'client', 'facture').all()
    serializer_class = LitigeSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'client__nom', 'facture__numero', 'motif']
    filterset_fields = ['statut', 'client']
    ordering_fields = ['date_ouverture']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        """Marquer un litige comme résolu."""
        litige = self.get_object()
        litige.statut = 'resolu'
        litige.date_resolution = date.today()
        litige.resolution = request.data.get('resolution', '')
        litige.save()
        return Response(LitigeSerializer(litige).data)


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

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Balance générale : totaux débit/crédit par compte."""
        comptes = CompteComptable.objects.filter(actif=True)
        data = []
        for compte in comptes:
            lignes = compte.lignes_ecriture.filter(ecriture__statut='validee')
            debit = lignes.aggregate(t=Sum('debit'))['t'] or 0
            credit = lignes.aggregate(t=Sum('credit'))['t'] or 0
            if debit or credit:
                data.append({
                    'compte_id': compte.id,
                    'numero': compte.numero,
                    'libelle': compte.libelle,
                    'debit': float(debit),
                    'credit': float(credit),
                    'solde': float(debit) - float(credit),
                })
        return Response(data)


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


# ============================================================
# CLÔTURE COMPTABLE ✅ NOUVEAU
# ============================================================

class ClotureComptableViewset(viewsets.ModelViewSet):
    """CRUD Clôtures comptables + workflow."""
    queryset = ClotureComptable.objects.select_related(
        'cloture_par', 'reouverte_par'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'notes']
    filterset_fields = ['statut', 'type', 'annee', 'mois']
    ordering_fields = ['-annee', '-mois', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClotureComptableListSerializer
        return ClotureComptableSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'calculer', 'valider', 'reouvrir']:
            return [CanEditComptabilite()]
        return [CanViewComptabilite()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        """Retourne le prochain numéro de clôture proposé."""
        return Response({'numero': ClotureComptable.proposer_numero()})

    @action(detail=True, methods=['post'])
    def calculer(self, request, pk=None):
        """Calcule les totaux depuis les écritures."""
        cloture = self.get_object()
        if cloture.statut == 'validee':
            return Response(
                {"error": "Impossible de recalculer une clôture validée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cloture.calculer_totaux()
        cloture.statut = 'en_cours'
        cloture.save()
        return Response(ClotureComptableSerializer(cloture).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide définitivement une clôture."""
        cloture = self.get_object()
        if cloture.statut == 'validee':
            return Response(
                {"error": "Cette clôture est déjà validée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cloture.statut = 'validee'
        cloture.cloture_par = request.user
        cloture.date_cloture = timezone.now()
        cloture.save()
        return Response(ClotureComptableSerializer(cloture).data)

    @action(detail=True, methods=['post'])
    def reouvrir(self, request, pk=None):
        """Réouvre une clôture validée."""
        cloture = self.get_object()
        if cloture.statut != 'validee':
            return Response(
                {"error": "Seule une clôture validée peut être réouverte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cloture.statut = 'reouverte'
        cloture.reouverte_par = request.user
        cloture.date_reouverture = timezone.now()
        cloture.save()
        return Response(ClotureComptableSerializer(cloture).data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des clôtures."""
        qs = ClotureComptable.objects.all()
        data = {
            'total': qs.count(),
            'brouillon': qs.filter(statut='brouillon').count(),
            'en_cours': qs.filter(statut='en_cours').count(),
            'validees': qs.filter(statut='validee').count(),
            'reouvertes': qs.filter(statut='reouverte').count(),
        }
        return Response(data)
