# comptabilite/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel


# ============================================================
# PLAN COMPTABLE
# ============================================================

class CompteComptable(BaseModel):
    """Plan comptable APG (SYSCOHADA adapté)."""

    CLASSE_CHOICES = [
        ('1', 'Classe 1 — Ressources durables'),
        ('2', 'Classe 2 — Actif immobilisé'),
        ('3', 'Classe 3 — Stocks'),
        ('4', 'Classe 4 — Tiers'),
        ('5', 'Classe 5 — Trésorerie'),
        ('6', 'Classe 6 — Charges'),
        ('7', 'Classe 7 — Produits'),
        ('8', 'Classe 8 — Autres charges/produits'),
    ]

    TYPE_CHOICES = [
        ('actif', 'Actif'),
        ('passif', 'Passif'),
        ('charge', 'Charge'),
        ('produit', 'Produit'),
        ('tresorerie', 'Trésorerie'),
    ]

    numero = models.CharField(
        max_length=20, unique=True, verbose_name="Numéro")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    classe = models.CharField(
        max_length=2, choices=CLASSE_CHOICES, verbose_name="Classe")
    compte_parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='sous_comptes',
        verbose_name="Compte parent",
    )
    type_compte = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Plan comptable"
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} — {self.libelle}"

    @property
    def solde(self):
        """Solde = sum(debit) - sum(credit) sur les lignes validées."""
        from django.db.models import Sum
        lignes = self.lignes_ecriture.filter(ecriture__statut='validee')
        debit = lignes.aggregate(t=Sum('debit'))['t'] or 0
        credit = lignes.aggregate(t=Sum('credit'))['t'] or 0
        return debit - credit


# ============================================================
# JOURNAL
# ============================================================

class Journal(BaseModel):
    """Journaux comptables."""

    TYPE_CHOICES = [
        ('AC', 'Achats'),
        ('VE', 'Ventes'),
        ('BQ', 'Banque'),
        ('CA', 'Caisse'),
        ('OD', 'Opérations Diverses'),
        ('PA', 'Paie'),
    ]

    code = models.CharField(max_length=10, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    type = models.CharField(
        max_length=5, choices=TYPE_CHOICES, verbose_name="Type")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Journal comptable"
        verbose_name_plural = "Journaux comptables"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.libelle}"


# ============================================================
# FACTURATION (Facture, Devis, Avoir, Paiement, Litige)
# ============================================================

