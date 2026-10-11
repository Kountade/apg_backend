from django.db import models

# Create your models here.
# tresorerie/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel


# ============================================================
# CAISSE (Module 9.3)
# ============================================================

class Caisse(BaseModel):
    """Caisse physique ou virtuelle."""

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=100, verbose_name="Nom de la caisse")
    responsable = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='caisses_gerees',
        verbose_name="Responsable",
    )
    devise = models.CharField(max_length=10, default='GNF', verbose_name="Devise")
    solde_initial = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Solde initial")
    solde_theorique = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Solde théorique")
    solde_physique = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Solde physique")
    actif = models.BooleanField(default=True, verbose_name="Active")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Caisse"
        verbose_name_plural = "Caisses"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.nom}"

    @property
    def difference(self):
        return self.solde_physique - self.solde_theorique

    def calculer_solde(self):
        """Recalcule le solde théorique à partir des mouvements."""
        from django.db.models import Sum
        entrees = self.mouvements.filter(type='entree').aggregate(t=Sum('montant'))['t'] or 0
        sorties = self.mouvements.filter(type='sortie').aggregate(t=Sum('montant'))['t'] or 0
        self.solde_theorique = self.solde_initial + entrees - sorties
        self.save(update_fields=['solde_theorique'])
        return self.solde_theorique


# ============================================================
# COMPTE BANCAIRE (Module 9.4)
# ============================================================

class CompteBancaire(BaseModel):
    """Comptes bancaires et mobile money."""

    TYPE_CHOICES = [
        ('banque', 'Compte bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('caisse_populaire', 'Caisse populaire'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=100, verbose_name="Nom du compte")
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='banque', verbose_name="Type")
    banque = models.CharField(max_length=100, blank=True, verbose_name="Banque / Opérateur")
    numero_compte = models.CharField(max_length=50, blank=True, verbose_name="Numéro de compte")
    iban = models.CharField(max_length=50, blank=True, verbose_name="IBAN")
    swift = models.CharField(max_length=20, blank=True, verbose_name="SWIFT")
    titulaire = models.CharField(max_length=200, blank=True, verbose_name="Titulaire")
    devise = models.CharField(max_length=10, default='GNF', verbose_name="Devise")
    solde_initial = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Solde initial")
    solde_actuel = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Solde actuel")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Compte bancaire"
        verbose_name_plural = "Comptes bancaires"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.nom} ({self.get_type_display()})"


# ============================================================
# MOUVEMENT DE TRÉSORERIE (base commune)
# ============================================================

