# vehicules/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel


# ============================================================
# TRICYCLE (Module 15) — avec lien stocks.Equipement
# ============================================================

class Tricycle(SoftDeleteModel):
    """
    Tricycles de collecte APG.
    
    🔗 Lien vers stocks.Equipement (optionnel) : permet de relier le PARC ROULANT
    au BIEN PHYSIQUE (coût, amortissement, état comptable).
    """

    ETAT_CHOICES = [
        ('disponible', 'Disponible'),
        ('en_mission', 'En mission'),
        ('en_maintenance', 'En maintenance'),
        ('en_panne', 'En panne'),
        ('hors_service', 'Hors service'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('vendu', 'Vendu'),
        ('reforme', 'Réformé'),
        ('archive', 'Archivé'),
    ]

    # 🔗 LIEN VERS STOCKS (le bien physique)
    equipement = models.OneToOneField(
        'stocks.Equipement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tricycle_lie',
        verbose_name="Équipement lié (stocks)",
        help_text="Le bien physique correspondant dans stocks.Equipement"
    )

    numero_interne = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro interne")
    immatriculation = models.CharField(
        max_length=50, blank=True, verbose_name="Immatriculation")
    marque = models.CharField(
        max_length=100, blank=True, verbose_name="Marque")
    modele = models.CharField(
        max_length=100, blank=True, verbose_name="Modèle")
    annee = models.IntegerField(null=True, blank=True, verbose_name="Année")
    numero_chassis = models.CharField(
        max_length=100, blank=True, verbose_name="N° de châssis")
    numero_moteur = models.CharField(
        max_length=100, blank=True, verbose_name="N° de moteur")

    date_acquisition = models.DateField(
        null=True, blank=True, verbose_name="Date d'acquisition")
    cout_acquisition = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Coût d'acquisition (GNF)")

    capacite_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Capacité (kg)")
    kilometrage_actuel = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Kilométrage")

    # Suivi vidange
    date_derniere_vidange = models.DateField(
        null=True, blank=True, verbose_name="Date dernière vidange")
    km_derniere_vidange = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Km à la dernière vidange")
    intervalle_vidange_km = models.IntegerField(
        default=5000, verbose_name="Intervalle vidange (km)")

    etat = models.CharField(
        max_length=20, choices=ETAT_CHOICES, default='disponible',
        verbose_name="État")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif',
        verbose_name="Statut administratif")

    conducteur_affecte = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tricycles_affectes',
        verbose_name="Conducteur affecté",
    )
    zone_exploitation = models.CharField(
        max_length=100, blank=True, verbose_name="Zone d'exploitation")

    photo = models.ImageField(
        upload_to='tricycles/', null=True, blank=True,
        verbose_name="Photo")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Tricycle"
        verbose_name_plural = "Tricycles"
        ordering = ['numero_interne']
        indexes = [
            models.Index(fields=['numero_interne']),
            models.Index(fields=['etat']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.numero_interne} — {self.marque} {self.modele}"

    # ✅ Propriétés dérivées de stocks (pas de duplication)
    @property
    def valeur_actuelle(self):
        return self.equipement.valeur_actuelle if self.equipement else self.cout_acquisition

    @property
    def cout_acquisition_stocks(self):
        return self.equipement.cout_acquisition if self.equipement else self.cout_acquisition

    @property
    def etat_stocks(self):
        return self.equipement.etat if self.equipement else None

    @property
    def categorie_nom(self):
        return self.equipement.categorie.nom if self.equipement and self.equipement.categorie else None

    # Vidange
    @property
    def kilometrage_depuis_vidange(self):
        return float(self.kilometrage_actuel) - float(self.km_derniere_vidange)

    @property
    def vidange_a_faire(self):
        return self.kilometrage_depuis_vidange >= self.intervalle_vidange_km

    # Documents (raccourcis vers le dernier de chaque type)
    @property
    def date_expiration_assurance(self):
        doc = self.assurances.order_by('-date_fin').first()
        return doc.date_fin if doc else None

    @property
    def est_assurance_valide(self):
        from datetime import date
        if not self.date_expiration_assurance:
            return False
        return self.date_expiration_assurance >= date.today()

    # ✅ Proposer numéro auto
    @staticmethod
    def proposer_numero_interne():
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"TRI-{year}-"
        dernier = Tricycle.objects.filter(
            numero_interne__startswith=prefixe
        ).aggregate(max_num=Max('numero_interne'))['max_num']
        if dernier:
            try:
                nouveau = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau = 1
        else:
            nouveau = 1
        return f"{prefixe}{nouveau:06d}"


# ============================================================
# VÉHICULE (Module 15) — avec lien stocks.Equipement
# ============================================================

class Vehicule(SoftDeleteModel):
    """Véhicules (camions, bennes, 4x4...)."""

    TYPE_CHOICES = [
        ('camion', 'Camion'),
        ('benne', 'Camion benne'),
        ('pickup', 'Pick-up'),
        ('4x4', '4x4'),
        ('voiture', 'Voiture'),
        ('autre', 'Autre'),
    ]

    ETAT_CHOICES = Tricycle.ETAT_CHOICES
    STATUT_CHOICES = Tricycle.STATUT_CHOICES

    # 🔗 LIEN VERS STOCKS
    equipement = models.OneToOneField(
        'stocks.Equipement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vehicule_lie',
        verbose_name="Équipement lié (stocks)",
        help_text="Le bien physique correspondant dans stocks.Equipement"
    )

    numero_interne = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro interne")
    immatriculation = models.CharField(
        max_length=50, blank=True, verbose_name="Immatriculation")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='camion',
        verbose_name="Type")
    marque = models.CharField(
        max_length=100, blank=True, verbose_name="Marque")
    modele = models.CharField(
        max_length=100, blank=True, verbose_name="Modèle")
    annee = models.IntegerField(null=True, blank=True, verbose_name="Année")
    numero_chassis = models.CharField(
        max_length=100, blank=True, verbose_name="N° de châssis")
    numero_moteur = models.CharField(
        max_length=100, blank=True, verbose_name="N° de moteur")

    date_acquisition = models.DateField(
        null=True, blank=True, verbose_name="Date d'acquisition")
    cout_acquisition = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Coût d'acquisition")

    capacite_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Capacité (kg)")
    kilometrage_actuel = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Kilométrage")

    # Suivi vidange
    date_derniere_vidange = models.DateField(
        null=True, blank=True, verbose_name="Date dernière vidange")
    km_derniere_vidange = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Km à la dernière vidange")
    intervalle_vidange_km = models.IntegerField(
        default=5000, verbose_name="Intervalle vidange (km)")

    etat = models.CharField(
        max_length=20, choices=ETAT_CHOICES, default='disponible',
        verbose_name="État")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif',
        verbose_name="Statut administratif")

    conducteur_affecte = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='vehicules_affectes',
        verbose_name="Conducteur affecté",
    )
    zone_exploitation = models.CharField(
        max_length=100, blank=True, verbose_name="Zone d'exploitation")

    photo = models.ImageField(
        upload_to='vehicules/', null=True, blank=True, verbose_name="Photo")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['numero_interne']
        indexes = [
            models.Index(fields=['numero_interne']),
            models.Index(fields=['etat']),
            models.Index(fields=['type']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.numero_interne} — {self.get_type_display()} {self.marque}"

    # ✅ Propriétés dérivées de stocks
    @property
    def valeur_actuelle(self):
        return self.equipement.valeur_actuelle if self.equipement else self.cout_acquisition

    @property
    def cout_acquisition_stocks(self):
        return self.equipement.cout_acquisition if self.equipement else self.cout_acquisition

    @property
    def etat_stocks(self):
        return self.equipement.etat if self.equipement else None

    @property
    def categorie_nom(self):
        return self.equipement.categorie.nom if self.equipement and self.equipement.categorie else None

    # Vidange
    @property
    def kilometrage_depuis_vidange(self):
        return float(self.kilometrage_actuel) - float(self.km_derniere_vidange)

    @property
    def vidange_a_faire(self):
        return self.kilometrage_depuis_vidange >= self.intervalle_vidange_km

    # Documents
    @property
    def date_expiration_assurance(self):
        doc = self.assurances.order_by('-date_fin').first()
        return doc.date_fin if doc else None

    @property
    def est_assurance_valide(self):
        from datetime import date
        if not self.date_expiration_assurance:
            return False
        return self.date_expiration_assurance >= date.today()

    @staticmethod
    def proposer_numero_interne():
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"VEH-{year}-"
        dernier = Vehicule.objects.filter(
            numero_interne__startswith=prefixe
        ).aggregate(max_num=Max('numero_interne'))['max_num']
        if dernier:
            try:
                nouveau = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau = 1
        else:
            nouveau = 1
        return f"{prefixe}{nouveau:06d}"


# ============================================================
# CONDUCTEUR
# ============================================================

class Conducteur(BaseModel):
    """Conducteurs (chauffeurs, pilotes de tricycle)."""

    employe = models.OneToOneField(
        'rh.Employe',
        on_delete=models.CASCADE,
        related_name='conducteur_profile',
        verbose_name="Employé",
    )
    numero_permis = models.CharField(
        max_length=50, blank=True, verbose_name="N° de permis")
    categorie_permis = models.CharField(
        max_length=10, blank=True, verbose_name="Catégorie permis")
    date_expiration_permis = models.DateField(
        null=True, blank=True, verbose_name="Expiration permis")
    annees_experience = models.IntegerField(
        default=0, verbose_name="Années d'expérience")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        ordering = ['employe__nom']

    def __str__(self):
        return f"{self.employe.nom_complet} — {self.numero_permis or 'Sans permis'}"

    @property
    def permis_valide(self):
        from datetime import date
        if not self.date_expiration_permis:
            return False
        return self.date_expiration_permis >= date.today()

    @property
    def jours_avant_expiration_permis(self):
        from datetime import date
        if not self.date_expiration_permis:
            return None
        return (self.date_expiration_permis - date.today()).days


# ============================================================
# AFFECTATION VÉHICULE
# ============================================================

class AffectationVehicule(BaseModel):
    """Affectation d'un véhicule/tricycle à un conducteur ou une mission."""

    tricycle = models.ForeignKey(
        Tricycle, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='affectations', verbose_name="Tricycle")
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='affectations', verbose_name="Véhicule")
    conducteur = models.ForeignKey(
        Conducteur, on_delete=models.PROTECT,
        related_name='affectations', verbose_name="Conducteur")

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True, blank=True, verbose_name="Date de fin")

    zone = models.CharField(max_length=100, blank=True, verbose_name="Zone")
    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Affectation véhicule"
        verbose_name_plural = "Affectations véhicules"
        ordering = ['-date_debut']

    def __str__(self):
        engin = self.tricycle or self.vehicule
        return f"{engin} → {self.conducteur}"

    @property
    def est_en_cours(self):
        return self.date_fin is None


