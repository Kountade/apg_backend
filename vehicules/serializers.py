# vehicules/serializers.py
from rest_framework import serializers
from .models import (
    Tricycle, Vehicule, Conducteur,
    AffectationVehicule, DocumentVehicule, Assurance,
    SuiviGPS, PleinCarburant,
)


# ============================================================
# VALIDATION UTILITAIRE — XOR tricycle/vehicule
# ============================================================

def validate_xor_tricycle_vehicule(data, instance=None):
    """
    Valide qu'exactement UN des deux champs (tricycle, vehicule) est fourni.
    En édition, garde les valeurs existantes si non fournies.
    """
    tricycle = data.get('tricycle')
    vehicule = data.get('vehicule')

    if instance:
        # En édition, si non fourni, garde l'existant
        if 'tricycle' not in data:
            tricycle = instance.tricycle
        if 'vehicule' not in data:
            vehicule = instance.vehicule

    if not tricycle and not vehicule:
        raise serializers.ValidationError(
            "Vous devez sélectionner soit un tricycle, soit un véhicule."
        )
    if tricycle and vehicule:
        raise serializers.ValidationError(
            "Sélectionnez UN SEUL engin : soit un tricycle, soit un véhicule, pas les deux."
        )
    return data


# ============================================================
# TRICYCLE
# ============================================================

class TricycleSerializer(serializers.ModelSerializer):
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    conducteur_nom = serializers.SerializerMethodField(read_only=True)
    equipement_code = serializers.SerializerMethodField(read_only=True)
    equipement_designation = serializers.SerializerMethodField(read_only=True)

    # Propriétés dérivées de stocks
    valeur_actuelle = serializers.ReadOnlyField()
    cout_acquisition_stocks = serializers.ReadOnlyField()
    etat_stocks = serializers.ReadOnlyField()
    categorie_nom = serializers.ReadOnlyField()

    # Vidange & assurance
    kilometrage_depuis_vidange = serializers.ReadOnlyField()
    vidange_a_faire = serializers.ReadOnlyField()
    date_expiration_assurance = serializers.ReadOnlyField()
    est_assurance_valide = serializers.ReadOnlyField()

    class Meta:
        model = Tricycle
        fields = [
            'id', 'numero_interne', 'immatriculation',
            'marque', 'modele', 'annee',
            'numero_chassis', 'numero_moteur',
            'date_acquisition', 'cout_acquisition',
            'capacite_charge', 'kilometrage_actuel',
            'date_derniere_vidange', 'km_derniere_vidange', 'intervalle_vidange_km',
            'etat', 'etat_display',
            'statut', 'statut_display',
            'conducteur_affecte', 'conducteur_nom',
            'zone_exploitation',
            'photo', 'notes',
            # Lien stocks
            'equipement', 'equipement_code', 'equipement_designation',
            # Propriétés calculées
            'valeur_actuelle', 'cout_acquisition_stocks',
            'etat_stocks', 'categorie_nom',
            'kilometrage_depuis_vidange', 'vidange_a_faire',
            'date_expiration_assurance', 'est_assurance_valide',
            # Meta
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_deleted',
            'valeur_actuelle', 'cout_acquisition_stocks',
            'etat_stocks', 'categorie_nom',
            'kilometrage_depuis_vidange', 'vidange_a_faire',
            'date_expiration_assurance', 'est_assurance_valide',
        ]

    def get_conducteur_nom(self, obj):
        return obj.conducteur_affecte.nom_complet if obj.conducteur_affecte else None

    def get_equipement_code(self, obj):
        return obj.equipement.code if obj.equipement else None

    def get_equipement_designation(self, obj):
        return obj.equipement.designation if obj.equipement else None


class TricycleListSerializer(serializers.ModelSerializer):
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    conducteur_nom = serializers.SerializerMethodField()
    valeur_actuelle = serializers.ReadOnlyField()

    class Meta:
        model = Tricycle
        fields = [
            'id', 'numero_interne', 'immatriculation',
            'marque', 'modele',
            'kilometrage_actuel',
            'etat', 'etat_display',
            'statut', 'statut_display',
            'conducteur_nom',
            'zone_exploitation',
            'photo',
            'valeur_actuelle',
        ]

    def get_conducteur_nom(self, obj):
        return obj.conducteur_affecte.nom_complet if obj.conducteur_affecte else None


