# rh/serializers.py
from rest_framework import serializers
from .models import (
    Departement, Poste, Employe, Contrat,
    Presence, JoursTravailles, Conge, SoldeConge,
    Absence, Evaluation, Formation,
)


# ============================================================
# DÉPARTEMENTS
# ============================================================

class DepartementSerializer(serializers.ModelSerializer):
    """Lecture / écriture Département."""
    responsable_nom = serializers.SerializerMethodField(read_only=True)
    nombre_employes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Departement
        fields = [
            'id', 'nom', 'code', 'description',
            'responsable', 'responsable_nom', 'nombre_employes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_responsable_nom(self, obj):
        return obj.responsable.nom_complet if obj.responsable else None

    def get_nombre_employes(self, obj):
        return obj.employes.filter(is_deleted=False).count()


# ============================================================
# POSTES
# ============================================================

class PosteSerializer(serializers.ModelSerializer):
    """Lecture / écriture Poste."""
    departement_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Poste
        fields = [
            'id', 'nom', 'departement', 'departement_nom',
            'salaire_min', 'salaire_max', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_departement_nom(self, obj):
        return obj.departement.nom if obj.departement else None

    def validate(self, data):
        """Vérifie que salaire_max >= salaire_min."""
        salaire_min = data.get('salaire_min', 0)
        salaire_max = data.get('salaire_max', 0)
        if salaire_max and salaire_min and salaire_max < salaire_min:
            raise serializers.ValidationError(
                "Le salaire maximum doit être supérieur ou égal au minimum."
            )
        return data


# ============================================================
# EMPLOYÉS
# ============================================================

class EmployeSerializer(serializers.ModelSerializer):
    """Lecture Employé (avec infos enrichies)."""
    nom_complet = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    anciennete_annees = serializers.ReadOnlyField()
    poste_nom = serializers.SerializerMethodField(read_only=True)
    departement_nom = serializers.SerializerMethodField(read_only=True)
    superieur_nom = serializers.SerializerMethodField(read_only=True)
    type_contrat_display = serializers.CharField(
        source='get_type_contrat_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    sexe_display = serializers.CharField(
        source='get_sexe_display', read_only=True)

    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'user',
            # Identité
            'nom', 'prenom', 'nom_complet', 'age',
            'date_naissance', 'lieu_naissance',
            'sexe', 'sexe_display',
            'situation_matrimoniale', 'nationalite',
            # Contact
            'adresse', 'telephone', 'email',
            # Documents
            'numero_cni', 'numero_cnss',
            # Affectation
            'poste', 'poste_nom',
            'departement', 'departement_nom',
            'superieur', 'superieur_nom',
            # Contrat
            'date_embauche', 'type_contrat', 'type_contrat_display',
            'salaire_base', 'statut', 'statut_display',
            'anciennete_annees',
            # Média
            'photo',
            # Métadonnées
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_deleted',
            'nom_complet', 'age', 'anciennete_annees',
        ]

    def get_poste_nom(self, obj):
        return obj.poste.nom if obj.poste else None

    def get_departement_nom(self, obj):
        return obj.departement.nom if obj.departement else None

    def get_superieur_nom(self, obj):
        return obj.superieur.nom_complet if obj.superieur else None


class EmployeListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    nom_complet = serializers.ReadOnlyField()
    poste_nom = serializers.SerializerMethodField()
    departement_nom = serializers.SerializerMethodField()

    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'nom_complet',
            'poste_nom', 'departement_nom',
            'telephone', 'email',
            'statut', 'type_contrat',
            'date_embauche', 'photo',
        ]

    def get_poste_nom(self, obj):
        return obj.poste.nom if obj.poste else None

    def get_departement_nom(self, obj):
        return obj.departement.nom if obj.departement else None


class EmployeWriteSerializer(serializers.ModelSerializer):
    """Création / modification Employé."""
    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'user',
            'nom', 'prenom', 'date_naissance', 'lieu_naissance',
            'sexe', 'situation_matrimoniale', 'nationalite',
            'adresse', 'telephone', 'email',
            'numero_cni', 'numero_cnss',
            'poste', 'departement', 'superieur',
            'date_embauche', 'type_contrat',
            'salaire_base', 'statut', 'photo',
        ]

    def validate_matricule(self, value):
        """Le matricule doit être unique (sauf en modification)."""
        qs = Employe.objects.filter(matricule=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ce matricule est déjà utilisé."
            )
        return value


