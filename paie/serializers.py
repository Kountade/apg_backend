# paie/serializers.py
from rest_framework import serializers
from .models import (
    PeriodePaie, BulletinPaie, LigneBulletin,
    Prime, Retenue, AvanceSalaire, FichePaie,
)


# ============================================================
# PÉRIODE DE PAIE
# ============================================================

class PeriodePaieSerializer(serializers.ModelSerializer):
    """Lecture / écriture Période de paie."""
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    preparee_par_nom = serializers.SerializerMethodField(read_only=True)
    controlee_par_nom = serializers.SerializerMethodField(read_only=True)
    validee_par_nom = serializers.SerializerMethodField(read_only=True)
    payee_par_nom = serializers.SerializerMethodField(read_only=True)
    nombre_bulletins = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PeriodePaie
        fields = [
            'id', 'mois', 'annee', 'libelle',
            'date_debut', 'date_fin', 'date_paiement_prevue',
            'statut', 'statut_display',
            'nombre_employes', 'total_brut', 'total_retenues',
            'total_net', 'total_cnss',
            'preparee_par', 'preparee_par_nom',
            'controlee_par', 'controlee_par_nom',
            'validee_par', 'validee_par_nom',
            'payee_par', 'payee_par_nom',
            'date_controle', 'date_validation', 'date_paiement',
            'nombre_bulletins',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'nombre_employes', 'total_brut', 'total_retenues',
            'total_net', 'total_cnss',
            'preparee_par', 'controlee_par', 'validee_par', 'payee_par',
            'date_controle', 'date_validation', 'date_paiement',
        ]

    def get_preparee_par_nom(self, obj):
        if not obj.preparee_par:
            return None
        return obj.preparee_par.get_full_name() or obj.preparee_par.email

    def get_controlee_par_nom(self, obj):
        if not obj.controlee_par:
            return None
        return obj.controlee_par.get_full_name() or obj.controlee_par.email

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email

    def get_payee_par_nom(self, obj):
        if not obj.payee_par:
            return None
        return obj.payee_par.get_full_name() or obj.payee_par.email

    def get_nombre_bulletins(self, obj):
        return obj.bulletins.count()


class PeriodePaieListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = PeriodePaie
        fields = [
            'id', 'mois', 'annee', 'libelle',
            'date_debut', 'date_fin', 'date_paiement_prevue',
            'statut', 'statut_display',
            'nombre_employes', 'total_brut', 'total_net',
            'created_at',
        ]


# ============================================================
# BULLETIN DE PAIE
# ============================================================

class LigneBulletinSerializer(serializers.ModelSerializer):
    """Ligne de bulletin."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = LigneBulletin
        fields = [
            'id', 'bulletin', 'type', 'type_display',
            'libelle', 'montant', 'imposable', 'ordre',
        ]
        read_only_fields = ['id']


class BulletinPaieSerializer(serializers.ModelSerializer):
    """Lecture / écriture Bulletin de paie."""
    employe_nom = serializers.SerializerMethodField(read_only=True)
    periode_libelle = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    lignes = LigneBulletinSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BulletinPaie
        fields = [
            'id', 'numero', 'periode', 'periode_libelle',
            'employe', 'employe_nom',
            'matricule_snapshot', 'nom_snapshot',
            'poste_snapshot', 'departement_snapshot',
            'salaire_base', 'jours_travailles', 'jours_theoriques',
            'total_primes', 'total_indemnites',
            'heures_supplementaires', 'montant_heures_sup',
            'salaire_brut',
            'cnss_salarial', 'impot_revenu', 'avances_deduites',
            'autres_retenues', 'total_retenues',
            'cnss_patronal',
            'salaire_net',
            'statut', 'statut_display',
            'date_paiement', 'mode_paiement', 'decaissement',
            'document_pdf', 'notes',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'salaire_brut', 'total_retenues', 'salaire_net',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_periode_libelle(self, obj):
        return f"{obj.periode.mois:02d}/{obj.periode.annee}" if obj.periode else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()


class BulletinPaieListSerializer(serializers.ModelSerializer):
    """Version allégée."""
    employe_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = BulletinPaie
        fields = [
            'id', 'numero',
            'employe', 'employe_nom',
            'salaire_base', 'salaire_brut', 'total_retenues', 'salaire_net',
            'statut', 'statut_display',
            'date_paiement',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# PRIME / INDEMNITÉ
# ============================================================

class PrimeSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Prime
        fields = [
            'id', 'code', 'nom',
            'type', 'type_display',
            'montant_fixe', 'pourcentage_salaire',
            'imposable', 'soumis_cnss', 'actif',
            'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# RETENUE
# ============================================================

class RetenueSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Retenue
        fields = [
            'id', 'code', 'nom',
            'type', 'type_display',
            'pourcentage', 'montant_fixe',
            'actif', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# AVANCE SUR SALAIRE
# ============================================================

class AvanceSalaireSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    validee_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AvanceSalaire
        fields = [
            'id', 'numero',
            'employe', 'employe_nom',
            'date_demande', 'montant', 'motif',
            'mois_deduction', 'annee_deduction',
            'statut', 'statut_display',
            'validee_par', 'validee_par_nom', 'date_validation',
            'payee', 'date_paiement',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'created_at', 'updated_at',
            'date_demande', 'validee_par', 'date_validation',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email


class AvanceSalaireListSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = AvanceSalaire
        fields = [
            'id', 'numero',
            'employe', 'employe_nom',
            'date_demande', 'montant',
            'mois_deduction', 'annee_deduction',
            'statut', 'statut_display',
            'payee',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# FICHE DE PAIE
# ============================================================

class FichePaieSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    bulletin_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FichePaie
        fields = [
            'id', 'employe', 'employe_nom',
            'bulletin', 'bulletin_numero',
            'annee', 'mois',
            'salaire_brut', 'salaire_net',
            'fichier_pdf',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_bulletin_numero(self, obj):
        return obj.bulletin.numero if obj.bulletin else None