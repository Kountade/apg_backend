# tresorerie/serializers.py
from rest_framework import serializers
from .models import (
    Caisse, CompteBancaire, MouvementTresorerie,
    Encaissement, Decaissement, MouvementCaisse,
    PrevisionTresorerie, AlerteTresorerie,
)


# ============================================================
# CAISSE
# ============================================================

class CaisseSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.SerializerMethodField(read_only=True)
    difference = serializers.ReadOnlyField()
    nombre_mouvements = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Caisse
        fields = [
            'id', 'code', 'nom',
            'responsable', 'responsable_nom',
            'devise', 'solde_initial', 'solde_theorique', 'solde_physique',
            'difference', 'actif', 'description',
            'nombre_mouvements',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'difference']

    def get_responsable_nom(self, obj):
        return obj.responsable.nom_complet if obj.responsable else None

    def get_nombre_mouvements(self, obj):
        return obj.mouvements.count()


class CaisseListSerializer(serializers.ModelSerializer):
    difference = serializers.ReadOnlyField()

    class Meta:
        model = Caisse
        fields = [
            'id', 'code', 'nom', 'devise',
            'solde_theorique', 'solde_physique', 'difference',
            'actif',
        ]


# ============================================================
# COMPTE BANCAIRE
# ============================================================

class CompteBancaireSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    nombre_mouvements = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompteBancaire
        fields = [
            'id', 'code', 'nom',
            'type', 'type_display',
            'banque', 'numero_compte', 'iban', 'swift', 'titulaire',
            'devise', 'solde_initial', 'solde_actuel',
            'actif', 'notes',
            'nombre_mouvements',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nombre_mouvements(self, obj):
        return obj.mouvements.count()


class CompteBancaireListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = CompteBancaire
        fields = [
            'id', 'code', 'nom', 'type', 'type_display',
            'banque', 'devise', 'solde_actuel', 'actif',
        ]


# ============================================================
# MOUVEMENT DE TRÉSORERIE
# ============================================================

class MouvementTresorerieSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    mode_paiement_display = serializers.CharField(
        source='get_mode_paiement_display', read_only=True)
    caisse_nom = serializers.SerializerMethodField(read_only=True)
    compte_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MouvementTresorerie
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'date_mouvement', 'montant',
            'mode_paiement', 'mode_paiement_display',
            'caisse', 'caisse_nom',
            'compte_bancaire', 'compte_nom',
            'origine', 'reference', 'motif',
            'module_source', 'object_id', 'justificatif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'created_at', 'updated_at']

    def get_caisse_nom(self, obj):
        return obj.caisse.nom if obj.caisse else None

    def get_compte_nom(self, obj):
        return obj.compte_bancaire.nom if obj.compte_bancaire else None


# ============================================================
# ENCAISSEMENT
# ============================================================

class EncaissementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    mode_paiement_display = serializers.CharField(
        source='get_mode_paiement_display', read_only=True)
    client_nom = serializers.SerializerMethodField(read_only=True)
    caisse_nom = serializers.SerializerMethodField(read_only=True)
    compte_nom = serializers.SerializerMethodField(read_only=True)
    valide_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Encaissement
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'date_encaissement', 'montant',
            'mode_paiement', 'mode_paiement_display',
            'client', 'client_nom',
            'facture_reference',
            'origine',
            'caisse', 'caisse_nom',
            'compte_bancaire', 'compte_nom',
            'reference', 'motif', 'justificatif',
            'statut', 'statut_display',
            'valide_par', 'valide_par_nom', 'date_validation',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'valide_par', 'date_validation',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_caisse_nom(self, obj):
        return obj.caisse.nom if obj.caisse else None

    def get_compte_nom(self, obj):
        return obj.compte_bancaire.nom if obj.compte_bancaire else None

    def get_valide_par_nom(self, obj):
        if not obj.valide_par:
            return None
        return obj.valide_par.get_full_name() or obj.valide_par.email


class EncaissementListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    client_nom = serializers.SerializerMethodField()

    class Meta:
        model = Encaissement
        fields = [
            'id', 'numero', 'type', 'type_display',
            'date_encaissement', 'montant',
            'client', 'client_nom',
            'origine',
            'statut', 'statut_display',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None


# ============================================================
# DÉCAISSEMENT
# ============================================================

class DecaissementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    mode_paiement_display = serializers.CharField(
        source='get_mode_paiement_display', read_only=True)
    caisse_nom = serializers.SerializerMethodField(read_only=True)
    compte_nom = serializers.SerializerMethodField(read_only=True)
    demande_par_nom = serializers.SerializerMethodField(read_only=True)
    valide_par_nom = serializers.SerializerMethodField(read_only=True)
    paye_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Decaissement
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'date_demande', 'date_paiement',
            'montant', 'mode_paiement', 'mode_paiement_display',
            'beneficiaire', 'fournisseur_reference',
            'caisse', 'caisse_nom',
            'compte_bancaire', 'compte_nom',
            'motif', 'reference', 'justificatif',
            'statut', 'statut_display',
            'demande_par', 'demande_par_nom',
            'valide_par', 'valide_par_nom',
            'paye_par', 'paye_par_nom',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'date_demande',
            'demande_par', 'valide_par', 'paye_par',
        ]

    def get_caisse_nom(self, obj):
        return obj.caisse.nom if obj.caisse else None

    def get_compte_nom(self, obj):
        return obj.compte_bancaire.nom if obj.compte_bancaire else None

    def get_demande_par_nom(self, obj):
        if not obj.demande_par:
            return None
        return obj.demande_par.get_full_name() or obj.demande_par.email

    def get_valide_par_nom(self, obj):
        if not obj.valide_par:
            return None
        return obj.valide_par.get_full_name() or obj.valide_par.email

    def get_paye_par_nom(self, obj):
        if not obj.paye_par:
            return None
        return obj.paye_par.get_full_name() or obj.paye_par.email


class DecaissementListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Decaissement
        fields = [
            'id', 'numero', 'type', 'type_display',
            'date_demande', 'date_paiement',
            'montant', 'beneficiaire',
            'statut', 'statut_display',
        ]


# ============================================================
# MOUVEMENT DE CAISSE
# ============================================================

class MouvementCaisseSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    caisse_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MouvementCaisse
        fields = [
            'id', 'caisse', 'caisse_nom',
            'type', 'type_display',
            'date_mouvement', 'montant', 'libelle',
            'encaissement', 'decaissement',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'date_mouvement']

    def get_caisse_nom(self, obj):
        return obj.caisse.nom if obj.caisse else None


# ============================================================
# PRÉVISION DE TRÉSORERIE
# ============================================================

class PrevisionTresorerieSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = PrevisionTresorerie
        fields = [
            'id', 'date_prevue',
            'type', 'type_display',
            'libelle', 'montant', 'realise', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# ALERTE TRÉSORERIE
# ============================================================

class AlerteTresorerieSerializer(serializers.ModelSerializer):
    niveau_display = serializers.CharField(
        source='get_niveau_display', read_only=True)
    caisse_nom = serializers.SerializerMethodField(read_only=True)
    compte_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AlerteTresorerie
        fields = [
            'id', 'titre', 'message',
            'niveau', 'niveau_display',
            'caisse', 'caisse_nom',
            'compte_bancaire', 'compte_nom',
            'resolue', 'date_resolution',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at',
                            'updated_at', 'date_resolution']

    def get_caisse_nom(self, obj):
        return obj.caisse.nom if obj.caisse else None

    def get_compte_nom(self, obj):
        return obj.compte_bancaire.nom if obj.compte_bancaire else None