class Facture(BaseModel):
    """Facture client."""

    TYPE_CHOICES = [
        ('proforma', 'Pro-forma'),
        ('definitive', 'Définitive'),
        ('avoir', 'Avoir'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('emise', 'Émise'),
        ('envoyee', 'Envoyée'),
        ('partiellement_payee', 'Partiellement payée'),
        ('payee', 'Payée'),
        ('en_retard', 'En retard'),
        ('litige', 'En litige'),
        ('annulee', 'Annulée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format FACT-YYYY-NNNNNN"
    )
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='definitive', verbose_name="Type")

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='factures',
        verbose_name="Client",
    )
    contrat = models.ForeignKey(
        'clients.ContratClient',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factures',
        verbose_name="Contrat lié",
    )

    date_emission = models.DateField(
        auto_now_add=True, verbose_name="Date d'émission")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    periode_debut = models.DateField(
        null=True, blank=True, verbose_name="Période du")
    periode_fin = models.DateField(
        null=True, blank=True, verbose_name="Période au")

    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant HT")
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="TVA (%)")
    montant_tva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant TTC")
    montant_paye = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant payé")
    remise = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Remise")

    statut = models.CharField(
        max_length=30, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")

    emise_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factures_emises',
        verbose_name="Émise par",
    )

    objet = models.CharField(max_length=300, blank=True, verbose_name="Objet")
    notes = models.TextField(blank=True, verbose_name="Notes")
    conditions_paiement = models.TextField(
        blank=True, verbose_name="Conditions")
    document_pdf = models.FileField(
        upload_to='factures/%Y/%m/', null=True, blank=True, verbose_name="PDF")

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['client', 'statut']),
            models.Index(fields=['date_echeance']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.client.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        if self.montant_ht and self.taux_tva is not None:
            self.calculer_totaux()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"FACT-{year}-"
        dernier = Facture.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
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
        prefixe = f"FACT-{year}-"
        dernier = Facture.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"

    @property
    def solde_restant(self):
        return self.montant_ttc - self.montant_paye - self.remise

    @property
    def est_payee(self):
        return self.solde_restant <= 0

    @property
    def est_en_retard(self):
        from datetime import date
        if self.est_payee:
            return False
        return self.date_echeance < date.today()

    @property
    def jours_retard(self):
        from datetime import date
        if not self.est_en_retard:
            return 0
        return (date.today() - self.date_echeance).days

    def calculer_totaux(self):
        self.montant_tva = self.montant_ht * (self.taux_tva / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva - self.remise
        return self.montant_ttc


class LigneFacture(BaseModel):
    """Ligne de facture."""

    facture = models.ForeignKey(
        Facture, on_delete=models.CASCADE, related_name='lignes', verbose_name="Facture")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    description = models.TextField(blank=True, verbose_name="Description")
    quantite = models.DecimalField(
        max_digits=10, decimal_places=2, default=1, verbose_name="Quantité")
    unite = models.CharField(max_length=30, blank=True, verbose_name="Unité")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Prix unitaire")
    remise_ligne = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Remise")
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant HT")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.designation} x {self.quantite}"

    def save(self, *args, **kwargs):
        self.montant_ht = (
            self.quantite * self.prix_unitaire) - self.remise_ligne
        super().save(*args, **kwargs)


class Devis(BaseModel):
    """Devis commercial."""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
        ('transforme', 'Transformé en facture'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format DEV-YYYY-NNNNNN"
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE, related_name='devis', verbose_name="Client")
    objet = models.CharField(max_length=300, verbose_name="Objet")
    date_emission = models.DateField(
        auto_now_add=True, verbose_name="Date d'émission")
    date_validite = models.DateField(verbose_name="Date de validité")

    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant HT")
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="TVA (%)")
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant TTC")

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    facture_generee = models.ForeignKey(
        Facture, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='devis_origine',
        verbose_name="Facture générée",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Devis"
        verbose_name_plural = "Devis"
        ordering = ['-date_emission']

    def __str__(self):
        return f"{self.numero} — {self.client.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        if self.montant_ht and self.taux_tva is not None:
            self.montant_ttc = self.montant_ht + \
                (self.montant_ht * self.taux_tva / 100)
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"DEV-{year}-"
        dernier = Devis.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
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
        prefixe = f"DEV-{year}-"
        dernier = Devis.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


class LigneDevis(BaseModel):
    """Ligne de devis."""

    devis = models.ForeignKey(
        Devis, on_delete=models.CASCADE, related_name='lignes', verbose_name="Devis")
    designation = models.CharField(max_length=300, verbose_name="Désignation")
    quantite = models.DecimalField(
        max_digits=10, decimal_places=2, default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Prix unitaire")
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant HT")

    class Meta:
        verbose_name = "Ligne de devis"
        verbose_name_plural = "Lignes de devis"
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.montant_ht = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)


class Avoir(BaseModel):
    """Avoir émis à un client (remboursement, annulation partielle)."""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('emis', 'Émis'),
        ('utilise', 'Utilisé'),
        ('annule', 'Annulé'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format AVR-YYYY-NNNNNN"
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='avoirs', verbose_name="Client"
    )
    facture_origine = models.ForeignKey(
        Facture, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='avoirs',
        verbose_name="Facture d'origine"
    )
    date_avoir = models.DateField(
        auto_now_add=True, verbose_name="Date de l'avoir")
    objet = models.CharField(max_length=300, verbose_name="Objet")
    motif = models.TextField(verbose_name="Motif")

    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant HT")
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="TVA (%)")
    montant_tva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant TTC")

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Avoir"
        verbose_name_plural = "Avoirs"
        ordering = ['-date_avoir']

    def __str__(self):
        return f"{self.numero} — {self.client.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        self.montant_tva = self.montant_ht * (self.taux_tva / 100)
        self.montant_ttc = self.montant_ht + self.montant_tva
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"AVR-{year}-"
        dernier = Avoir.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


class PaiementClient(BaseModel):
    """Paiement reçu d'un client pour une facture."""

    MODE_CHOICES = [
        ('especes', 'Espèces'),
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format PAI-YYYY-NNNNNN"
    )
    facture = models.ForeignKey(
        Facture, on_delete=models.CASCADE,
        related_name='paiements', verbose_name="Facture"
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='paiements', verbose_name="Client"
    )
    montant = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant payé (GNF)")
    date_paiement = models.DateField(verbose_name="Date du paiement")
    mode = models.CharField(max_length=30, choices=MODE_CHOICES,
                            default='especes', verbose_name="Mode de paiement")
    reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True, verbose_name="Notes")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='valide', verbose_name="Statut")
    justificatif = models.FileField(
        upload_to='paiements/%Y/%m/', null=True, blank=True, verbose_name="Justificatif")

    class Meta:
        verbose_name = "Paiement client"
        verbose_name_plural = "Paiements clients"
        ordering = ['-date_paiement']

    def __str__(self):
        return f"{self.numero} — {self.client.nom_complet} ({self.montant} GNF)"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)
        if self.statut == 'valide':
            self._update_facture()

    def _update_facture(self):
        from django.db.models import Sum
        total_paye = PaiementClient.objects.filter(
            facture=self.facture, statut='valide'
        ).aggregate(t=Sum('montant'))['t'] or 0
        self.facture.montant_paye = total_paye
        if self.facture.solde_restant <= 0:
            self.facture.statut = 'payee'
        elif total_paye > 0:
            self.facture.statut = 'partiellement_payee'
        self.facture.save(update_fields=['montant_paye', 'statut'])

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"PAI-{year}-"
        dernier = PaiementClient.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


