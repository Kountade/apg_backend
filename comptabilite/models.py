from django.db import models

# Create your models here.
# comptabilite/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


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
        max_length=20,
        choices=[
            ('actif', 'Actif'),
            ('passif', 'Passif'),
            ('charge', 'Charge'),
            ('produit', 'Produit'),
            ('tresorerie', 'Trésorerie'),
        ],
        verbose_name="Type",
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Plan comptable"
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} — {self.libelle}"


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
# FACTURATION
# ============================================================

class Facture(BaseModel, NumeroAutoMixin):
    """Facture client."""

    PREFIX = 'FACT'

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
        max_length=50, unique=True, verbose_name="Numéro")
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

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        if self.montant_ht and self.taux_tva is not None:
            self.calculer_totaux()
        super().save(*args, **kwargs)


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


# ============================================================
# DEVIS
# ============================================================

class Devis(BaseModel, NumeroAutoMixin):
    """Devis commercial."""

    PREFIX = 'DEV'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
        ('transforme', 'Transformé en facture'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
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
            self.numero = self.generate_numero()
        if self.montant_ht and self.taux_tva is not None:
            self.montant_ttc = self.montant_ht + \
                (self.montant_ht * self.taux_tva / 100)
        super().save(*args, **kwargs)


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


# ============================================================
# ÉCRITURES COMPTABLES
# ============================================================

class EcritureComptable(BaseModel, NumeroAutoMixin):
    """Écriture comptable (partie double)."""

    PREFIX = 'ECR'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('lettree', 'Lettrée'),
        ('annulee', 'Annulée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
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
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['journal', 'date_ecriture']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.libelle}"

    @property
    def est_equilibree(self):
        return self.total_debit == self.total_credit

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)


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


# ============================================================
# LETTRAGE
# ============================================================

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


# ============================================================
# RAPPROCHEMENT BANCAIRE
# ============================================================

class RapprochementBancaire(BaseModel):
    """Rapprochement bancaire."""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('equilibre', 'Équilibré'),
        ('ecart', 'Écart détecté'),
        ('cloture', 'Clôturé'),
    ]

    compte_bancaire = models.ForeignKey(
        'tresorerie.CompteBancaire',
        on_delete=models.CASCADE,
        related_name='rapprochements',
        verbose_name="Compte bancaire",
    )
    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    solde_releve = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Solde relevé")
    solde_comptable = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Solde comptable")
    ecart = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Écart")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_cours', verbose_name="Statut")
    notes = models.TextField(blank=True, verbose_name="Notes")
    releve = models.FileField(
        upload_to='rapprochements/', null=True, blank=True, verbose_name="Relevé")
    cloture_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='rapprochements_clotures',
        verbose_name="Clôturé par",
    )
    date_cloture = models.DateTimeField(
        null=True, blank=True, verbose_name="Date clôture")

    class Meta:
        verbose_name = "Rapprochement bancaire"
        verbose_name_plural = "Rapprochements bancaires"
        unique_together = ['compte_bancaire', 'mois', 'annee']
        ordering = ['-annee', '-mois']

    def __str__(self):
        return f"{self.compte_bancaire} — {self.mois}/{self.annee}"

    def save(self, *args, **kwargs):
        self.ecart = self.solde_releve - self.solde_comptable
        super().save(*args, **kwargs)


# ============================================================
# DÉCLARATIONS FISCALES
# ============================================================

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