# ============================================================
# DOCUMENT VÉHICULE
# ============================================================

class DocumentVehicule(BaseModel):
    """Documents attachés à un véhicule (carte grise, assurance, visite technique)."""

    TYPE_CHOICES = [
        ('carte_grise', 'Carte grise'),
        ('assurance', 'Assurance'),
        ('visite_technique', 'Visite technique'),
        ('permis', 'Permis de conduire'),
        ('autre', 'Autre'),
    ]

    tricycle = models.ForeignKey(
        Tricycle, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='documents', verbose_name="Tricycle")
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='documents', verbose_name="Véhicule")

    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    numero = models.CharField(
        max_length=100, blank=True, verbose_name="Numéro du document")
    date_emission = models.DateField(
        null=True, blank=True, verbose_name="Date d'émission")
    date_expiration = models.DateField(
        null=True, blank=True, verbose_name="Date d'expiration")
    organisme = models.CharField(
        max_length=200, blank=True, verbose_name="Organisme émetteur")
    montant = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Montant (GNF)")

    fichier = models.FileField(
        upload_to='documents_vehicules/%Y/', null=True, blank=True,
        verbose_name="Fichier")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Document véhicule"
        verbose_name_plural = "Documents véhicules"
        ordering = ['-date_expiration']
        indexes = [
            models.Index(fields=['date_expiration']),
        ]

    def __str__(self):
        engin = self.tricycle or self.vehicule
        return f"{engin} — {self.get_type_display()}"

    @property
    def est_expire(self):
        from datetime import date
        return self.date_expiration and self.date_expiration < date.today()

    @property
    def jours_avant_expiration(self):
        from datetime import date
        if not self.date_expiration:
            return None
        return (self.date_expiration - date.today()).days


