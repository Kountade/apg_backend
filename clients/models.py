# clients/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


# ============================================================
# TYPE DE CONTRAT (référentiel centralisé)
# ============================================================

class TypeContrat(BaseModel):
    """
    Référentiel centralisé des types de contrats.
    Sert à la fois pour les employés et les clients.
    """

    CATEGORIE_CHOICES = [
        ('emploi', 'Contrat de travail'),
        ('client', 'Contrat client / prestation'),
        ('fournisseur', 'Contrat fournisseur'),
        ('partenariat', 'Contrat de partenariat'),
        ('bail', 'Bail / location'),
        ('maintenance', 'Maintenance'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('archive', 'Archivé'),
    ]

    # ✅ CODE AUTO-GÉNÉRÉ : TCT-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code",
        help_text="Généré automatiquement au format TCT-YYYY-NNNNNN"
    )

    titre = models.CharField(
        max_length=200, verbose_name="Titre du contrat",
        help_text="Ex : Contrat de travail à durée indéterminée"
    )
    categorie = models.CharField(
        max_length=30, choices=CATEGORIE_CHOICES, default='emploi',
        verbose_name="Catégorie"
    )
    description = models.TextField(
        verbose_name="Description / Contenu type",
        help_text="Texte complet du contrat (modèle réutilisable)"
    )

    # Contenu du contrat (peut être un modèle réutilisable)
    contenu = models.TextField(
        blank=True, verbose_name="Corps du contrat",
        help_text="Texte complet du contrat qui sera repris comme base"
    )

    # Durée par défaut
    duree_mois = models.IntegerField(
        null=True, blank=True,
        verbose_name="Durée par défaut (mois)",
        help_text="Laisser vide pour durée indéterminée"
    )

    # Période d'essai
    periode_essai_jours = models.IntegerField(
        null=True, blank=True,
        verbose_name="Période d'essai (jours)"
    )

    # Préavis
    preavis_jours = models.IntegerField(
        default=30, verbose_name="Préavis (jours)"
    )

    # Références légales
    reference_legale = models.CharField(
        max_length=200, blank=True,
        verbose_name="Référence légale",
        help_text="Ex : Article L.1221-2 du Code du travail"
    )

    # Fichier modèle (PDF, DOCX)
    fichier_modele = models.FileField(
        upload_to='contrats/types/%Y/', null=True, blank=True,
        verbose_name="Fichier modèle (PDF/DOCX)"
    )

    # Statut
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif',
        verbose_name="Statut"
    )

    ordre = models.IntegerField(
        default=0, verbose_name="Ordre d'affichage"
    )

    notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        verbose_name = "Type de contrat"
        verbose_name_plural = "Types de contrats"
        ordering = ['categorie', 'ordre', 'titre']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['categorie', 'statut']),
        ]

    def __str__(self):
        return f"{self.code} — {self.titre}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique TCT-YYYY-NNNNNN."""
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"TCT-{year}-"

        dernier = TypeContrat.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"

    @staticmethod
    def proposer_code():
        """Retourne le prochain code SANS l'enregistrer (pour le formulaire)."""
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"TCT-{year}-"

        dernier = TypeContrat.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"


# ============================================================
# CLIENT
# ============================================================

class Client(SoftDeleteModel):
    """Client d'APG : particulier, entreprise, administration, ONG, etc."""

    TYPE_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('administration', 'Administration'),
        ('ong', 'ONG'),
        ('collectivite', 'Collectivité'),
        ('commerce', 'Commerce'),
        ('hotel', 'Hôtel'),
        ('ecole', 'Établissement scolaire'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
        ('archive', 'Archivé'),
    ]

    # ✅ CODE AUTO-GÉNÉRÉ : CLI-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code client",
        help_text="Généré automatiquement au format CLI-YYYY-NNNNNN"
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES,
                            default='particulier', verbose_name="Type")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif', verbose_name="Statut")

    # Identité
    nom = models.CharField(max_length=200, verbose_name="Nom / Raison sociale")
    prenom = models.CharField(
        max_length=150, blank=True, verbose_name="Prénom")
    sigle = models.CharField(max_length=50, blank=True, verbose_name="Sigle")
    sexe = models.CharField(
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        blank=True, verbose_name="Sexe"
    )

    # Contact
    telephone = models.CharField(max_length=30, verbose_name="Téléphone")
    telephone2 = models.CharField(
        max_length=30, blank=True, verbose_name="Téléphone 2")
    email = models.EmailField(blank=True, verbose_name="Email")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    quartier = models.CharField(
        max_length=100, blank=True, verbose_name="Quartier")
    zone = models.CharField(max_length=100, blank=True,
                            verbose_name="Zone de collecte")

    # Légal
    num_contribuable = models.CharField(
        max_length=50, blank=True, verbose_name="N° Contribuable")
    num_rccm = models.CharField(
        max_length=50, blank=True, verbose_name="N° RCCM")

    # Contact entreprise
    contact_nom = models.CharField(
        max_length=150, blank=True, verbose_name="Nom du contact")
    contact_fonction = models.CharField(
        max_length=100, blank=True, verbose_name="Fonction du contact")
    contact_telephone = models.CharField(
        max_length=30, blank=True, verbose_name="Téléphone contact")

    # Portail client (futur)
    compte_utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='client_profile',
        verbose_name="Compte portail client",
    )

    # GPS
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Longitude")

    # Média & notes
    photo = models.ImageField(
        upload_to='clients/', null=True, blank=True, verbose_name="Photo / Logo")
    notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type', 'statut']),
            models.Index(fields=['zone']),
        ]

    def __str__(self):
        return f"{self.code} — {self.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"CLI-{year}-"

        dernier = Client.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"

    @property
    def nom_complet(self):
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom

    @property
    def solde_du(self):
        return 0

    @property
    def total_facture(self):
        return 0

    @property
    def total_paye(self):
        return 0


