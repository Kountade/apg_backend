# comptabilite/serializers.py
from rest_framework import serializers
from .models import (
    CompteComptable, Journal,
    Facture, LigneFacture,
    Devis, LigneDevis,
    Avoir, PaiementClient, Litige,
    EcritureComptable, LigneEcriture,
    Lettrage, DeclarationFiscale,
    ClotureComptable,  # ✅ NOUVEAU
)


# ============================================================
# COMPTE COMPTABLE
# ============================================================

class CompteComptableSerializer(serializers.ModelSerializer):
    """Lecture / écriture CompteComptable."""
    classe_display = serializers.CharField(
        source='get_classe_display', read_only=True)
    type_display = serializers.CharField(
        source='get_type_compte_display', read_only=True)
    solde = serializers.ReadOnlyField()
    parent_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero', 'libelle',
            'classe', 'classe_display',
            'compte_parent', 'parent_numero',
            'type_compte', 'type_display',
            'actif', 'description',
            'solde',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'solde']

    def get_parent_numero(self, obj):
        return obj.compte_parent.numero if obj.compte_parent else None


class CompteComptableListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    classe_display = serializers.CharField(
        source='get_classe_display', read_only=True)
    type_display = serializers.CharField(
        source='get_type_compte_display', read_only=True)

    class Meta:
        model = CompteComptable
        fields = [
            'id', 'numero', 'libelle',
            'classe', 'classe_display',
            'type_compte', 'type_display',
            'actif',
        ]


# ============================================================
# JOURNAL
# ============================================================

class JournalSerializer(serializers.ModelSerializer):
    """Lecture / écriture Journal."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Journal
        fields = [
            'id', 'code', 'libelle',
            'type', 'type_display', 'actif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JournalListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Journal
        fields = ['id', 'code', 'libelle', 'type', 'type_display', 'actif']


# ============================================================
# LIGNE FACTURE
# ============================================================

class LigneFactureSerializer(serializers.ModelSerializer):
    """Ligne de facture."""
    class Meta:
        model = LigneFacture
        fields = [
            'id', 'facture',
            'designation', 'description',
            'quantite', 'unite',
            'prix_unitaire', 'remise_ligne', 'montant_ht',
            'ordre',
        ]
        read_only_fields = ['id', 'montant_ht']


# ============================================================
# FACTURE
# ============================================================

class FactureSerializer(serializers.ModelSerializer):
    """Lecture / écriture Facture avec lignes imbriquées."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    lignes = LigneFactureSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)
    solde_restant = serializers.ReadOnlyField()
    est_payee = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()
    jours_retard = serializers.ReadOnlyField()
    emise_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Facture
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'client', 'client_nom',
            'contrat',
            'date_emission', 'date_echeance',
            'periode_debut', 'periode_fin',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc',
            'montant_paye', 'remise',
            'solde_restant', 'est_payee',
            'est_en_retard', 'jours_retard',
            'statut', 'statut_display',
            'emise_par', 'emise_par_nom',
            'objet', 'notes', 'conditions_paiement',
            'document_pdf',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero',
            'montant_tva', 'montant_ttc', 'montant_paye',
            'solde_restant', 'est_payee', 'est_en_retard', 'jours_retard',
            'created_at', 'updated_at',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def get_emise_par_nom(self, obj):
        if not obj.emise_par:
            return None
        return obj.emise_par.get_full_name() or obj.emise_par.email

    def validate(self, data):
        date_emission = data.get('date_emission')
        date_echeance = data.get('date_echeance')
        if date_echeance and date_emission and date_echeance < date_emission:
            raise serializers.ValidationError(
                "La date d'échéance doit être postérieure à la date d'émission."
            )
        return data


class FactureListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    client_nom = serializers.SerializerMethodField()
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    solde_restant = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = Facture
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'client', 'client_nom',
            'date_emission', 'date_echeance',
            'montant_ttc', 'montant_paye', 'solde_restant',
            'statut', 'statut_display',
            'est_en_retard',
            'objet',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None


# ============================================================
# LIGNE DEVIS
# ============================================================

class LigneDevisSerializer(serializers.ModelSerializer):
    """Ligne de devis."""
    class Meta:
        model = LigneDevis
        fields = [
            'id', 'devis',
            'designation',
            'quantite',
            'prix_unitaire', 'montant_ht',
        ]
        read_only_fields = ['id', 'montant_ht']


# ============================================================
# DEVIS
# ============================================================

