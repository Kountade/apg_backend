# clients/serializers.py
from rest_framework import serializers
from .models import (
    Client, ContratClient, Prestation, Relance, TypeContrat,
)


# ============================================================
# TYPE DE CONTRAT (référentiel)
# ============================================================

class TypeContratSerializer(serializers.ModelSerializer):
    """Lecture / écriture TypeContrat avec code auto-généré."""
    categorie_display = serializers.CharField(
        source='get_categorie_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = TypeContrat
        fields = [
            'id', 'code', 'titre',
            'categorie', 'categorie_display',
            'description', 'contenu',
            'duree_mois', 'periode_essai_jours', 'preavis_jours',
            'reference_legale',
            'fichier_modele',
            'statut', 'statut_display',
            'ordre', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'code': {
                'required': False,
                'allow_blank': True,
            }
        }

    def validate_code(self, value):
        if not value:
            return value
        qs = TypeContrat.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce code de type de contrat est déjà utilisé."
            )
        return value


class TypeContratListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes déroulantes."""
    categorie_display = serializers.CharField(
        source='get_categorie_display', read_only=True)

    class Meta:
        model = TypeContrat
        fields = [
            'id', 'code', 'titre',
            'categorie', 'categorie_display',
            'duree_mois', 'statut',
        ]


# ============================================================
# CLIENT
# ============================================================

class ClientSerializer(serializers.ModelSerializer):
    """Lecture Client (avec infos enrichies)."""
    nom_complet = serializers.ReadOnlyField()
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    solde_du = serializers.ReadOnlyField()
    total_facture = serializers.ReadOnlyField()
    total_paye = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            'id', 'code', 'type', 'type_display', 'statut', 'statut_display',
            'nom', 'prenom', 'nom_complet', 'sigle', 'sexe',
            'telephone', 'telephone2', 'email',
            'adresse', 'ville', 'quartier', 'zone',
            'num_contribuable', 'num_rccm',
            'contact_nom', 'contact_fonction', 'contact_telephone',
            'compte_utilisateur',
            'latitude', 'longitude',
            'photo', 'notes',
            'solde_du', 'total_facture', 'total_paye',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_deleted',
            'nom_complet', 'solde_du', 'total_facture', 'total_paye',
        ]


class ClientListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    nom_complet = serializers.ReadOnlyField()
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'code', 'nom', 'prenom', 'nom_complet',
            'type', 'type_display', 'statut',
            'telephone', 'email', 'zone', 'photo',
        ]


class ClientWriteSerializer(serializers.ModelSerializer):
    """Création / modification Client."""

    class Meta:
        model = Client
        fields = [
            'id', 'code', 'type', 'statut',
            'nom', 'prenom', 'sigle', 'sexe',
            'telephone', 'telephone2', 'email',
            'adresse', 'ville', 'quartier', 'zone',
            'num_contribuable', 'num_rccm',
            'contact_nom', 'contact_fonction', 'contact_telephone',
            'compte_utilisateur',
            'latitude', 'longitude',
            'photo', 'notes',
        ]

    def validate_code(self, value):
        qs = Client.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce code client est déjà utilisé.")
        return value

    def validate_telephone(self, value):
        if not value:
            raise serializers.ValidationError("Le téléphone est obligatoire.")
        return value


# ============================================================
# CONTRAT CLIENT
# ============================================================

class ContratClientSerializer(serializers.ModelSerializer):
    """Lecture / écriture ContratClient avec type_contrat intégré."""
    client_nom = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    frequence_display = serializers.CharField(
        source='get_frequence_display', read_only=True)
    modalite_paiement_display = serializers.CharField(
        source='get_modalite_paiement_display', read_only=True)
    est_actif = serializers.ReadOnlyField()
    est_expire = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()
    montant_ttc = serializers.ReadOnlyField()
    equipe_nom = serializers.SerializerMethodField(read_only=True)

    # ✅ NOUVEAU : type_contrat
    type_contrat = serializers.PrimaryKeyRelatedField(
        queryset=TypeContrat.objects.filter(statut='actif'),
        required=False, allow_null=True,
    )
    type_contrat_titre = serializers.SerializerMethodField(read_only=True)
    type_contrat_code = serializers.SerializerMethodField(read_only=True)
    type_contrat_contenu = serializers.SerializerMethodField(read_only=True)
    type_contrat_categorie = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ContratClient
        fields = [
            'id', 'numero', 'client', 'client_nom',
            # ✅ NOUVEAU
            'type_contrat', 'type_contrat_titre', 'type_contrat_code',
            'type_contrat_contenu', 'type_contrat_categorie',
            'prestation', 'description',
            'frequence', 'frequence_display',
            'zone',
            'date_debut', 'date_fin',
            'reconduction_tacite', 'jours_preavis',
            'tarif', 'tva', 'montant_ttc',
            'modalite_paiement', 'modalite_paiement_display',
            'equipe', 'equipe_nom',
            'statut', 'statut_display',
            'valide_par', 'date_validation',
            'document', 'conditions_particulieres',
            'est_actif', 'est_expire', 'jours_avant_expiration',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'valide_par', 'date_validation',
            'est_actif', 'est_expire', 'jours_avant_expiration', 'montant_ttc',
        ]
        extra_kwargs = {
            'numero': {
                'required': False,
                'allow_blank': True,
            }
        }

    # ---------- Méthodes enrichies ----------
    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_equipe_nom(self, obj):
        return obj.equipe.nom_complet if obj.equipe else None

    def get_type_contrat_titre(self, obj):
        return obj.type_contrat.titre if obj.type_contrat else None

    def get_type_contrat_code(self, obj):
        return obj.type_contrat.code if obj.type_contrat else None

    def get_type_contrat_contenu(self, obj):
        return obj.type_contrat.contenu if obj.type_contrat else None

    def get_type_contrat_categorie(self, obj):
        return obj.type_contrat.get_categorie_display() if obj.type_contrat else None

    # ---------- Validations ----------
    def validate_numero(self, value):
        if not value:
            return value
        qs = ContratClient.objects.filter(numero=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce numéro de contrat est déjà utilisé."
            )
        return value

    def validate(self, data):
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        if date_fin and date_debut and date_fin < date_debut:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return data


class ContratClientListSerializer(serializers.ModelSerializer):
    """Version allégée avec type_contrat_titre."""
    client_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    type_contrat_titre = serializers.SerializerMethodField()

    class Meta:
        model = ContratClient
        fields = [
            'id', 'numero', 'client', 'client_nom',
            # ✅ NOUVEAU
            'type_contrat', 'type_contrat_titre',
            'prestation', 'frequence',
            'date_debut', 'date_fin',
            'tarif', 'statut', 'statut_display',
        ]

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None

    def get_type_contrat_titre(self, obj):
        return obj.type_contrat.titre if obj.type_contrat else None


class ContratClientValidationSerializer(serializers.Serializer):
    """Serializer pour valider un contrat."""
    action = serializers.ChoiceField(
        choices=['valider', 'resilier', 'suspendre'])
    commentaire = serializers.CharField(required=False, allow_blank=True)


# ============================================================
# PRESTATION
# ============================================================

class PrestationSerializer(serializers.ModelSerializer):
    """Lecture / écriture Prestation avec code auto-généré et modifiable."""

    class Meta:
        model = Prestation
        fields = [
            'id', 'code', 'nom', 'description',
            'tarif_base', 'unite', 'actif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'code': {
                'required': False,
                'allow_blank': True,
            }
        }

    def validate_code(self, value):
        if not value:
            return value
        qs = Prestation.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce code prestation est déjà utilisé."
            )
        return value


# ============================================================
# RELANCE
# ============================================================

class RelanceSerializer(serializers.ModelSerializer):
    client_nom = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Relance
        fields = [
            'id', 'client', 'client_nom',
            'facture_reference',
            'type', 'type_display',
            'date_relance', 'message', 'montant_reclame',
            'reponse_client', 'prochaine_relance',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'date_relance']

    def get_client_nom(self, obj):
        return obj.client.nom_complet if obj.client else None