# ============================================================
# VÉHICULE
# ============================================================

class VehiculeSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    conducteur_nom = serializers.SerializerMethodField(read_only=True)
    equipement_code = serializers.SerializerMethodField(read_only=True)
    equipement_designation = serializers.SerializerMethodField(read_only=True)

    # Propriétés dérivées
    valeur_actuelle = serializers.ReadOnlyField()
    cout_acquisition_stocks = serializers.ReadOnlyField()
    etat_stocks = serializers.ReadOnlyField()
    categorie_nom = serializers.ReadOnlyField()

    kilometrage_depuis_vidange = serializers.ReadOnlyField()
    vidange_a_faire = serializers.ReadOnlyField()
    date_expiration_assurance = serializers.ReadOnlyField()
    est_assurance_valide = serializers.ReadOnlyField()

    class Meta:
        model = Vehicule
        fields = [
            'id', 'numero_interne', 'immatriculation',
            'type', 'type_display',
            'marque', 'modele', 'annee',
            'numero_chassis', 'numero_moteur',
            'date_acquisition', 'cout_acquisition',
            'capacite_charge', 'kilometrage_actuel',
            'date_derniere_vidange', 'km_derniere_vidange', 'intervalle_vidange_km',
            'etat', 'etat_display',
            'statut', 'statut_display',
            'conducteur_affecte', 'conducteur_nom',
            'zone_exploitation',
            'photo', 'notes',
            'equipement', 'equipement_code', 'equipement_designation',
            'valeur_actuelle', 'cout_acquisition_stocks',
            'etat_stocks', 'categorie_nom',
            'kilometrage_depuis_vidange', 'vidange_a_faire',
            'date_expiration_assurance', 'est_assurance_valide',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_deleted',
            'valeur_actuelle', 'cout_acquisition_stocks',
            'etat_stocks', 'categorie_nom',
            'kilometrage_depuis_vidange', 'vidange_a_faire',
            'date_expiration_assurance', 'est_assurance_valide',
        ]

    def get_conducteur_nom(self, obj):
        return obj.conducteur_affecte.nom_complet if obj.conducteur_affecte else None

    def get_equipement_code(self, obj):
        return obj.equipement.code if obj.equipement else None

    def get_equipement_designation(self, obj):
        return obj.equipement.designation if obj.equipement else None


class VehiculeListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    conducteur_nom = serializers.SerializerMethodField()
    valeur_actuelle = serializers.ReadOnlyField()

    class Meta:
        model = Vehicule
        fields = [
            'id', 'numero_interne', 'immatriculation',
            'type', 'type_display',
            'marque', 'modele',
            'kilometrage_actuel',
            'etat', 'etat_display',
            'statut', 'statut_display',
            'conducteur_nom',
            'zone_exploitation',
            'photo',
            'valeur_actuelle',
        ]

    def get_conducteur_nom(self, obj):
        return obj.conducteur_affecte.nom_complet if obj.conducteur_affecte else None


# ============================================================
# CONDUCTEUR
# ============================================================

class ConducteurSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    employe_telephone = serializers.SerializerMethodField(read_only=True)
    permis_valide = serializers.ReadOnlyField()
    jours_avant_expiration_permis = serializers.ReadOnlyField()
    nombre_affectations = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conducteur
        fields = [
            'id',
            'employe', 'employe_nom', 'employe_telephone',
            'numero_permis', 'categorie_permis',
            'date_expiration_permis',
            'annees_experience',
            'actif',
            'permis_valide', 'jours_avant_expiration_permis',
            'nombre_affectations',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'permis_valide', 'jours_avant_expiration_permis',
            'nombre_affectations',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_employe_telephone(self, obj):
        return getattr(obj.employe, 'telephone', None) if obj.employe else None

    def get_nombre_affectations(self, obj):
        return obj.affectations.count()


class ConducteurListSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField()
    permis_valide = serializers.ReadOnlyField()

    class Meta:
        model = Conducteur
        fields = [
            'id', 'employe_nom',
            'numero_permis', 'categorie_permis',
            'date_expiration_permis',
            'permis_valide',
            'annees_experience', 'actif',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# AFFECTATION VÉHICULE
# ============================================================

class AffectationVehiculeSerializer(serializers.ModelSerializer):
    conducteur_nom = serializers.SerializerMethodField(read_only=True)
    tricycle_numero = serializers.SerializerMethodField(read_only=True)
    vehicule_numero = serializers.SerializerMethodField(read_only=True)
    engin_libelle = serializers.SerializerMethodField(read_only=True)
    est_en_cours = serializers.ReadOnlyField()

    class Meta:
        model = AffectationVehicule
        fields = [
            'id',
            'tricycle', 'tricycle_numero',
            'vehicule', 'vehicule_numero',
            'engin_libelle',
            'conducteur', 'conducteur_nom',
            'date_debut', 'date_fin',
            'zone', 'observation',
            'est_en_cours',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'est_en_cours']

    def validate(self, data):
        validate_xor_tricycle_vehicule(data, self.instance)
        return data

    def get_conducteur_nom(self, obj):
        if not obj.conducteur or not obj.conducteur.employe:
            return None
        return obj.conducteur.employe.nom_complet

    def get_tricycle_numero(self, obj):
        return obj.tricycle.numero_interne if obj.tricycle else None

    def get_vehicule_numero(self, obj):
        return obj.vehicule.numero_interne if obj.vehicule else None

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


class AffectationVehiculeListSerializer(serializers.ModelSerializer):
    conducteur_nom = serializers.SerializerMethodField()
    engin_libelle = serializers.SerializerMethodField()
    est_en_cours = serializers.ReadOnlyField()

    class Meta:
        model = AffectationVehicule
        fields = [
            'id', 'engin_libelle',
            'conducteur_nom',
            'date_debut', 'date_fin',
            'zone', 'est_en_cours',
        ]

    def get_conducteur_nom(self, obj):
        if not obj.conducteur or not obj.conducteur.employe:
            return None
        return obj.conducteur.employe.nom_complet

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


# ============================================================
# DOCUMENT VÉHICULE
# ============================================================

class DocumentVehiculeSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    tricycle_numero = serializers.SerializerMethodField(read_only=True)
    vehicule_numero = serializers.SerializerMethodField(read_only=True)
    engin_libelle = serializers.SerializerMethodField(read_only=True)
    est_expire = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()

    class Meta:
        model = DocumentVehicule
        fields = [
            'id',
            'tricycle', 'tricycle_numero',
            'vehicule', 'vehicule_numero',
            'engin_libelle',
            'type', 'type_display',
            'numero', 'organisme',
            'date_emission', 'date_expiration',
            'montant',
            'fichier', 'notes',
            'est_expire', 'jours_avant_expiration',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'est_expire', 'jours_avant_expiration',
        ]

    def validate(self, data):
        validate_xor_tricycle_vehicule(data, self.instance)
        return data

    def get_tricycle_numero(self, obj):
        return obj.tricycle.numero_interne if obj.tricycle else None

    def get_vehicule_numero(self, obj):
        return obj.vehicule.numero_interne if obj.vehicule else None

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


# ============================================================
# ASSURANCE
# ============================================================

class AssuranceSerializer(serializers.ModelSerializer):
    tricycle_numero = serializers.SerializerMethodField(read_only=True)
    vehicule_numero = serializers.SerializerMethodField(read_only=True)
    engin_libelle = serializers.SerializerMethodField(read_only=True)
    est_expire = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()

    class Meta:
        model = Assurance
        fields = [
            'id',
            'tricycle', 'tricycle_numero',
            'vehicule', 'vehicule_numero',
            'engin_libelle',
            'compagnie', 'numero_police',
            'type_couverture',
            'prime_annuelle',
            'date_debut', 'date_fin',
            'fichier', 'notes',
            'est_expire', 'jours_avant_expiration',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'est_expire', 'jours_avant_expiration',
        ]

    def validate(self, data):
        validate_xor_tricycle_vehicule(data, self.instance)
        return data

    def validate_date_fin(self, value):
        date_debut = self.initial_data.get('date_debut')
        if date_debut and value:
            from datetime import datetime
            try:
                debut = datetime.strptime(str(date_debut), '%Y-%m-%d').date()
                if value < debut:
                    raise serializers.ValidationError(
                        "La date de fin doit être après la date de début."
                    )
            except (ValueError, TypeError):
                pass
        return value

    def get_tricycle_numero(self, obj):
        return obj.tricycle.numero_interne if obj.tricycle else None

    def get_vehicule_numero(self, obj):
        return obj.vehicule.numero_interne if obj.vehicule else None

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


class AssuranceListSerializer(serializers.ModelSerializer):
    engin_libelle = serializers.SerializerMethodField()
    est_expire = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()

    class Meta:
        model = Assurance
        fields = [
            'id', 'engin_libelle',
            'compagnie', 'numero_police',
            'prime_annuelle',
            'date_debut', 'date_fin',
            'est_expire', 'jours_avant_expiration',
        ]

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


# ============================================================
# SUIVI GPS
# ============================================================

class SuiviGPSSerializer(serializers.ModelSerializer):
    tricycle_numero = serializers.SerializerMethodField(read_only=True)
    vehicule_numero = serializers.SerializerMethodField(read_only=True)
    engin_libelle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SuiviGPS
        fields = [
            'id',
            'tricycle', 'tricycle_numero',
            'vehicule', 'vehicule_numero',
            'engin_libelle',
            'latitude', 'longitude',
            'vitesse', 'cap',
            'date_position', 'adresse',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        validate_xor_tricycle_vehicule(data, self.instance)
        return data

    def get_tricycle_numero(self, obj):
        return obj.tricycle.numero_interne if obj.tricycle else None

    def get_vehicule_numero(self, obj):
        return obj.vehicule.numero_interne if obj.vehicule else None

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None


# ============================================================
# PLEIN CARBURANT
# ============================================================

class PleinCarburantSerializer(serializers.ModelSerializer):
    type_carburant_display = serializers.CharField(source='get_type_carburant_display', read_only=True)
    tricycle_numero = serializers.SerializerMethodField(read_only=True)
    vehicule_numero = serializers.SerializerMethodField(read_only=True)
    engin_libelle = serializers.SerializerMethodField(read_only=True)
    conducteur_nom = serializers.SerializerMethodField(read_only=True)
    consommation = serializers.ReadOnlyField()
    distance_parcourue = serializers.ReadOnlyField()

    class Meta:
        model = PleinCarburant
        fields = [
            'id',
            'tricycle', 'tricycle_numero',
            'vehicule', 'vehicule_numero',
            'engin_libelle',
            'date', 'type_carburant', 'type_carburant_display',
            'litres', 'prix_litre', 'montant',
            'km_compteur',
            'station',
            'conducteur', 'conducteur_nom',
            'justificatif', 'notes',
            'consommation', 'distance_parcourue',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'montant', 'consommation', 'distance_parcourue',
        ]

    def validate(self, data):
        validate_xor_tricycle_vehicule(data, self.instance)
        # Validation litres > 0
        if data.get('litres') is not None and float(data['litres']) <= 0:
            raise serializers.ValidationError(
                {"litres": "Le nombre de litres doit être supérieur à 0."}
            )
        return data

    def get_tricycle_numero(self, obj):
        return obj.tricycle.numero_interne if obj.tricycle else None

    def get_vehicule_numero(self, obj):
        return obj.vehicule.numero_interne if obj.vehicule else None

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None

    def get_conducteur_nom(self, obj):
        return obj.conducteur.nom_complet if obj.conducteur else None


class PleinCarburantListSerializer(serializers.ModelSerializer):
    engin_libelle = serializers.SerializerMethodField()
    type_carburant_display = serializers.CharField(source='get_type_carburant_display', read_only=True)
    consommation = serializers.ReadOnlyField()

    class Meta:
        model = PleinCarburant
        fields = [
            'id', 'engin_libelle',
            'date', 'type_carburant', 'type_carburant_display',
            'litres', 'prix_litre', 'montant',
            'km_compteur',
            'consommation',
            'station',
        ]

    def get_engin_libelle(self, obj):
        if obj.tricycle:
            return f"Tricycle {obj.tricycle.numero_interne}"
        if obj.vehicule:
            return f"Véhicule {obj.vehicule.numero_interne}"
        return None