class DevisSerializer(serializers.ModelSerializer):
    """Lecture / écriture Devis avec lignes imbriquées."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    lignes = LigneDevisSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)
    facture_generee_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Devis
        fields = [
            'id', 'numero',
            'client', 'client_nom',
            'objet',
            'date_emission', 'date_validite',
            'montant_ht', 'taux_tva', 'montant_ttc',
            'statut', 'statut_display',
            'facture_generee', 'facture_generee_numero',
            'notes',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'montant_ttc',
            'facture_generee',
            'created_at', 'updated_at',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def get_facture_generee_numero(self, obj):
        return obj.facture_generee.numero if obj.facture_generee else None

    def validate(self, data):
        date_emission = data.get('date_emission')
        date_validite = data.get('date_validite')
        if date_validite and date_emission and date_validite < date_emission:
            raise serializers.ValidationError(
                "La date de validité doit être postérieure à la date d'émission."
            )
        return data


class DevisListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    client_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Devis
        fields = [
            'id', 'numero',
            'client', 'client_nom',
            'objet',
            'date_emission', 'date_validite',
            'montant_ttc',
            'statut', 'statut_display',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None


# ============================================================
# AVOIR
# ============================================================

class AvoirSerializer(serializers.ModelSerializer):
    """Lecture / écriture Avoir."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    facture_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Avoir
        fields = [
            'id', 'numero',
            'client', 'client_nom',
            'facture_origine', 'facture_numero',
            'date_avoir',
            'objet', 'motif',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc',
            'statut', 'statut_display',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero',
            'montant_tva', 'montant_ttc',
            'created_at', 'updated_at',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_facture_numero(self, obj):
        return obj.facture_origine.numero if obj.facture_origine else None


# ============================================================
# PAIEMENT CLIENT
# ============================================================

class PaiementClientSerializer(serializers.ModelSerializer):
    """Lecture / écriture PaiementClient."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    facture_numero = serializers.SerializerMethodField(read_only=True)
    mode_display = serializers.CharField(
        source='get_mode_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = PaiementClient
        fields = [
            'id', 'numero',
            'facture', 'facture_numero',
            'client', 'client_nom',
            'montant', 'date_paiement',
            'mode', 'mode_display',
            'reference', 'notes',
            'statut', 'statut_display',
            'justificatif',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero',
            'created_at', 'updated_at',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_facture_numero(self, obj):
        return obj.facture.numero if obj.facture else None

    def validate(self, data):
        montant = data.get('montant')
        facture = data.get('facture')
        if montant is not None and montant <= 0:
            raise serializers.ValidationError(
                "Le montant doit être supérieur à 0."
            )
        if facture and montant:
            solde_restant = float(facture.solde_restant)
            if float(montant) > solde_restant + 0.01:
                raise serializers.ValidationError(
                    f"Le montant ({montant}) dépasse le solde restant ({solde_restant})."
                )
        return data


# ============================================================
# LITIGE
# ============================================================

class LitigeSerializer(serializers.ModelSerializer):
    """Lecture / écriture Litige."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    facture_numero = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Litige
        fields = [
            'id', 'numero',
            'facture', 'facture_numero',
            'client', 'client_nom',
            'date_ouverture', 'date_resolution',
            'motif', 'description',
            'montant_conteste',
            'statut', 'statut_display',
            'resolution',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'date_ouverture',
            'created_at', 'updated_at',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_facture_numero(self, obj):
        return obj.facture.numero if obj.facture else None


# ============================================================
# LIGNE ÉCRITURE
# ============================================================

class LigneEcritureSerializer(serializers.ModelSerializer):
    """Ligne d'écriture comptable."""
    compte_numero = serializers.SerializerMethodField(read_only=True)
    compte_libelle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LigneEcriture
        fields = [
            'id', 'ecriture',
            'compte', 'compte_numero', 'compte_libelle',
            'libelle',
            'debit', 'credit',
            'lettrage', 'ordre',
        ]
        read_only_fields = ['id']

    def get_compte_numero(self, obj):
        return obj.compte.numero if obj.compte else None

    def get_compte_libelle(self, obj):
        return obj.compte.libelle if obj.compte else None

    def validate(self, data):
        debit = data.get('debit', 0)
        credit = data.get('credit', 0)
        if debit and credit:
            raise serializers.ValidationError(
                "Une ligne ne peut pas avoir à la fois un débit et un crédit."
            )
        if not debit and not credit:
            raise serializers.ValidationError(
                "Une ligne doit avoir soit un débit, soit un crédit."
            )
        return data


# ============================================================
# ÉCRITURE COMPTABLE
# ============================================================

class EcritureComptableSerializer(serializers.ModelSerializer):
    """Lecture / écriture ÉcritureComptable avec lignes imbriquées."""
    journal_code = serializers.SerializerMethodField(read_only=True)
    journal_libelle = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    lignes = LigneEcritureSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)
    est_equilibree = serializers.ReadOnlyField()
    validee_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero',
            'journal', 'journal_code', 'journal_libelle',
            'date_ecriture',
            'libelle', 'reference',
            'statut', 'statut_display',
            'total_debit', 'total_credit', 'est_equilibree',
            'module_source', 'object_id',
            'validee_par', 'validee_par_nom', 'date_validation',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero',
            'total_debit', 'total_credit',
            'est_equilibree',
            'validee_par', 'date_validation',
            'created_at', 'updated_at',
        ]

    def get_journal_code(self, obj):
        return obj.journal.code if obj.journal else None

    def get_journal_libelle(self, obj):
        return obj.journal.libelle if obj.journal else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email


class EcritureComptableListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    journal_code = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    est_equilibree = serializers.ReadOnlyField()

    class Meta:
        model = EcritureComptable
        fields = [
            'id', 'numero',
            'journal_code',
            'date_ecriture',
            'libelle', 'reference',
            'total_debit', 'total_credit',
            'est_equilibree',
            'statut', 'statut_display',
        ]

    def get_journal_code(self, obj):
        return obj.journal.code if obj.journal else None


# ============================================================
# LETTRAGE
# ============================================================

class LettrageSerializer(serializers.ModelSerializer):
    """Lecture / écriture Lettrage."""
    compte_numero = serializers.SerializerMethodField(read_only=True)
    compte_libelle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Lettrage
        fields = [
            'id', 'compte',
            'compte_numero', 'compte_libelle',
            'code_lettrage',
            'date_lettrage',
            'montant_lettre',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'date_lettrage',
            'created_at', 'updated_at',
        ]

    def get_compte_numero(self, obj):
        return obj.compte.numero if obj.compte else None

    def get_compte_libelle(self, obj):
        return obj.compte.libelle if obj.compte else None


# ============================================================
# DÉCLARATION FISCALE
# ============================================================

class DeclarationFiscaleSerializer(serializers.ModelSerializer):
    """Lecture / écriture DéclarationFiscale."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = DeclarationFiscale
        fields = [
            'id',
            'type', 'type_display',
            'periode',
            'montant',
            'date_echeance', 'date_depot', 'date_paiement',
            'statut', 'statut_display',
            'document',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_montant(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Le montant ne peut pas être négatif."
            )
        return value


class DeclarationFiscaleListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = DeclarationFiscale
        fields = [
            'id',
            'type', 'type_display',
            'periode', 'montant',
            'date_echeance',
            'statut', 'statut_display',
        ]


# ============================================================
# CLÔTURE COMPTABLE ✅ NOUVEAU
# ============================================================

class ClotureComptableSerializer(serializers.ModelSerializer):
    """Lecture / écriture ClotureComptable."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    cloture_par_nom = serializers.SerializerMethodField(read_only=True)
    reouverte_par_nom = serializers.SerializerMethodField(read_only=True)
    libelle = serializers.ReadOnlyField()
    est_benefice = serializers.ReadOnlyField()

    class Meta:
        model = ClotureComptable
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'mois', 'annee', 'trimestre',
            'date_debut', 'date_fin',
            'total_debit', 'total_credit',
            'total_produits', 'total_charges', 'resultat',
            'nombre_ecritures',
            'statut', 'statut_display',
            'cloture_par', 'cloture_par_nom', 'date_cloture',
            'reouverte_par', 'reouverte_par_nom', 'date_reouverture',
            'notes', 'rapport_pdf',
            'libelle', 'est_benefice',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero',
            'total_debit', 'total_credit',
            'total_produits', 'total_charges', 'resultat',
            'nombre_ecritures',
            'cloture_par', 'date_cloture',
            'reouverte_par', 'date_reouverture',
            'created_at', 'updated_at',
        ]

    def get_cloture_par_nom(self, obj):
        if not obj.cloture_par:
            return None
        return obj.cloture_par.get_full_name() or obj.cloture_par.email

    def get_reouverte_par_nom(self, obj):
        if not obj.reouverte_par:
            return None
        return obj.reouverte_par.get_full_name() or obj.reouverte_par.email


class ClotureComptableListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    libelle = serializers.ReadOnlyField()
    est_benefice = serializers.ReadOnlyField()

    class Meta:
        model = ClotureComptable
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'mois', 'annee', 'trimestre',
            'date_debut', 'date_fin',
            'resultat', 'nombre_ecritures',
            'statut', 'statut_display',
            'libelle', 'est_benefice',
        ]