class Litige(BaseModel):
    """Litige sur une facture impayée."""

    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('clos', 'Clos'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format LIT-YYYY-NNNNNN"
    )
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE,
                                related_name='litiges', verbose_name="Facture concernée")
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT, related_name='litiges', verbose_name="Client")
    date_ouverture = models.DateField(
        auto_now_add=True, verbose_name="Date d'ouverture")
    date_resolution = models.DateField(
        null=True, blank=True, verbose_name="Date de résolution")
    motif = models.TextField(verbose_name="Motif du litige")
    description = models.TextField(blank=True, verbose_name="Description")
    montant_conteste = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Montant contesté")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='ouvert', verbose_name="Statut")
    resolution = models.TextField(blank=True, verbose_name="Résolution")

    class Meta:
        verbose_name = "Litige"
        verbose_name_plural = "Litiges"
        ordering = ['-date_ouverture']

    def __str__(self):
        return f"{self.numero} — {self.facture.numero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"LIT-{year}-"
        dernier = Litige.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


# ============================================================
# ÉCRITURES COMPTABLES
# ============================================================

class EcritureComptable(BaseModel):
    """Écriture comptable (partie double)."""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('lettree', 'Lettrée'),
        ('annulee', 'Annulée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format ECR-YYYY-NNNNNN"
    )
    journal = models.ForeignKey(
        Journal, on_delete=models.PROTECT, related_name='ecritures', verbose_name="Journal")
    date_ecriture = models.DateField(verbose_name="Date")
    libelle = models.CharField(max_length=300, verbose_name="Libellé")
    reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")

    module_source = models.CharField(
        max_length=50, blank=True, verbose_name="Module source")
    object_id = models.CharField(
        max_length=50, blank=True, verbose_name="ID objet source")

    total_debit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total débit")
    total_credit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Total crédit")

    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='ecritures_validees',
        verbose_name="Validée par",
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date validation")

    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ['-date_ecriture', '-numero']

    def __str__(self):
        return f"{self.numero} — {self.libelle}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"ECR-{year}-"
        dernier = EcritureComptable.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"

    @property
    def est_equilibree(self):
        return self.total_debit == self.total_credit

    def calculer_totaux(self):
        from django.db.models import Sum
        lignes = self.lignes.all()
        self.total_debit = lignes.aggregate(t=Sum('debit'))['t'] or 0
        self.total_credit = lignes.aggregate(t=Sum('credit'))['t'] or 0
        self.save(update_fields=['total_debit', 'total_credit'])