class MouvementTresorerie(BaseModel):
    """Mouvement de trésorerie (base commune encaissement/décaissement)."""

    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
        ('carte', 'Carte bancaire'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format MVT-YYYY-NNNNNN"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    date_mouvement = models.DateField(verbose_name="Date")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant (GNF)")
    mode_paiement = models.CharField(
        max_length=30, choices=MODE_PAIEMENT_CHOICES,
        default='especes', verbose_name="Mode de paiement"
    )

    caisse = models.ForeignKey(
        Caisse, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements',
        verbose_name="Caisse",
    )
    compte_bancaire = models.ForeignKey(
        CompteBancaire, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements',
        verbose_name="Compte bancaire",
    )

    origine = models.CharField(max_length=200, blank=True, verbose_name="Origine / Bénéficiaire")
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    motif = models.TextField(blank=True, verbose_name="Motif")

    module_source = models.CharField(max_length=50, blank=True, verbose_name="Module source")
    object_id = models.CharField(max_length=50, blank=True, verbose_name="ID objet")

    justificatif = models.FileField(
        upload_to='tresorerie/%Y/%m/',
        null=True, blank=True,
        verbose_name="Justificatif"
    )

    class Meta:
        verbose_name = "Mouvement de trésorerie"
        verbose_name_plural = "Mouvements de trésorerie"
        ordering = ['-date_mouvement', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['type', 'date_mouvement']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.get_type_display()} {self.montant} GNF"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"MVT-{year}-"
        dernier = MouvementTresorerie.objects.filter(
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


# ============================================================
# ENCAISSEMENT (Module 9.1)
# ============================================================

class Encaissement(BaseModel):
    """Encaissement client ou recette diverse."""

    TYPE_CHOICES = [
        ('paiement_client', 'Paiement client'),
        ('reglement_facture', 'Règlement facture'),
        ('recette_diverse', 'Recette diverse'),
        ('apport', 'Apport'),
        ('financement', 'Financement'),
        ('remboursement', 'Remboursement reçu'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
        ('carte', 'Carte bancaire'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format ENC-YYYY-NNNNNN"
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    date_encaissement = models.DateField(verbose_name="Date")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant (GNF)")
    mode_paiement = models.CharField(
        max_length=30, choices=MODE_PAIEMENT_CHOICES,
        default='especes', verbose_name="Mode de paiement"
    )

    # Origine
    client = models.ForeignKey(
        'clients.Client',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='encaissements',
        verbose_name="Client",
    )
    facture_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence facture"
    )
    origine = models.CharField(max_length=200, blank=True, verbose_name="Origine / Source")

    # Destination
    caisse = models.ForeignKey(
        Caisse, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='encaissements',
        verbose_name="Caisse",
    )
    compte_bancaire = models.ForeignKey(
        CompteBancaire, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='encaissements',
        verbose_name="Compte bancaire",
    )

    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    motif = models.TextField(blank=True, verbose_name="Motif")
    justificatif = models.FileField(
        upload_to='encaissements/%Y/%m/',
        null=True, blank=True,
        verbose_name="Justificatif"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES,
        default='en_attente', verbose_name="Statut"
    )

    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='encaissements_valides',
        verbose_name="Validé par",
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date validation")

    class Meta:
        verbose_name = "Encaissement"
        verbose_name_plural = "Encaissements"
        ordering = ['-date_encaissement', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['statut', 'date_encaissement']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.montant} GNF"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"ENC-{year}-"
        dernier = Encaissement.objects.filter(
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
        prefixe = f"ENC-{year}-"
        dernier = Encaissement.objects.filter(
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


# ============================================================
# DÉCAISSEMENT (Module 9.2)
# ============================================================

class Decaissement(BaseModel):
    """Décaissement / dépense."""

    TYPE_CHOICES = [
        ('paiement_salaire', 'Paiement salaire'),
        ('paiement_fournisseur', 'Paiement fournisseur'),
        ('carburant', 'Carburant'),
        ('entretien', 'Entretien'),
        ('achat', 'Achat'),
        ('transport', 'Transport'),
        ('charge', 'Charge'),
        ('avance', 'Avance'),
        ('depense_diverse', 'Dépense diverse'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
        ('refuse', 'Refusé'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
        ('carte', 'Carte bancaire'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format DEC-YYYY-NNNNNN"
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name="Type")
    date_demande = models.DateField(auto_now_add=True, verbose_name="Date de demande")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant (GNF)")
    mode_paiement = models.CharField(
        max_length=30, choices=MODE_PAIEMENT_CHOICES,
        default='especes', verbose_name="Mode de paiement"
    )

    # Bénéficiaire
    beneficiaire = models.CharField(max_length=200, blank=True, verbose_name="Bénéficiaire")
    # ✅ TEMPORAIRE : CharField au lieu de FK vers achats.Fournisseur
    fournisseur_reference = models.CharField(
        max_length=200, blank=True,
        verbose_name="Référence fournisseur"
    )

    # Source de fonds
    caisse = models.ForeignKey(
        Caisse, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='decaissements',
        verbose_name="Caisse",
    )
    compte_bancaire = models.ForeignKey(
        CompteBancaire, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='decaissements',
        verbose_name="Compte bancaire",
    )

    motif = models.TextField(verbose_name="Motif")
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    justificatif = models.FileField(
        upload_to='decaissements/%Y/%m/',
        null=True, blank=True,
        verbose_name="Justificatif"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES,
        default='en_attente', verbose_name="Statut"
    )

    # Workflow
    demande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='decaissements_demandes',
        verbose_name="Demandé par",
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='decaissements_valides',
        verbose_name="Validé par",
    )
    paye_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='decaissements_payes',
        verbose_name="Payé par",
    )

    class Meta:
        verbose_name = "Décaissement"
        verbose_name_plural = "Décaissements"
        ordering = ['-date_demande', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['statut']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.montant} GNF"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"DEC-{year}-"
        dernier = Decaissement.objects.filter(
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
        prefixe = f"DEC-{year}-"
        dernier = Decaissement.objects.filter(
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


# ============================================================
# MOUVEMENT DE CAISSE (journal détaillé)
# ============================================================

class MouvementCaisse(BaseModel):
    """Mouvement détaillé d'une caisse (entrée/sortie)."""

    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]

    caisse = models.ForeignKey(
        Caisse, on_delete=models.CASCADE,
        related_name='mouvements_caisse_detail',
        verbose_name="Caisse"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    date_mouvement = models.DateField(auto_now_add=True, verbose_name="Date")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant")
    libelle = models.CharField(max_length=300, verbose_name="Libellé")

    encaissement = models.ForeignKey(
        Encaissement, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_caisse',
        verbose_name="Encaissement lié"
    )
    decaissement = models.ForeignKey(
        Decaissement, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_caisse',
        verbose_name="Décaissement lié"
    )

    class Meta:
        verbose_name = "Mouvement de caisse"
        verbose_name_plural = "Mouvements de caisse"
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.caisse.code} — {self.get_type_display()} {self.montant}"


# ============================================================
# PRÉVISION DE TRÉSORERIE
# ============================================================

class PrevisionTresorerie(BaseModel):
    """Prévisions de trésorerie."""

    TYPE_CHOICES = [
        ('entree', 'Entrée prévue'),
        ('sortie', 'Sortie prévue'),
    ]

    date_prevue = models.DateField(verbose_name="Date prévue")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    libelle = models.CharField(max_length=300, verbose_name="Libellé")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant")
    realise = models.BooleanField(default=False, verbose_name="Réalisé")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Prévision de trésorerie"
        verbose_name_plural = "Prévisions de trésorerie"
        ordering = ['date_prevue']

    def __str__(self):
        return f"{self.date_prevue} — {self.libelle} ({self.montant})"


# ============================================================
# ALERTE TRÉSORERIE
# ============================================================

class AlerteTresorerie(BaseModel):
    """Alertes de trésorerie."""

    NIVEAU_CHOICES = [
        ('info', 'Information'),
        ('avertissement', 'Avertissement'),
        ('critique', 'Critique'),
    ]

    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='info', verbose_name="Niveau")
    caisse = models.ForeignKey(
        Caisse, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alertes',
        verbose_name="Caisse"
    )
    compte_bancaire = models.ForeignKey(
        CompteBancaire, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alertes',
        verbose_name="Compte"
    )
    resolue = models.BooleanField(default=False, verbose_name="Résolue")
    date_resolution = models.DateTimeField(null=True, blank=True, verbose_name="Date résolution")

    class Meta:
        verbose_name = "Alerte trésorerie"
        verbose_name_plural = "Alertes trésorerie"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_niveau_display()}] {self.titre}"