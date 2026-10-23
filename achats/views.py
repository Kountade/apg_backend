from django.shortcuts import render

# Create your views here.
# achats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination

from .models import (
    Fournisseur, EvaluationFournisseur,
    DemandeAchat, LigneDemandeAchat,
    DevisFournisseur, LigneDevisFournisseur,
    BonCommande, LigneBonCommande,
    Reception, LigneReception,
    FactureFournisseur, PaiementFournisseur,
)
from .serializers import (
    FournisseurSerializer, FournisseurListSerializer,
    EvaluationFournisseurSerializer,
    DemandeAchatSerializer, DemandeAchatListSerializer,
    LigneDemandeAchatSerializer,
    DevisFournisseurSerializer, DevisFournisseurListSerializer,
    LigneDevisFournisseurSerializer,
    BonCommandeSerializer, BonCommandeListSerializer,
    LigneBonCommandeSerializer,
    ReceptionSerializer, ReceptionListSerializer,
    LigneReceptionSerializer,
    FactureFournisseurSerializer, FactureFournisseurListSerializer,
    PaiementFournisseurSerializer, PaiementFournisseurListSerializer,
)


# ============================================================
# FOURNISSEUR
# ============================================================

class FournisseurViewset(viewsets.ModelViewSet):
    """CRUD Fournisseurs."""
    queryset = Fournisseur.objects.filter(is_deleted=False)
    pagination_class = StandardPagination
    search_fields = ['code', 'nom', 'sigle', 'telephone', 'email', 'ville']
    filterset_fields = ['type', 'statut']
    ordering_fields = ['nom', 'code', 'note_moyenne']

    def get_serializer_class(self):
        if self.action == 'list':
            return FournisseurListSerializer
        return FournisseurSerializer

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
        return Response({'code': Fournisseur.proposer_code()})

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Fournisseur.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'par_type': list(qs.values('type').annotate(total=Count('id')).order_by('-total')),
            'par_statut': list(qs.values('statut').annotate(total=Count('id')).order_by('-total')),
            'note_moyenne_globale': qs.aggregate(moy=Sum('note_moyenne'))['moy'] or 0,
        }
        return Response(data)


# ============================================================
# ÉVALUATION FOURNISSEUR
# ============================================================

class EvaluationFournisseurViewset(viewsets.ModelViewSet):
    """CRUD Évaluations fournisseurs."""
    queryset = EvaluationFournisseur.objects.select_related('fournisseur', 'evaluateur').all()
    serializer_class = EvaluationFournisseurSerializer
    pagination_class = StandardPagination
    search_fields = ['fournisseur__nom', 'periode', 'commentaire']
    filterset_fields = ['fournisseur']
    ordering_fields = ['date_evaluation', 'note_globale']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            evaluateur=self.request.user,
        )


# ============================================================
# DEMANDE D'ACHAT
# ============================================================