# ============================================================
# ASSURANCE
# ============================================================

class Assurance(BaseModel):
    """Assurances véhicules."""

    tricycle = models.ForeignKey(
        Tricycle, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='assurances', verbose_name="Tricycle")
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='assurances', verbose_name="Véhicule")

    compagnie = models.CharField(
        max_length=200, verbose_name="Compagnie d'assurance")
    numero_police = models.CharField(
        max_length=100, verbose_name="Numéro de police")
    type_couverture = models.CharField(
        max_length=100, blank=True, verbose_name="Type de couverture")
    prime_annuelle = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prime annuelle (GNF)")

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")

    fichier = models.FileField(
        upload_to='assurances/%Y/', null=True, blank=True,
        verbose_name="Attestation")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Assurance"
        verbose_name_plural = "Assurances"
        ordering = ['-date_fin']
        indexes = [
            models.Index(fields=['date_fin']),
        ]

    def __str__(self):
        engin = self.tricycle or self.vehicule
        return f"{engin} — {self.compagnie}"

    @property
    def est_expire(self):
        from datetime import date
        return self.date_fin < date.today()

    @property
    def jours_avant_expiration(self):
        from datetime import date
        return (self.date_fin - date.today()).days


# ============================================================
# SUIVI GPS
# ============================================================

