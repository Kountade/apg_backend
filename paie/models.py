from django.db import models

# Create your models here.
# paie/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, NumeroAutoMixin


# ============================================================
# PÉRIODE DE PAIE (Module 8)
# ============================================================

class PeriodePaie(BaseModel):
    """Période de paie mensuelle."""

    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('en_preparation', 'En préparation'),
        ('calculee', 'Calculée'),
        ('controlee', 'Contrôlée'),
        ('validee', 'Validée'),
        ('en_attente_paiement', 'En attente de paiement'),
        ('payee', 'Payée'),
        ('cloturee', 'Clôturée'),
        ('annulee', 'Annulée'),
    ]

    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    libelle = models.CharField(
        max_length=100, blank=True, verbose_name="Libellé")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    date_paiement_prevue = models.DateField(
        null=True, blank=True, verbose_name="Date de paiement prévue")

    statut = models.CharField(
        max_length=30, choices=STATUT_CHOICES, default='ouverte', verbose_name="Statut")

    # Totaux
    nombre_employes = models.IntegerField(
        default=0, verbose_name="Nombre d'employés")
    total_brut = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="Total brut")
    total_retenues = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="Total retenues")
    total_net = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="Total net")
    total_cnss = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="Total CNSS")

    # Workflow
    preparee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='periodes_paie_preparees',
        verbose_name="Préparée par",
    )
    controlee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='periodes_paie_controlees',
        verbose_name="Contrôlée par",
    )
    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='periodes_paie_validees',
        verbose_name="Validée par",
    )
    payee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='periodes_paie_payees',
        verbose_name="Payée par",
    )

    date_controle = models.DateTimeField(
        null=True, blank=True, verbose_name="Date contrôle")
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date validation")
    date_paiement = models.DateTimeField(
        null=True, blank=True, verbose_name="Date paiement")

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Période de paie"
        verbose_name_plural = "Périodes de paie"
        unique_together = ['mois', 'annee']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Paie {self.mois:02d}/{self.annee} — {self.get_statut_display()}"

    def recalculer_totaux(self):
        """Recalcule les totaux depuis les bulletins."""
        from django.db.models import Sum
        bulletins = self.bulletins.all()
        self.nombre_employes = bulletins.count()
        self.total_brut = bulletins.aggregate(t=Sum('salaire_brut'))['t'] or 0
        self.total_retenues = bulletins.aggregate(
            t=Sum('total_retenues'))['t'] or 0
        self.total_net = bulletins.aggregate(t=Sum('salaire_net'))['t'] or 0
        self.total_cnss = bulletins.aggregate(t=Sum('cnss_salarial'))['t'] or 0
        self.save(update_fields=[
                  'nombre_employes', 'total_brut', 'total_retenues', 'total_net', 'total_cnss'])


# ============================================================
# BULLETIN DE PAIE (Module 8)
# ============================================================

class BulletinPaie(BaseModel, NumeroAutoMixin):
    """Bulletin de paie individuel."""

    PREFIX = 'BUL'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('calcule', 'Calculé'),
        ('controle', 'Contrôlé'),
        ('valide', 'Validé'),
        ('en_attente_paiement', 'En attente de paiement'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
    periode = models.ForeignKey(
        PeriodePaie, on_delete=models.CASCADE, related_name='bulletins', verbose_name="Période")
    employe = models.ForeignKey('rh.Employe', on_delete=models.PROTECT,
                                related_name='bulletins_paie', verbose_name="Employé")

    # Snapshot des infos employé (pour archivage)
    matricule_snapshot = models.CharField(
        max_length=20, blank=True, verbose_name="Matricule")
    nom_snapshot = models.CharField(
        max_length=200, blank=True, verbose_name="Nom")
    poste_snapshot = models.CharField(
        max_length=200, blank=True, verbose_name="Poste")
    departement_snapshot = models.CharField(
        max_length=200, blank=True, verbose_name="Département")

    # Éléments de base
    salaire_base = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Salaire de base")
    jours_travailles = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name="Jours travaillés")
    jours_theoriques = models.DecimalField(
        max_digits=6, decimal_places=2, default=0, verbose_name="Jours théoriques")

    # Primes et indemnités
    total_primes = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total primes")
    total_indemnites = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total indemnités")
    heures_supplementaires = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Heures sup.")
    montant_heures_sup = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant heures sup.")

    # Salaire brut
    salaire_brut = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Salaire brut")

    # Retenues
    cnss_salarial = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="CNSS salarial")
    impot_revenu = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Impôt sur revenu")
    avances_deduites = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Avances déduites")
    autres_retenues = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Autres retenues")
    total_retenues = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total retenues")

    # Charges patronales
    cnss_patronal = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="CNSS patronal")

    # Net à payer
    salaire_net = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Salaire net")

    # Statut
    statut = models.CharField(
        max_length=30, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")

    # Paiement
    date_paiement = models.DateField(
        null=True, blank=True, verbose_name="Date de paiement")
    mode_paiement = models.CharField(
        max_length=30,
        choices=[
            ('especes', 'Espèces'),
            ('virement', 'Virement'),
            ('mobile_money', 'Mobile Money'),
            ('cheque', 'Chèque'),
        ],
        default='especes',
        verbose_name="Mode de paiement",
    )
    decaissement = models.ForeignKey(
        'tresorerie.Decaissement',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bulletins_paie',
        verbose_name="Décaissement lié",
    )

    # Document
    document_pdf = models.FileField(
        upload_to='bulletins/%Y/%m/', null=True, blank=True, verbose_name="Bulletin PDF")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Bulletin de paie"
        verbose_name_plural = "Bulletins de paie"
        unique_together = ['periode', 'employe']
        ordering = ['-periode__annee', '-periode__mois', 'employe__nom']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['statut']),
            models.Index(fields=['employe', 'periode']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.employe.nom_complet}"

    def calculer(self):
        """Calcule tous les totaux du bulletin."""
        # Salaire brut = base + primes + indemnités + heures sup
        self.salaire_brut = (
            self.salaire_base
            + self.total_primes
            + self.total_indemnites
            + self.montant_heures_sup
        )

        # Retenues
        self.total_retenues = (
            self.cnss_salarial
            + self.impot_revenu
            + self.avances_deduites
            + self.autres_retenues
        )

        # Net à payer
        self.salaire_net = self.salaire_brut - self.total_retenues

        self.save()
        return self.salaire_net

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)