class DemandeAchatViewset(viewsets.ModelViewSet):
    """CRUD Demandes d'achat."""
    queryset = DemandeAchat.objects.select_related('demandeur', 'validee_par').prefetch_related('lignes').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'objet', 'service', 'demandeur__nom']
    filterset_fields = ['statut', 'urgence', 'demandeur', 'service']
    ordering_fields = ['date_demande', 'numero', 'urgence']

    def get_serializer_class(self):
        if self.action == 'list':
            return DemandeAchatListSerializer
        return DemandeAchatSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        return Response({'numero': DemandeAchat.generate_numero_class() if hasattr(DemandeAchat, 'generate_numero_class') else ''})

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        demande = self.get_object()
        if demande.statut != 'brouillon':
            return Response(
                {"error": "Seules les demandes en brouillon peuvent être soumises."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        demande.statut = 'soumise'
        demande.save()
        return Response(DemandeAchatSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        demande = self.get_object()
        if demande.statut not in ['soumise', 'brouillon']:
            return Response(
                {"error": "Cette demande ne peut plus être validée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        demande.statut = 'validee'
        demande.validee_par = request.user
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire_validation', '')
        demande.save()
        return Response(DemandeAchatSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        demande = self.get_object()
        if demande.statut in ['validee', 'convertie', 'annulee']:
            return Response(
                {"error": "Cette demande ne peut plus être refusée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        demande.statut = 'refusee'
        demande.validee_par = request.user
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire_validation', '')
        demande.save()
        return Response(DemandeAchatSerializer(demande).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = DemandeAchat.objects.filter(statut='soumise').select_related('demandeur')
        serializer = DemandeAchatListSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# LIGNE DEMANDE ACHAT
# ============================================================

class LigneDemandeAchatViewset(viewsets.ModelViewSet):
    queryset = LigneDemandeAchat.objects.select_related('demande', 'article_stock').all()
    serializer_class = LigneDemandeAchatSerializer
    pagination_class = StandardPagination
    filterset_fields = ['demande', 'article_stock']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# DEVIS FOURNISSEUR
# ============================================================

class DevisFournisseurViewset(viewsets.ModelViewSet):
    """CRUD Devis fournisseurs."""
    queryset = DevisFournisseur.objects.select_related('fournisseur', 'demande_achat').prefetch_related('lignes').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'numero_devis_fournisseur', 'objet', 'fournisseur__nom']
    filterset_fields = ['statut', 'fournisseur', 'demande_achat']
    ordering_fields = ['date_devis', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return DevisFournisseurListSerializer
        return DevisFournisseurSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def accepter(self, request, pk=None):
        devis = self.get_object()
        if devis.statut not in ['recu', 'en_etude']:
            return Response({"error": "Ce devis ne peut plus être accepté."}, status=400)
        devis.statut = 'accepte'
        devis.save()
        return Response(DevisFournisseurSerializer(devis).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        devis = self.get_object()
        devis.statut = 'refuse'
        devis.save()
        return Response(DevisFournisseurSerializer(devis).data)


class LigneDevisFournisseurViewset(viewsets.ModelViewSet):
    queryset = LigneDevisFournisseur.objects.select_related('devis').all()
    serializer_class = LigneDevisFournisseurSerializer
    pagination_class = StandardPagination
    filterset_fields = ['devis']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# BON DE COMMANDE
# ============================================================

class BonCommandeViewset(viewsets.ModelViewSet):
    """CRUD Bons de commande."""
    queryset = BonCommande.objects.select_related(
        'fournisseur', 'demande_achat', 'devis_fournisseur', 'valide_par'
    ).prefetch_related('lignes').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'objet', 'fournisseur__nom']
    filterset_fields = ['statut', 'fournisseur', 'demande_achat']
    ordering_fields = ['date_commande', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return BonCommandeListSerializer
        return BonCommandeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def envoyer(self, request, pk=None):
        bc = self.get_object()
        if bc.statut != 'brouillon':
            return Response({"error": "Seuls les brouillons peuvent être envoyés."}, status=400)
        bc.statut = 'envoye'
        bc.save()
        return Response(BonCommandeSerializer(bc).data)

    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        bc = self.get_object()
        bc.statut = 'confirme'
        bc.save()
        return Response(BonCommandeSerializer(bc).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        bc = self.get_object()
        if bc.statut in ['recu']:
            return Response({"error": "Un bon de commande reçu ne peut être annulé."}, status=400)
        bc.statut = 'annule'
        bc.save()
        return Response(BonCommandeSerializer(bc).data)


class LigneBonCommandeViewset(viewsets.ModelViewSet):
    queryset = LigneBonCommande.objects.select_related('bon_commande', 'article_stock').all()
    serializer_class = LigneBonCommandeSerializer
    pagination_class = StandardPagination
    filterset_fields = ['bon_commande', 'article_stock']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# RÉCEPTION
# ============================================================

class ReceptionViewset(viewsets.ModelViewSet):
    """CRUD Réceptions."""
    queryset = Reception.objects.select_related(
        'bon_commande', 'fournisseur', 'magasin_destination', 'controle_par'
    ).prefetch_related('lignes').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'numero_bon_livraison', 'bon_commande__numero', 'fournisseur__nom']
    filterset_fields = ['statut', 'fournisseur', 'bon_commande', 'magasin_destination']
    ordering_fields = ['date_reception', 'numero']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReceptionListSerializer
        return ReceptionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def controler(self, request, pk=None):
        reception = self.get_object()
        reception.statut = 'controlee'
        reception.controle_par = request.user
        reception.date_controle = timezone.now()
        reception.observations = request.data.get('observations', reception.observations)
        reception.save()
        return Response(ReceptionSerializer(reception).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """
        Valide la réception : met à jour les stocks et les quantités reçues
        sur les lignes de bon de commande, puis crée les mouvements de stock.
        """
        from stocks.models import MouvementStock, Article

        reception = self.get_object()
        if reception.statut == 'validee':
            return Response({"error": "Cette réception est déjà validée."}, status=400)

        # Créer les mouvements de stock pour chaque ligne acceptée
        for ligne in reception.lignes.all():
            ligne_bc = ligne.ligne_bon_commande

            # Mettre à jour la quantité reçue sur la ligne de bon de commande
            ligne_bc.quantite_recue = float(ligne_bc.quantite_recue) + float(ligne.quantite_acceptee)
            ligne_bc.save(update_fields=['quantite_recue'])

            # Si un article stock est lié et quantité acceptée > 0 → mouvement entrée
            if ligne_bc.article_stock and float(ligne.quantite_acceptee) > 0:
                MouvementStock.objects.create(
                    type='entree',
                    motif='achat',
                    article=ligne_bc.article_stock,
                    quantite=ligne.quantite_acceptee,
                    magasin_destination=reception.magasin_destination,
                    fournisseur_nom=reception.fournisseur.nom,
                    reference=reception.numero,
                    observation=f"Réception {reception.numero} — BC {reception.bon_commande.numero}",
                    created_by=request.user,
                )

        # Mettre à jour le statut de la réception
        reception.statut = 'validee'
        reception.save()

        # Mettre à jour le statut du bon de commande
        bc = reception.bon_commande
        lignes_bc = bc.lignes.all()
        toutes_recues = all(
            float(l.quantite_recue) >= float(l.quantite) for l in lignes_bc
        )
        if toutes_recues:
            bc.statut = 'recu'
            bc.date_livraison_reelle = date.today()
        elif any(float(l.quantite_recue) > 0 for l in lignes_bc):
            bc.statut = 'partiellement_recu'
        bc.save()

        return Response(ReceptionSerializer(reception).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        reception = self.get_object()
        reception.statut = 'refusee'
        reception.observations = request.data.get('observations', '')
        reception.save()
        return Response(ReceptionSerializer(reception).data)


class LigneReceptionViewset(viewsets.ModelViewSet):
    queryset = LigneReception.objects.select_related('reception', 'ligne_bon_commande').all()
    serializer_class = LigneReceptionSerializer
    pagination_class = StandardPagination
    filterset_fields = ['reception', 'ligne_bon_commande']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# FACTURE FOURNISSEUR
# ============================================================

class FactureFournisseurViewset(viewsets.ModelViewSet):
    """CRUD Factures fournisseurs."""
    queryset = FactureFournisseur.objects.select_related(
        'fournisseur', 'bon_commande', 'reception', 'validee_par'
    ).prefetch_related('paiements').all()
    pagination_class = StandardPagination
    search_fields = ['numero_interne', 'numero_facture_fournisseur', 'objet', 'fournisseur__nom']
    filterset_fields = ['statut', 'fournisseur', 'bon_commande']
    ordering_fields = ['date_facture', 'date_echeance', 'numero_interne']

    def get_serializer_class(self):
        if self.action == 'list':
            return FactureFournisseurListSerializer
        return FactureFournisseurSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        facture = self.get_object()
        facture.statut = 'validee'
        facture.validee_par = request.user
        facture.date_validation = timezone.now()
        facture.save()
        return Response(FactureFournisseurSerializer(facture).data)

    @action(detail=False, methods=['get'])
    def impayees(self, request):
        qs = FactureFournisseur.objects.filter(
            statut__in=['recue', 'controlee', 'validee', 'partiellement_payee']
        ).select_related('fournisseur')
        serializer = FactureFournisseurListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def echues(self, request):
        today = date.today()
        qs = FactureFournisseur.objects.filter(
            date_echeance__lt=today,
            statut__in=['recue', 'controlee', 'validee', 'partiellement_payee'],
        ).select_related('fournisseur')
        serializer = FactureFournisseurListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = FactureFournisseur.objects.all()
        data = {
            'total': qs.count(),
            'montant_total_ttc': qs.aggregate(t=Sum('montant_ttc'))['t'] or 0,
            'montant_total_paye': qs.aggregate(t=Sum('montant_paye'))['t'] or 0,
            'par_statut': list(qs.values('statut').annotate(total=Count('id'))),
        }
        return Response(data)


# ============================================================
# PAIEMENT FOURNISSEUR
# ============================================================

class PaiementFournisseurViewset(viewsets.ModelViewSet):
    """CRUD Paiements fournisseurs."""
    queryset = PaiementFournisseur.objects.select_related('facture', 'fournisseur').all()
    pagination_class = StandardPagination
    search_fields = ['numero', 'reference', 'fournisseur__nom', 'facture__numero_interne']
    filterset_fields = ['statut', 'mode', 'fournisseur', 'facture']
    ordering_fields = ['date_paiement', 'numero', 'montant']

    def get_serializer_class(self):
        if self.action == 'list':
            return PaiementFournisseurListSerializer
        return PaiementFournisseurSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)