class SuiviGPS(BaseModel):
    """Positions GPS des véhicules/tricycles."""

    tricycle = models.ForeignKey(
        Tricycle, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='positions_gps', verbose_name="Tricycle")
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='positions_gps', verbose_name="Véhicule")

    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, verbose_name="Latitude")
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, verbose_name="Longitude")
    vitesse = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Vitesse (km/h)")
    cap = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Cap (degrés)")

    date_position = models.DateTimeField(verbose_name="Date de position")
    adresse = models.CharField(
        max_length=300, blank=True, verbose_name="Adresse approximative")

    class Meta:
        verbose_name = "Suivi GPS"
        verbose_name_plural = "Suivis GPS"
        ordering = ['-date_position']
        indexes = [
            models.Index(fields=['date_position']),
        ]

    def __str__(self):
        engin = self.tricycle or self.vehicule
        return f"{engin} — {self.date_position:%Y-%m-%d %H:%M}"


# ============================================================
# ✅ NOUVEAU — PLEIN CARBURANT
# ============================================================

class PleinCarburant(BaseModel):
    """Plein de carburant d'un véhicule ou tricycle."""

    TYPE_CHOICES = [
        ('essence', 'Essence'),
        ('gasoil', 'Gasoil'),
        ('huile', 'Huile'),
    ]

    tricycle = models.ForeignKey(
        Tricycle, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='pleins', verbose_name="Tricycle")
    vehicule = models.ForeignKey(
        Vehicule, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='pleins', verbose_name="Véhicule")

    date = models.DateField(verbose_name="Date du plein")
    type_carburant = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='essence',
        verbose_name="Type de carburant")

    litres = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Litres")
    prix_litre = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Prix au litre (GNF)")
    montant = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Montant total (GNF)")

    km_compteur = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Kilométrage au compteur")

    station = models.CharField(
        max_length=200, blank=True, verbose_name="Station-service")
    conducteur = models.ForeignKey(
        'rh.Employe', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pleins_effectues',
        verbose_name="Conducteur")
    justificatif = models.FileField(
        upload_to='carburant/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Plein carburant"
        verbose_name_plural = "Pleins carburant"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        engin = self.tricycle or self.vehicule
        return f"{engin} — {self.litres}L le {self.date}"

    def save(self, *args, **kwargs):
        # Calcul auto du montant
        self.montant = float(self.litres) * float(self.prix_litre)
        super().save(*args, **kwargs)

    @property
    def engin(self):
        return self.tricycle or self.vehicule

    @property
    def consommation(self):
        """Consommation L/100km calculée depuis le plein précédent."""
        if self.tricycle:
            dernier = PleinCarburant.objects.filter(
                tricycle=self.tricycle,
                km_compteur__lt=self.km_compteur,
            ).exclude(pk=self.pk).order_by('-km_compteur').first()
        elif self.vehicule:
            dernier = PleinCarburant.objects.filter(
                vehicule=self.vehicule,
                km_compteur__lt=self.km_compteur,
            ).exclude(pk=self.pk).order_by('-km_compteur').first()
        else:
            return None
        if not dernier:
            return None
        km = float(self.km_compteur) - float(dernier.km_compteur)
        if km <= 0:
            return None
        return round(float(self.litres) / km * 100, 2)

    @property
    def distance_parcourue(self):
        """Distance depuis le plein précédent."""
        if self.tricycle:
            dernier = PleinCarburant.objects.filter(
                tricycle=self.tricycle,
                km_compteur__lt=self.km_compteur,
            ).exclude(pk=self.pk).order_by('-km_compteur').first()
        elif self.vehicule:
            dernier = PleinCarburant.objects.filter(
                vehicule=self.vehicule,
                km_compteur__lt=self.km_compteur,
            ).exclude(pk=self.pk).order_by('-km_compteur').first()
        else:
            return None
        if not dernier:
            return None
        return float(self.km_compteur) - float(dernier.km_compteur)