class LigneBulletin(BaseModel):
    """Ligne de détail d'un bulletin (prime, indemnité, retenue)."""

    TYPE_CHOICES = [
        ('prime', 'Prime'),
        ('indemnite', 'Indemnité'),
        ('retenue', 'Retenue'),
        ('avantage', 'Avantage'),
        ('heure_sup', 'Heure supplémentaire'),
    ]

    bulletin = models.ForeignKey(
        BulletinPaie, on_delete=models.CASCADE, related_name='lignes', verbose_name="Bulletin")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    montant = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant")
    imposable = models.BooleanField(default=True, verbose_name="Imposable")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Ligne de bulletin"
        verbose_name_plural = "Lignes de bulletin"
        ordering = ['type', 'ordre']

    def __str__(self):
        return f"{self.libelle} — {self.montant}"


# ============================================================
# PRIME / INDEMNITÉ (référentiel)
# ============================================================

class Prime(BaseModel):
    """Référentiel des primes et indemnités."""

    TYPE_CHOICES = [
        ('prime', 'Prime'),
        ('indemnite', 'Indemnité'),
        ('avantage', 'Avantage en nature'),
    ]

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='prime', verbose_name="Type")
    montant_fixe = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Montant fixe (GNF)")
    pourcentage_salaire = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="% du salaire")
    imposable = models.BooleanField(default=True, verbose_name="Imposable")
    soumis_cnss = models.BooleanField(default=True, verbose_name="Soumis CNSS")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Prime / Indemnité"
        verbose_name_plural = "Primes & Indemnités"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"


# ============================================================
# RETENUE (référentiel)
# ============================================================

class Retenue(BaseModel):
    """Référentiel des retenues."""

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    type = models.CharField(
        max_length=20,
        choices=[
            ('cnss', 'CNSS'),
            ('impot', 'Impôt'),
            ('pret', 'Prêt'),
            ('avance', 'Avance'),
            ('autre', 'Autre'),
        ],
        verbose_name="Type",
    )
    pourcentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="Pourcentage (%)")
    montant_fixe = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Montant fixe")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Retenue"
        verbose_name_plural = "Retenues"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"


# ============================================================
# AVANCE SUR SALAIRE
# ============================================================

class AvanceSalaire(BaseModel, NumeroAutoMixin):
    """Avances sur salaire."""

    PREFIX = 'AVS'

    STATUT_CHOICES = [
        ('demandee', 'Demandée'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('payee', 'Payée'),
        ('remboursee', 'Remboursée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
    employe = models.ForeignKey(
        'rh.Employe', on_delete=models.PROTECT, related_name='avances', verbose_name="Employé")
    date_demande = models.DateField(
        auto_now_add=True, verbose_name="Date de demande")
    montant = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Montant (GNF)")
    motif = models.TextField(blank=True, verbose_name="Motif")
    mois_deduction = models.IntegerField(verbose_name="Mois de déduction")
    annee_deduction = models.IntegerField(verbose_name="Année de déduction")

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='demandee', verbose_name="Statut")

    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='avances_validees',
        verbose_name="Validée par",
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date validation")

    payee = models.BooleanField(default=False, verbose_name="Payée")
    date_paiement = models.DateField(
        null=True, blank=True, verbose_name="Date paiement")

    class Meta:
        verbose_name = "Avance sur salaire"
        verbose_name_plural = "Avances sur salaire"
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.numero} — {self.employe.nom_complet} ({self.montant})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)


# ============================================================
# FICHE DE PAIE (vue agrégée)
# ============================================================

class FichePaie(BaseModel):
    """Fiche de paie consolidée (historique)."""

    employe = models.ForeignKey('rh.Employe', on_delete=models.CASCADE,
                                related_name='fiches_paie', verbose_name="Employé")
    bulletin = models.OneToOneField(
        BulletinPaie, on_delete=models.CASCADE, related_name='fiche', verbose_name="Bulletin")

    annee = models.IntegerField(verbose_name="Année")
    mois = models.IntegerField(verbose_name="Mois")
    salaire_brut = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Salaire brut")
    salaire_net = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Salaire net")

    fichier_pdf = models.FileField(
        upload_to='fiches_paie/%Y/', null=True, blank=True, verbose_name="Fichier PDF")

    class Meta:
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"Fiche {self.mois:02d}/{self.annee} — {self.employe.nom_complet}"