# ============================================================
# CONTRAT CLIENT
# ============================================================

class ContratClient(BaseModel):
    """Contrat de prestation entre APG et un client."""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('expire', 'Expiré'),
        ('resilie', 'Résilié'),
        ('archive', 'Archivé'),
    ]

    FREQUENCE_CHOICES = [
        ('quotidien', 'Quotidien'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('bimensuel', 'Bimensuel'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
        ('ponctuel', 'Ponctuel'),
    ]

    PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
    ]

    # ✅ NUMÉRO AUTO-GÉNÉRÉ : CTR-YYYY-NNNNNN
    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format CTR-YYYY-NNNNNN"
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='contrats', verbose_name="Client")

    # ✅ NOUVEAU : lien vers le référentiel des types de contrats
    type_contrat = models.ForeignKey(
        'clients.TypeContrat',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='contrats_clients',
        verbose_name="Type de contrat",
        help_text="Modèle de contrat utilisé (pré-remplit le contenu)"
    )

    prestation = models.CharField(max_length=200, verbose_name="Prestation")
    description = models.TextField(blank=True, verbose_name="Description")
    frequence = models.CharField(
        max_length=30, choices=FREQUENCE_CHOICES, default='mensuel', verbose_name="Fréquence")
    zone = models.CharField(max_length=100, blank=True, verbose_name="Zone")

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True, blank=True, verbose_name="Date de fin")
    reconduction_tacite = models.BooleanField(
        default=False, verbose_name="Reconduction tacite")
    jours_preavis = models.IntegerField(
        default=30, verbose_name="Jours de préavis")

    tarif = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Tarif (GNF)")
    tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="TVA (%)")
    modalite_paiement = models.CharField(
        max_length=30, choices=PAIEMENT_CHOICES, default='especes', verbose_name="Modalité")

    equipe = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='contrats_affectes',
        verbose_name="Équipe / Superviseur",
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='contrats_clients_valides',
        verbose_name="Validé par",
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date validation")

    document = models.FileField(
        upload_to='contrats_clients/', null=True, blank=True, verbose_name="Contrat signé")
    conditions_particulieres = models.TextField(
        blank=True, verbose_name="Conditions particulières")

    class Meta:
        verbose_name = "Contrat client"
        verbose_name_plural = "Contrats clients"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['client', 'statut']),
            models.Index(fields=['date_fin']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.client.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"CTR-{year}-"

        dernier = ContratClient.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"

    @staticmethod
    def proposer_numero():
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"CTR-{year}-"

        dernier = ContratClient.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"

    @property
    def est_actif(self):
        from datetime import date
        today = date.today()
        if self.statut != 'actif':
            return False
        if self.date_debut and self.date_debut > today:
            return False
        if self.date_fin and self.date_fin < today:
            return False
        return True

    @property
    def est_expire(self):
        from datetime import date
        return self.date_fin and self.date_fin < date.today()

    @property
    def jours_avant_expiration(self):
        from datetime import date
        if not self.date_fin:
            return None
        return (self.date_fin - date.today()).days

    @property
    def montant_ttc(self):
        return self.tarif + (self.tarif * self.tva / 100)


# ============================================================
# PRESTATION
# ============================================================

class Prestation(BaseModel):
    """Catalogue des prestations APG."""

    # ✅ CODE AUTO-GÉNÉRÉ : PRE-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code",
        help_text="Généré automatiquement au format PRE-YYYY-NNNNNN"
    )
    nom = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    tarif_base = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Tarif de base (GNF)")
    unite = models.CharField(max_length=50, blank=True, verbose_name="Unité")
    actif = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"PRE-{year}-"

        dernier = Prestation.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"

    @staticmethod
    def proposer_code():
        from django.utils import timezone
        from django.db.models import Max

        year = timezone.now().year
        prefixe = f"PRE-{year}-"

        dernier = Prestation.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']

        if dernier:
            try:
                numero = int(dernier.split('-')[-1])
                nouveau_numero = numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1

        return f"{prefixe}{nouveau_numero:06d}"


# ============================================================
# RELANCE
# ============================================================

class Relance(BaseModel):
    """Historique des relances clients pour impayés."""

    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('appel', 'Appel téléphonique'),
        ('courrier', 'Courrier'),
        ('visite', 'Visite sur site'),
    ]

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='relances', verbose_name="Client")

    facture_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence facture"
    )

    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    date_relance = models.DateField(auto_now_add=True, verbose_name="Date")
    message = models.TextField(blank=True, verbose_name="Message")
    montant_reclame = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Montant réclamé")
    reponse_client = models.TextField(
        blank=True, verbose_name="Réponse client")
    prochaine_relance = models.DateField(
        null=True, blank=True, verbose_name="Prochaine relance")

    class Meta:
        verbose_name = "Relance"
        verbose_name_plural = "Relances"
        ordering = ['-date_relance']

    def __str__(self):
        return f"{self.client.nom_complet} — {self.get_type_display()} ({self.date_relance})"