class LigneEcriture(BaseModel):
    """Ligne d'écriture (débit/crédit)."""

    ecriture = models.ForeignKey(
        EcritureComptable, on_delete=models.CASCADE, related_name='lignes', verbose_name="Écriture")
    compte = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                               related_name='lignes_ecriture', verbose_name="Compte")
    libelle = models.CharField(
        max_length=300, blank=True, verbose_name="Libellé")
    debit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Débit")
    credit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Crédit")
    lettrage = models.CharField(
        max_length=20, blank=True, verbose_name="Lettrage")
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    class Meta:
        verbose_name = "Ligne d'écriture"
        verbose_name_plural = "Lignes d'écriture"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.compte.numero} — D:{self.debit} C:{self.credit}"


class Lettrage(BaseModel):
    """Lettrage de comptes."""

    compte = models.ForeignKey(CompteComptable, on_delete=models.CASCADE,
                               related_name='lettrages', verbose_name="Compte")
    code_lettrage = models.CharField(max_length=20, verbose_name="Code")
    date_lettrage = models.DateField(auto_now_add=True, verbose_name="Date")
    montant_lettre = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant lettré")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Lettrage"
        verbose_name_plural = "Lettrages"
        ordering = ['-date_lettrage']

    def __str__(self):
        return f"{self.code_lettrage} — {self.compte.numero} ({self.montant_lettre})"


class DeclarationFiscale(BaseModel):
    """Déclarations fiscales."""

    TYPE_CHOICES = [
        ('tva', 'TVA'),
        ('is', 'Impôt sur les sociétés'),
        ('ir', 'Impôt sur le revenu'),
        ('cnss', 'CNSS'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('a_preparer', 'À préparer'),
        ('preparee', 'Préparée'),
        ('deposee', 'Déposée'),
        ('payee', 'Payée'),
    ]

    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    periode = models.CharField(max_length=50, verbose_name="Période")
    montant = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant (GNF)")
    date_echeance = models.DateField(verbose_name="Échéance")
    date_depot = models.DateField(
        null=True, blank=True, verbose_name="Date dépôt")
    date_paiement = models.DateField(
        null=True, blank=True, verbose_name="Date paiement")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='a_preparer', verbose_name="Statut")
    document = models.FileField(
        upload_to='declarations/', null=True, blank=True, verbose_name="Document")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Déclaration fiscale"
        verbose_name_plural = "Déclarations fiscales"
        ordering = ['-date_echeance']

    def __str__(self):
        return f"{self.get_type_display()} — {self.periode}"


# ============================================================
# CLÔTURE COMPTABLE
# ============================================================