# ============================================================
# CONTRATS
# ============================================================

class ContratSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    est_expire = serializers.ReadOnlyField()

    class Meta:
        model = Contrat
        fields = [
            'id', 'numero', 'employe', 'employe_nom',
            'type', 'type_display',
            'date_debut', 'date_fin',
            'salaire', 'document',
            'statut', 'statut_display',
            'renouvellement', 'est_expire',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'est_expire']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def validate(self, data):
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        if date_fin and date_debut and date_fin < date_debut:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return data


# ============================================================
# PRÉSENCES
# ============================================================

class PresenceSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    employe_matricule = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Presence
        fields = [
            'id', 'employe', 'employe_nom', 'employe_matricule',
            'date', 'heure_arrivee', 'heure_depart',
            'statut', 'statut_display',
            'motif', 'justificatif', 'heures_travaillees',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_employe_matricule(self, obj):
        return obj.employe.matricule if obj.employe else None

    def validate(self, data):
        employe = data.get('employe')
        date = data.get('date')
        if employe and date:
            qs = Presence.objects.filter(employe=employe, date=date)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Une présence existe déjà pour cet employé à cette date."
                )
        return data


# ============================================================
# JOURS TRAVAILLÉS
# ============================================================

class JoursTravaillesSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JoursTravailles
        fields = [
            'id', 'employe', 'employe_nom',
            'mois', 'annee',
            'jours_theoriques', 'jours_presents',
            'absences_non_justifiees', 'jours_travailles',
            'commentaire',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# CONGÉS
# ============================================================

class CongeSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)
    valide_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conge
        fields = [
            'id', 'numero', 'employe', 'employe_nom',
            'type', 'type_display',
            'date_debut', 'date_fin', 'nombre_jours',
            'motif', 'statut', 'statut_display',
            'valide_par', 'valide_par_nom', 'date_validation',
            'commentaire',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'valide_par', 'date_validation',
        ]

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_valide_par_nom(self, obj):
        if not obj.valide_par:
            return None
        return obj.valide_par.get_full_name() or obj.valide_par.email


class CongeValidationSerializer(serializers.Serializer):
    """Serializer pour valider/refuser un congé."""
    action = serializers.ChoiceField(choices=['valider', 'refuser'])
    commentaire = serializers.CharField(required=False, allow_blank=True)


# ============================================================
# SOLDES DE CONGÉS
# ============================================================

class SoldeCongeSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SoldeConge
        fields = [
            'id', 'employe', 'employe_nom', 'annee',
            'solde_initial', 'jours_acquis', 'jours_pris', 'solde_restant',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# ABSENCES
# ============================================================

class AbsenceSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    type_display = serializers.CharField(
        source='get_type_display', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True)

    class Meta:
        model = Absence
        fields = [
            'id', 'employe', 'employe_nom',
            'date_debut', 'date_fin',
            'type', 'type_display',
            'motif', 'justificatif',
            'statut', 'statut_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# ÉVALUATIONS
# ============================================================

class EvaluationSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField(read_only=True)
    evaluateur_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            'id', 'employe', 'employe_nom',
            'evaluateur', 'evaluateur_nom',
            'date_evaluation', 'periode', 'note_globale',
            'points_forts', 'points_ameliorer', 'objectifs',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None

    def get_evaluateur_nom(self, obj):
        return obj.evaluateur.nom_complet if obj.evaluateur else None

    def validate_note_globale(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError(
                "La note doit être comprise entre 0 et 20."
            )
        return value


# ============================================================
# FORMATIONS
# ============================================================

class FormationSerializer(serializers.ModelSerializer):
    participants_noms = serializers.SerializerMethodField(read_only=True)
    nombre_participants = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Formation
        fields = [
            'id', 'titre', 'description', 'formateur',
            'date_debut', 'date_fin', 'lieu', 'cout',
            'participants', 'participants_noms', 'nombre_participants',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_participants_noms(self, obj):
        return [p.nom_complet for p in obj.participants.all()]

    def get_nombre_participants(self, obj):
        return obj.participants.count()
