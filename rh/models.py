# rh/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel


# ============================================================
# STRUCTURE ORGANISATIONNELLE
# ============================================================

class Departement(BaseModel):
    """Département / service de l'entreprise."""
    nom = models.CharField(max_length=100, verbose_name="Nom")
    code = models.CharField(max_length=20, blank=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    responsable = models.ForeignKey(
        'Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='departements_diriges',
        verbose_name="Responsable",
    )

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Poste(BaseModel):
    """Poste / fonction dans l'entreprise."""
    nom = models.CharField(max_length=100, verbose_name="Intitulé")
    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name='postes',
        verbose_name="Département",
    )
    salaire_min = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Salaire minimum",
    )
    salaire_max = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Salaire maximum",
    )
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.departement.nom})"


# ============================================================
# EMPLOYÉS
# ============================================================

class Employe(SoftDeleteModel):
    """Dossier numérique de chaque employé APG."""

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    TYPE_CONTRAT_CHOICES = [
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('STAGE', 'Stage'),
        ('TEMPORAIRE', 'Temporaire'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('parti', 'Parti'),
    ]

    matricule = models.CharField(
        max_length=20, unique=True, verbose_name="Matricule")

    # Lien vers le compte utilisateur (optionnel)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='employe_profile',
        verbose_name="Compte utilisateur",
    )

    # Identité
    nom = models.CharField(max_length=150, verbose_name="Nom")
    prenom = models.CharField(max_length=150, verbose_name="Prénom")
    date_naissance = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance")
    lieu_naissance = models.CharField(
        max_length=100, blank=True, verbose_name="Lieu de naissance")
    sexe = models.CharField(
        max_length=10, choices=SEXE_CHOICES, verbose_name="Sexe")
    situation_matrimoniale = models.CharField(
        max_length=30, blank=True, verbose_name="Situation matrimoniale")
    nationalite = models.CharField(
        max_length=50, default='Guinéenne', verbose_name="Nationalité")

    # Contact
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(
        max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Documents administratifs
    numero_cni = models.CharField(
        max_length=50, blank=True, verbose_name="N° CNI")
    numero_cnss = models.CharField(
        max_length=50, blank=True, verbose_name="N° CNSS")

    # Affectation
    poste = models.ForeignKey(
        Poste,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='employes',
        verbose_name="Poste",
    )
    departement = models.ForeignKey(
        Departement,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='employes',
        verbose_name="Département",
    )
    superieur = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='subordonnes',
        verbose_name="Supérieur hiérarchique",
    )

    # Contrat
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    type_contrat = models.CharField(
        max_length=30,
        choices=TYPE_CONTRAT_CHOICES,
        verbose_name="Type de contrat",
    )
    salaire_base = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Salaire de base (GNF)",
    )
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name="Statut",
    )

    # Média
    photo = models.ImageField(upload_to='employes/',
                              null=True, blank=True, verbose_name="Photo")

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['matricule']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.matricule} — {self.nom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def age(self):
        if not self.date_naissance:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (
                self.date_naissance.month, self.date_naissance.day)
        )

    @property
    def anciennete_annees(self):
        if not self.date_embauche:
            return 0
        from datetime import date
        today = date.today()
        return today.year - self.date_embauche.year


# ============================================================
# CONTRATS
# ============================================================

class Contrat(BaseModel):
    """Contrats de travail des employés."""

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('rompu', 'Rompu'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='contrats',
        verbose_name="Employé",
    )
    type = models.CharField(
        max_length=30,
        choices=Employe.TYPE_CONTRAT_CHOICES,
        verbose_name="Type",
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True, blank=True, verbose_name="Date de fin")
    salaire = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Salaire contractuel",
    )
    document = models.FileField(
        upload_to='contrats/', null=True, blank=True,
        verbose_name="Document scanné",
    )
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name="Statut",
    )
    renouvellement = models.BooleanField(
        default=False, verbose_name="Renouvelable")

    class Meta:
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.numero} — {self.employe.nom_complet}"

    @property
    def est_expire(self):
        from datetime import date
        return self.date_fin and self.date_fin < date.today()


# ============================================================
# PRÉSENCES
# ============================================================