class ClotureComptable(BaseModel):
    """Clôture d'une période comptable (mensuelle, trimestrielle, annuelle)."""

    TYPE_CHOICES = [
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('semestrielle', 'Semestrielle'),
        ('annuelle', 'Annuelle'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_cours', 'En cours'),
        ('validee', 'Validée'),
        ('reouverte', 'Réouverte'),
    ]

    # ✅ NUMÉRO AUTO-GÉNÉRÉ : CLO-YYYY-NNNNNN
    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format CLO-YYYY-NNNNNN"
    )
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='mensuelle',
        verbose_name="Type de clôture"
    )

    # Période concernée
    mois = models.IntegerField(null=True, blank=True, verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    trimestre = models.IntegerField(
        null=True, blank=True,
        choices=[
            (1, 'T1 (Jan-Mar)'),
            (2, 'T2 (Avr-Juin)'),
            (3, 'T3 (Juil-Sep)'),
            (4, 'T4 (Oct-Déc)'),
        ],
        verbose_name="Trimestre"
    )

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")

    # Totaux calculés au moment de la clôture
    total_debit = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name="Total débit"
    )
    total_credit = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name="Total crédit"
    )
    total_produits = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name="Total produits (Classe 7)"
    )
    total_charges = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name="Total charges (Classe 6)"
    )
    resultat = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name="Résultat de la période"
    )
    nombre_ecritures = models.IntegerField(
        default=0, verbose_name="Nombre d'écritures"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )

    # Workflow
    cloture_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='clotures_effectuees',
        verbose_name="Clôturée par",
    )
    date_cloture = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de clôture"
    )
    reouverte_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='clotures_reouvertes',
        verbose_name="Réouverte par",
    )
    date_reouverture = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Date de réouverture"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")
    rapport_pdf = models.FileField(
        upload_to='clotures/%Y/%m/', null=True, blank=True,
        verbose_name="Rapport PDF"
    )

    class Meta:
        verbose_name = "Clôture comptable"
        verbose_name_plural = "Clôtures comptables"
        ordering = ['-annee', '-mois']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['annee', 'mois']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        if self.mois:
            return f"Clôture {self.mois:02d}/{self.annee}"
        if self.trimestre:
            return f"Clôture T{self.trimestre}/{self.annee}"
        return f"Clôture annuelle {self.annee}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"CLO-{year}-"
        dernier = ClotureComptable.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
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
        prefixe = f"CLO-{year}-"
        dernier = ClotureComptable.objects.filter(
            numero__startswith=prefixe
        ).aggregate(max_numero=Max('numero'))['max_numero']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"

    def calculer_totaux(self):
        """Calcule les totaux depuis les écritures validées de la période."""
        from django.db.models import Sum, Count

        ecritures = EcritureComptable.objects.filter(
            date_ecriture__gte=self.date_debut,
            date_ecriture__lte=self.date_fin,
            statut='validee',
        )

        self.nombre_ecritures = ecritures.count()
        self.total_debit = ecritures.aggregate(t=Sum('total_debit'))['t'] or 0
        self.total_credit = ecritures.aggregate(
            t=Sum('total_credit'))['t'] or 0

        # Produits = lignes de comptes classe 7 (crédit - débit)
        produits = LigneEcriture.objects.filter(
            ecriture__in=ecritures,
            compte__numero__startswith='7',
        ).aggregate(
            debit=Sum('debit'),
            credit=Sum('credit'),
        )
        self.total_produits = (
            produits['credit'] or 0) - (produits['debit'] or 0)

        # Charges = lignes de comptes classe 6 (débit - crédit)
        charges = LigneEcriture.objects.filter(
            ecriture__in=ecritures,
            compte__numero__startswith='6',
        ).aggregate(
            debit=Sum('debit'),
            credit=Sum('credit'),
        )
        self.total_charges = (charges['debit'] or 0) - (charges['credit'] or 0)

        # Résultat = Produits - Charges
        self.resultat = self.total_produits - self.total_charges

        self.save(update_fields=[
            'nombre_ecritures', 'total_debit', 'total_credit',
            'total_produits', 'total_charges', 'resultat'
        ])
        return self.resultat

    @property
    def est_benefice(self):
        return self.resultat >= 0

    @property
    def libelle(self):
        if self.mois:
            from datetime import date
            mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                         'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
            return f"{mois_noms[self.mois - 1]} {self.annee}"
        if self.trimestre:
            return f"T{self.trimestre} {self.annee}"
        return f"Année {self.annee}"
