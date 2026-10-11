# comptabilite/serializers.py
from rest_framework import serializers
from .models import (
    CompteComptable, Journal,
    Facture, LigneFacture,
    Devis, LigneDevis,
    EcritureComptable, LigneEcriture,
    Lettrage, DeclarationFiscale,
)


# ============================================================
# COMPTE COMPTABLE
# ============================================================

class CompteComptableSerializer(serializers.ModelSerializer):
    """Lecture / écriture Compte comptable."""
    classe_display = serializers.CharField(
        source='get_classe_display', read_only=True)
    type_compte_display = serializers.CharField(
        source='get_type_compte_display', read_only=True)
    parent_numero = serializers.SerializerMethodField(read_only=True)
    nombre_sous_comptes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero', 'libelle',
            'classe', 'classe_display',
            'compte_parent', 'parent_numero', 'nombre_sous_comptes',
            'type_compte', 'type_compte_display',
            'actif', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_parent_numero(self, obj):
        return obj.compte_parent.numero if obj.compte_parent else None

    def get_nombre_sous_comptes(self, obj):
        return obj.sous_comptes.count()


class CompteComptableListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    classe_display = serializers.CharField(
        source='get_classe_display', read_only=True)

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero', 'libelle', 'classe', 'classe_display',
            'type_compte', 'actif',
        ]


# ============================================================
# JOURNAL
# ============================================================

class JournalSerializer(serializers.ModelSerializer):
    """Lecture / écriture Journal."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    nombre_ecritures = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Journal
        fields = [
            'id', 'code', 'libelle',
            'type', 'type_display',
            'actif', 'nombre_ecritures',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nombre_ecritures(self, obj):
        return obj.ecritures.count()


class JournalListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Journal
        fields = ['id', 'code', 'libelle', 'type', 'type_display', 'actif']


# ============================================================
# FACTURE
# ============================================================

class LigneFactureSerializer(serializers.ModelSerializer):
    """Ligne de facture."""
    class Meta:
        model = LigneFacture
        fields = [
            'id', 'facture', 'designation', 'description',
            'quantite', 'unite', 'prix_unitaire', 'remise_ligne',
            'montant_ht', 'ordre',
        ]
        read_only_fields = ['id', 'montant_ht']


class FactureSerializer(serializers.ModelSerializer):
    """Lecture / écriture Facture."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    contrat_numero = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    solde_restant = serializers.ReadOnlyField()
    est_payee = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()
    jours_retard = serializers.ReadOnlyField()
    lignes = LigneFactureSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Facture
        fields = [
            'id', 'numero', 'type', 'type_display',
            'client', 'client_nom',
            'contrat', 'contrat_numero',
            'date_emission', 'date_echeance',
            'periode_debut', 'periode_fin',
            'montant_ht', 'taux_tva', 'montant_tva',
            'montant_ttc', 'montant_paye', 'remise',
            'solde_restant', 'est_payee', 'est_en_retard', 'jours_retard',
            'statut', 'statut_display',
            'emise_par',
            'objet', 'notes', 'conditions_paiement',
            'document_pdf',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'emise_par', 'montant_tva', 'montant_ttc',
            'solde_restant', 'est_payee', 'est_en_retard', 'jours_retard',
        ]
        extra_kwargs = {
            'numero': {'required': False, 'allow_blank': True},
        }

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_contrat_numero(self, obj):
        return obj.contrat.numero if obj.contrat else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def validate_numero(self, value):
        if not value:
            return value
        qs = Facture.objects.filter(numero=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce numéro de facture est déjà utilisé."
            )
        return value


class FactureListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    client_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    solde_restant = serializers.ReadOnlyField()

    class Meta:
        model = Facture
        fields = [
            'id', 'numero', 'client', 'client_nom',
            'date_emission', 'date_echeance',
            'montant_ttc', 'montant_paye', 'solde_restant',
            'statut', 'statut_display',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None


# ============================================================
# DEVIS
# ============================================================

class LigneDevisSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneDevis
        fields = [
            'id', 'devis', 'designation',
            'quantite', 'prix_unitaire', 'montant_ht',
        ]
        read_only_fields = ['id', 'montant_ht']


class DevisSerializer(serializers.ModelSerializer):
    """Lecture / écriture Devis."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    facture_numero = serializers.SerializerMethodField(read_only=True)
    lignes = LigneDevisSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Devis
        fields = [
            'id', 'numero',
            'client', 'client_nom',
            'objet',
            'date_emission', 'date_validite',
            'montant_ht', 'taux_tva', 'montant_ttc',
            'statut', 'statut_display',
            'facture_generee', 'facture_numero',
            'notes',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'montant_ttc',
        ]
        extra_kwargs = {
            'numero': {'required': False, 'allow_blank': True},
        }

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_facture_numero(self, obj):
        return obj.facture_generee.numero if obj.facture_generee else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def validate_numero(self, value):
        if not value:
            return value
        qs = Devis.objects.filter(numero=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce numéro de devis est déjà utilisé."
            )
        return value


class DevisListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    client_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Devis
        fields = [
            'id', 'numero', 'client', 'client_nom',
            'objet', 'date_emission', 'date_validite',
            'montant_ttc', 'statut', 'statut_display',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None


# ============================================================
# ÉCRITURE COMPTABLE
# ============================================================

class LigneEcritureSerializer(serializers.ModelSerializer):
    compte_numero = serializers.SerializerMethodField(read_only=True)
    compte_libelle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LigneEcriture
        fields = [
            'id', 'ecriture',
            'compte', 'compte_numero', 'compte_libelle',
            'libelle', 'debit', 'credit', 'lettrage', 'ordre',
        ]
        read_only_fields = ['id']

    def get_compte_numero(self, obj):
        return obj.compte.numero if obj.compte else None

    def get_compte_libelle(self, obj):
        return obj.compte.libelle if obj.compte else None


class EcritureComptableSerializer(serializers.ModelSerializer):
    """Lecture / écriture Écriture comptable."""
    journal_code = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    est_equilibree = serializers.ReadOnlyField()
    validee_par_nom = serializers.SerializerMethodField(read_only=True)
    lignes = LigneEcritureSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero',
            'journal', 'journal_code',
            'date_ecriture', 'libelle', 'reference',
            'statut', 'statut_display',
            'module_source', 'object_id',
            'total_debit', 'total_credit', 'est_equilibree',
            'validee_par', 'validee_par_nom', 'date_validation',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'validee_par', 'date_validation',
        ]
        extra_kwargs = {
            'numero': {'required': False, 'allow_blank': True},
        }

    def get_journal_code(self, obj):
        return obj.journal.code if obj.journal else None

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def validate_numero(self, value):
        if not value:
            return value
        qs = EcritureComptable.objects.filter(numero=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce numéro d'écriture est déjà utilisé."
            )
        return value


class EcritureComptableListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    journal_code = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero', 'journal', 'journal_code',
            'date_ecriture', 'libelle',
            'total_debit', 'total_credit',
            'statut', 'statut_display',
        ]

    def get_journal_code(self, obj):
        return obj.journal.code if obj.journal else None


# ============================================================
# LETTRAGE
# ============================================================

class LettrageSerializer(serializers.ModelSerializer):
    compte_numero = serializers.SerializerMethodField(read_only=True)
    compte_libelle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Lettrage
        fields = [
            'id', 'compte', 'compte_numero', 'compte_libelle',
            'code_lettrage', 'date_lettrage', 'montant_lettre', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'date_lettrage']

    def get_compte_numero(self, obj):
        return obj.compte.numero if obj.compte else None

    def get_compte_libelle(self, obj):
        return obj.compte.libelle if obj.compte else None


# ============================================================
# DÉCLARATION FISCALE
# ============================================================

class DeclarationFiscaleSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = DeclarationFiscale
        fields = [
            'id', 'type', 'type_display',
            'periode', 'montant',
            'date_echeance', 'date_depot', 'date_paiement',
            'statut', 'statut_display',
            'document', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeclarationFiscaleListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = DeclarationFiscale
        fields = [
            'id', 'type', 'type_display', 'periode', 'montant',
            'date_echeance', 'statut', 'statut_display',
        ]