class Presence(BaseModel):
    """Feuille de présence quotidienne."""

    STATUT_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('retard', 'Retard'),
        ('mission', 'Mission'),
        ('conge', 'Congé'),
        ('repos', 'Repos'),
        ('depart_anticipe', 'Départ anticipé'),
    ]

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='presences',
        verbose_name="Employé",
    )
    date = models.DateField(verbose_name="Date")
    heure_arrivee = models.TimeField(
        null=True, blank=True, verbose_name="Heure d'arrivée")
    heure_depart = models.TimeField(
        null=True, blank=True, verbose_name="Heure de départ")
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='present',
        verbose_name="Statut",
    )
    motif = models.TextField(blank=True, verbose_name="Motif")
    justificatif = models.FileField(
        upload_to='justificatifs/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif",
    )
    heures_travaillees = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Heures travaillées",
    )

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ['employe', 'date']
        ordering = ['-date', 'employe__nom']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.date} ({self.get_statut_display()})"


# ============================================================
# JOURS TRAVAILLÉS (calcul mensuel)
# ============================================================

class JoursTravailles(BaseModel):
    """Calcul automatique des jours travaillés par mois."""

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='jours_travailles',
        verbose_name="Employé",
    )
    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    jours_theoriques = models.IntegerField(
        default=0, verbose_name="Jours théoriques")
    jours_presents = models.IntegerField(
        default=0, verbose_name="Jours présents")
    absences_non_justifiees = models.IntegerField(
        default=0, verbose_name="Absences non justifiées")
    jours_travailles = models.IntegerField(
        default=0, verbose_name="Jours travaillés")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Jours travaillés"
        verbose_name_plural = "Jours travaillés"
        unique_together = ['employe', 'mois', 'annee']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.mois}/{self.annee}"


# ============================================================
# CONGÉS
# ============================================================

class Conge(BaseModel):
    """Demandes et suivi des congés."""

    TYPE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('exceptionnel', 'Congé exceptionnel'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
        ('annule', 'Annulé'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='conges',
        verbose_name="Employé",
    )
    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    nombre_jours = models.IntegerField(verbose_name="Nombre de jours")
    motif = models.TextField(blank=True, verbose_name="Motif")
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut",
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='conges_valides',
        verbose_name="Validé par",
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de validation")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Congé"
        verbose_name_plural = "Congés"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.numero} — {self.employe.nom_complet}"


class SoldeConge(BaseModel):
    """Solde de congés annuel par employé."""

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='soldes_conges',
        verbose_name="Employé",
    )
    annee = models.IntegerField(verbose_name="Année")
    solde_initial = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Solde initial",
    )
    jours_acquis = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Jours acquis",
    )
    jours_pris = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Jours pris",
    )
    solde_restant = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Solde restant",
    )

    class Meta:
        verbose_name = "Solde de congés"
        verbose_name_plural = "Soldes de congés"
        unique_together = ['employe', 'annee']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.annee} ({self.solde_restant} j)"


# ============================================================
# ABSENCES
# ============================================================

class Absence(BaseModel):
    """Absences non liées aux congés."""

    TYPE_CHOICES = [
        ('maladie', 'Maladie'),
        ('injustifiee', 'Non justifiée'),
        ('autorisee', 'Autorisée'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ]

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='absences',
        verbose_name="Employé",
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    motif = models.TextField(blank=True, verbose_name="Motif")
    justificatif = models.FileField(
        upload_to='absences/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif",
    )
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut",
    )

    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.date_debut}"


# ============================================================
# ÉVALUATIONS
# ============================================================

class Evaluation(BaseModel):
    """Évaluations de performance."""

    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="Employé évalué",
    )
    evaluateur = models.ForeignKey(
        Employe,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='evaluations_faites',
        verbose_name="Évaluateur",
    )
    date_evaluation = models.DateField(verbose_name="Date d'évaluation")
    periode = models.CharField(max_length=30, verbose_name="Période")
    note_globale = models.DecimalField(
        max_digits=4, decimal_places=2,
        verbose_name="Note globale (/20)",
    )
    points_forts = models.TextField(blank=True, verbose_name="Points forts")
    points_ameliorer = models.TextField(
        blank=True, verbose_name="Points à améliorer")
    objectifs = models.TextField(blank=True, verbose_name="Objectifs")

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date_evaluation']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.periode}"


# ============================================================
# FORMATIONS
# ============================================================

class Formation(BaseModel):
    """Formations suivies par les employés."""

    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    formateur = models.CharField(
        max_length=200, blank=True, verbose_name="Formateur")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    lieu = models.CharField(max_length=200, blank=True, verbose_name="Lieu")
    cout = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Coût (GNF)",
    )
    participants = models.ManyToManyField(
        Employe,
        blank=True,
        related_name='formations',
        verbose_name="Participants",
    )

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-date_debut']

    def __str__(self):
        return self.titre
