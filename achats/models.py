from django.db import models

# Create your models here.
# achats/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


# ============================================================
# FOURNISSEUR
# ============================================================

class Fournisseur(SoftDeleteModel):
    """Fournisseur d'APG (pièces, EPI, carburant, services...)."""

    TYPE_CHOICES = [
        ('materiel', 'Matériel / Équipement'),
        ('piece', 'Pièces détachées'),
        ('epi', 'EPI / Consommables'),
        ('carburant', 'Carburant'),
        ('service', 'Prestation de service'),
        ('maintenance', 'Maintenance'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
        ('archive', 'Archivé'),
    ]

    # ✅ CODE AUTO-GÉNÉRÉ : FOU-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code fournisseur",
        help_text="Généré automatiquement au format FOU-YYYY-NNNNNN"
    )

    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default='materiel',
        verbose_name="Type de fournisseur"
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif',
        verbose_name="Statut"
    )

    # Identité
    nom = models.CharField(max_length=200, verbose_name="Nom / Raison sociale")
    sigle = models.CharField(max_length=50, blank=True, verbose_name="Sigle")
    num_contribuable = models.CharField(
        max_length=50, blank=True, verbose_name="N° Contribuable"
    )
    num_rccm = models.CharField(
        max_length=50, blank=True, verbose_name="N° RCCM"
    )

    # Contact
    telephone = models.CharField(max_length=30, verbose_name="Téléphone")
    telephone2 = models.CharField(
        max_length=30, blank=True, verbose_name="Téléphone 2"
    )
    email = models.EmailField(blank=True, verbose_name="Email")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    pays = models.CharField(
        max_length=100, default='Guinée', verbose_name="Pays"
    )

    # Contact commercial
    contact_nom = models.CharField(
        max_length=150, blank=True, verbose_name="Nom du contact"
    )
    contact_fonction = models.CharField(
        max_length=100, blank=True, verbose_name="Fonction du contact"
    )
    contact_telephone = models.CharField(
        max_length=30, blank=True, verbose_name="Téléphone contact"
    )
    contact_email = models.EmailField(
        blank=True, verbose_name="Email contact"
    )

    # Conditions commerciales
    delai_livraison_jours = models.IntegerField(
        default=7, verbose_name="Délai de livraison (jours)"
    )
    conditions_paiement = models.CharField(
        max_length=100, blank=True,
        verbose_name="Conditions de paiement",
        help_text="Ex : Comptant, 30 jours, 60 jours"
    )
    remise_habituelle = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Remise habituelle (%)"
    )

    # Coordonnées bancaires
    banque = models.CharField(
        max_length=100, blank=True, verbose_name="Banque")
    numero_compte = models.CharField(
        max_length=50, blank=True, verbose_name="Numéro de compte"
    )
    iban = models.CharField(max_length=50, blank=True, verbose_name="IBAN")

    # Évaluation
    note_moyenne = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Note moyenne (sur 5)"
    )

    # Média
    logo = models.ImageField(
        upload_to='fournisseurs/', null=True, blank=True, verbose_name="Logo"
    )
    notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type', 'statut']),
            models.Index(fields=['nom']),
        ]

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
        prefixe = f"FOU-{year}-"
        dernier = Fournisseur.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
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
        prefixe = f"FOU-{year}-"
        dernier = Fournisseur.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


# ============================================================
# ÉVALUATION FOURNISSEUR
# ============================================================

class EvaluationFournisseur(BaseModel):
    """Évaluation périodique d'un fournisseur."""

    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.CASCADE,
        related_name='evaluations', verbose_name="Fournisseur"
    )
    date_evaluation = models.DateField(
        auto_now_add=True, verbose_name="Date de l'évaluation"
    )
    periode = models.CharField(
        max_length=50, verbose_name="Période",
        help_text="Ex : T1 2026, Janvier 2026"
    )

    # Critères (notes sur 5)
    note_qualite = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Qualité (sur 5)"
    )
    note_prix = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Prix (sur 5)"
    )
    note_delai = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Délais (sur 5)"
    )
    note_service = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Service (sur 5)"
    )
    note_globale = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name="Note globale (sur 5)"
    )

    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    evaluateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='evaluations_fournisseurs',
        verbose_name="Évaluateur"
    )

    class Meta:
        verbose_name = "Évaluation fournisseur"
        verbose_name_plural = "Évaluations fournisseurs"
        ordering = ['-date_evaluation']
        unique_together = ['fournisseur', 'periode']

    def __str__(self):
        return f"{self.fournisseur.nom} — {self.periode} ({self.note_globale}/5)"

    def save(self, *args, **kwargs):
        # Calcul auto de la note globale
        notes = [
            self.note_qualite, self.note_prix,
            self.note_delai, self.note_service
        ]
        notes_valides = [float(n) for n in notes if n and float(n) > 0]
        if notes_valides:
            self.note_globale = sum(notes_valides) / len(notes_valides)
        super().save(*args, **kwargs)

        # Mettre à jour la note moyenne du fournisseur
        evaluations = EvaluationFournisseur.objects.filter(
            fournisseur=self.fournisseur
        )
        if evaluations.exists():
            from django.db.models import Avg
            moyenne = evaluations.aggregate(
                avg=Avg('note_globale')
            )['avg'] or 0
            self.fournisseur.note_moyenne = moyenne
            self.fournisseur.save(update_fields=['note_moyenne'])


# ============================================================
# DEMANDE D'ACHAT
# ============================================================

class DemandeAchat(BaseModel, NumeroAutoMixin):
    """Demande d'achat interne émise par un employé/service."""

    PREFIX = 'DEM-ACH'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('convertie', 'Convertie en bon de commande'),
        ('annulee', 'Annulée'),
    ]

    URGENCE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro"
    )
    date_demande = models.DateField(
        auto_now_add=True, verbose_name="Date de la demande"
    )
    date_souhaitee = models.DateField(
        null=True, blank=True, verbose_name="Date souhaitée de livraison"
    )

    demandeur = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='demandes_achat',
        verbose_name="Demandeur"
    )
    service = models.CharField(
        max_length=100, blank=True, verbose_name="Service demandeur"
    )

    objet = models.CharField(
        max_length=300, verbose_name="Objet de la demande")
    motif = models.TextField(blank=True, verbose_name="Motif / Justification")

    urgence = models.CharField(
        max_length=20, choices=URGENCE_CHOICES, default='normale',
        verbose_name="Niveau d'urgence"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )

    # Workflow
    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='demandes_achat_validees',
        verbose_name="Validée par"
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de validation"
    )
    commentaire_validation = models.TextField(
        blank=True, verbose_name="Commentaire de validation"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Demande d'achat"
        verbose_name_plural = "Demandes d'achat"
        ordering = ['-date_demande', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['statut']),
            models.Index(fields=['demandeur']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.objet}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)


class LigneDemandeAchat(BaseModel):
    """Ligne de demande d'achat."""

    demande = models.ForeignKey(
        DemandeAchat, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Demande"
    )
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    designation = models.CharField(max_length=300, verbose_name="Désignation")
    description = models.TextField(blank=True, verbose_name="Description")

    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, default=1,
        verbose_name="Quantité"
    )
    unite = models.CharField(
        max_length=30, blank=True, default='unité', verbose_name="Unité"
    )

    # Prix estimé (optionnel)
    prix_estime = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prix estimé (GNF)"
    )

    # Article en stock lié (optionnel)
    article_stock = models.ForeignKey(
        'stocks.Article',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='demandes_achat',
        verbose_name="Article en stock"
    )

    class Meta:
        verbose_name = "Ligne de demande d'achat"
        verbose_name_plural = "Lignes de demande d'achat"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.designation} x {self.quantite}"

    @property
    def montant_estime(self):
        return float(self.quantite) * float(self.prix_estime)


# ============================================================
# DEVIS FOURNISSEUR
# ============================================================

class DevisFournisseur(BaseModel, NumeroAutoMixin):
    """Devis reçu d'un fournisseur suite à une demande."""

    PREFIX = 'DEV-FOU'

    STATUT_CHOICES = [
        ('recu', 'Reçu'),
        ('en_etude', 'En étude'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro interne"
    )
    numero_devis_fournisseur = models.CharField(
        max_length=100, blank=True,
        verbose_name="N° devis fournisseur"
    )

    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='devis', verbose_name="Fournisseur"
    )
    demande_achat = models.ForeignKey(
        DemandeAchat,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='devis_recus',
        verbose_name="Demande d'achat liée"
    )

    date_devis = models.DateField(verbose_name="Date du devis")
    date_validite = models.DateField(
        null=True, blank=True, verbose_name="Date de validité"
    )

    objet = models.CharField(max_length=300, verbose_name="Objet")
    notes = models.TextField(blank=True, verbose_name="Notes")

    # Montants
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant HT (GNF)"
    )
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="TVA (%)"
    )
    montant_tva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TVA"
    )
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TTC"
    )

    delai_livraison_jours = models.IntegerField(
        default=7, verbose_name="Délai de livraison (jours)"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='recu',
        verbose_name="Statut"
    )

    # Document
    fichier_devis = models.FileField(
        upload_to='devis_fournisseurs/%Y/%m/', null=True, blank=True,
        verbose_name="Fichier du devis"
    )

    class Meta:
        verbose_name = "Devis fournisseur"
        verbose_name_plural = "Devis fournisseurs"
        ordering = ['-date_devis', '-numero']

    def __str__(self):
        return f"{self.numero} — {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        # Calcul auto TVA/TTC
        self.montant_tva = float(self.montant_ht) * \
            (float(self.taux_tva) / 100)
        self.montant_ttc = float(self.montant_ht) + float(self.montant_tva)
        super().save(*args, **kwargs)


class LigneDevisFournisseur(BaseModel):
    """Ligne de devis fournisseur."""

    devis = models.ForeignKey(
        DevisFournisseur, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Devis"
    )
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    designation = models.CharField(max_length=300, verbose_name="Désignation")
    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, default=1,
        verbose_name="Quantité"
    )
    unite = models.CharField(
        max_length=30, blank=True, default='unité', verbose_name="Unité"
    )
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prix unitaire HT"
    )
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant HT"
    )

    class Meta:
        verbose_name = "Ligne de devis fournisseur"
        verbose_name_plural = "Lignes de devis fournisseurs"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.designation} x {self.quantite}"

    def save(self, *args, **kwargs):
        self.montant_ht = float(self.quantite) * float(self.prix_unitaire)
        super().save(*args, **kwargs)


# ============================================================
# BON DE COMMANDE
# ============================================================

class BonCommande(BaseModel, NumeroAutoMixin):
    """Bon de commande envoyé au fournisseur."""

    PREFIX = 'BC'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé au fournisseur'),
        ('confirme', 'Confirmé par fournisseur'),
        ('partiellement_recu', 'Partiellement reçu'),
        ('recu', 'Entièrement reçu'),
        ('annule', 'Annulé'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro"
    )

    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='bons_commande', verbose_name="Fournisseur"
    )
    demande_achat = models.ForeignKey(
        DemandeAchat,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bons_commande',
        verbose_name="Demande d'achat origine"
    )
    devis_fournisseur = models.ForeignKey(
        DevisFournisseur,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bons_commande',
        verbose_name="Devis d'origine"
    )

    date_commande = models.DateField(verbose_name="Date de commande")
    date_livraison_prevue = models.DateField(
        null=True, blank=True, verbose_name="Date de livraison prévue"
    )
    date_livraison_reelle = models.DateField(
        null=True, blank=True, verbose_name="Date de livraison réelle"
    )

    objet = models.CharField(max_length=300, verbose_name="Objet")
    conditions_particulieres = models.TextField(
        blank=True, verbose_name="Conditions particulières"
    )

    # Montants
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant HT"
    )
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="TVA (%)"
    )
    montant_tva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TVA"
    )
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TTC"
    )

    statut = models.CharField(
        max_length=30, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )

    # Validation interne
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='bons_commande_valides',
        verbose_name="Validé par"
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de validation"
    )

    # Document
    fichier_pdf = models.FileField(
        upload_to='bons_commande/%Y/%m/', null=True, blank=True,
        verbose_name="Bon de commande PDF"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Bon de commande"
        verbose_name_plural = "Bons de commande"
        ordering = ['-date_commande', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['fournisseur', 'statut']),
            models.Index(fields=['date_commande']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        self.montant_tva = float(self.montant_ht) * \
            (float(self.taux_tva) / 100)
        self.montant_ttc = float(self.montant_ht) + float(self.montant_tva)
        super().save(*args, **kwargs)


class LigneBonCommande(BaseModel):
    """Ligne de bon de commande."""

    bon_commande = models.ForeignKey(
        BonCommande, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Bon de commande"
    )
    ordre = models.IntegerField(default=0, verbose_name="Ordre")

    designation = models.CharField(max_length=300, verbose_name="Désignation")
    description = models.TextField(blank=True, verbose_name="Description")

    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, default=1,
        verbose_name="Quantité commandée"
    )
    unite = models.CharField(
        max_length=30, blank=True, default='unité', verbose_name="Unité"
    )
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prix unitaire HT"
    )
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant HT"
    )

    # Article en stock lié (pour réapprovisionnement)
    article_stock = models.ForeignKey(
        'stocks.Article',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='lignes_bon_commande',
        verbose_name="Article en stock"
    )

    # Suivi réception
    quantite_recue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité reçue"
    )

    class Meta:
        verbose_name = "Ligne de bon de commande"
        verbose_name_plural = "Lignes de bon de commande"
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.designation} x {self.quantite}"

    def save(self, *args, **kwargs):
        self.montant_ht = float(self.quantite) * float(self.prix_unitaire)
        super().save(*args, **kwargs)

    @property
    def quantite_restante(self):
        return float(self.quantite) - float(self.quantite_recue)

    @property
    def est_completement_recu(self):
        return float(self.quantite_recue) >= float(self.quantite)


# ============================================================
# RÉCEPTION
# ============================================================

class Reception(BaseModel, NumeroAutoMixin):
    """Réception de marchandises suite à un bon de commande."""

    PREFIX = 'REC'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_attente', 'En attente de contrôle'),
        ('controlee', 'Contrôlée'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro"
    )

    bon_commande = models.ForeignKey(
        BonCommande, on_delete=models.PROTECT,
        related_name='receptions', verbose_name="Bon de commande"
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='receptions', verbose_name="Fournisseur"
    )

    date_reception = models.DateField(verbose_name="Date de réception")
    numero_bon_livraison = models.CharField(
        max_length=100, blank=True,
        verbose_name="N° bon de livraison fournisseur"
    )

    magasin_destination = models.ForeignKey(
        'stocks.Magasin',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='receptions',
        verbose_name="Magasin de destination"
    )

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )

    # Contrôle
    controle_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='receptions_controlees',
        verbose_name="Contrôlée par"
    )
    date_controle = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de contrôle"
    )

    observations = models.TextField(blank=True, verbose_name="Observations")

    # Documents
    fichier_bon_livraison = models.FileField(
        upload_to='receptions/%Y/%m/', null=True, blank=True,
        verbose_name="Bon de livraison scanné"
    )

    class Meta:
        verbose_name = "Réception"
        verbose_name_plural = "Réceptions"
        ordering = ['-date_reception', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['bon_commande', 'statut']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)


class LigneReception(BaseModel):
    """Ligne de réception (article + quantité reçue)."""

    reception = models.ForeignKey(
        Reception, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Réception"
    )
    ligne_bon_commande = models.ForeignKey(
        LigneBonCommande, on_delete=models.PROTECT,
        related_name='lignes_reception',
        verbose_name="Ligne du bon de commande"
    )

    quantite_recue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité reçue"
    )
    quantite_acceptee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité acceptée"
    )
    quantite_refusee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité refusée"
    )

    motif_refus = models.TextField(blank=True, verbose_name="Motif du refus")

    class Meta:
        verbose_name = "Ligne de réception"
        verbose_name_plural = "Lignes de réception"
        ordering = ['id']

    def __str__(self):
        return f"{self.ligne_bon_commande.designation} — Reçu: {self.quantite_recue}"

    def save(self, *args, **kwargs):
        self.quantite_refusee = float(
            self.quantite_recue) - float(self.quantite_acceptee)
        super().save(*args, **kwargs)


# ============================================================
# FACTURE FOURNISSEUR
# ============================================================

class FactureFournisseur(BaseModel, NumeroAutoMixin):
    """Facture reçue d'un fournisseur."""

    PREFIX = 'FAC-FOU'

    STATUT_CHOICES = [
        ('recue', 'Reçue'),
        ('controlee', 'Contrôlée'),
        ('validee', 'Validée'),
        ('partiellement_payee', 'Partiellement payée'),
        ('payee', 'Payée'),
        ('litige', 'En litige'),
        ('annulee', 'Annulée'),
    ]

    numero_interne = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro interne"
    )
    numero_facture_fournisseur = models.CharField(
        max_length=100, verbose_name="N° facture fournisseur"
    )

    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='factures', verbose_name="Fournisseur"
    )
    bon_commande = models.ForeignKey(
        BonCommande,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factures',
        verbose_name="Bon de commande lié"
    )
    reception = models.ForeignKey(
        Reception,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factures',
        verbose_name="Réception liée"
    )

    date_facture = models.DateField(verbose_name="Date de la facture")
    date_echeance = models.DateField(
        null=True, blank=True, verbose_name="Date d'échéance"
    )

    objet = models.CharField(max_length=300, verbose_name="Objet")

    # Montants
    montant_ht = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant HT"
    )
    taux_tva = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="TVA (%)"
    )
    montant_tva = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TVA"
    )
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant TTC"
    )
    montant_paye = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Montant payé"
    )

    statut = models.CharField(
        max_length=30, choices=STATUT_CHOICES, default='recue',
        verbose_name="Statut"
    )

    # Validation
    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factures_fournisseurs_validees',
        verbose_name="Validée par"
    )
    date_validation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date de validation"
    )

    # Document
    fichier_pdf = models.FileField(
        upload_to='factures_fournisseurs/%Y/%m/', null=True, blank=True,
        verbose_name="Facture scannée"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Facture fournisseur"
        verbose_name_plural = "Factures fournisseurs"
        ordering = ['-date_facture', '-numero_interne']
        indexes = [
            models.Index(fields=['numero_interne']),
            models.Index(fields=['fournisseur', 'statut']),
            models.Index(fields=['date_echeance']),
        ]

    def __str__(self):
        return f"{self.numero_interne} — {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        if not self.numero_interne:
            self.numero_interne = self.generate_numero()
        self.montant_tva = float(self.montant_ht) * \
            (float(self.taux_tva) / 100)
        self.montant_ttc = float(self.montant_ht) + float(self.montant_tva)
        super().save(*args, **kwargs)

    @property
    def solde_du(self):
        return float(self.montant_ttc) - float(self.montant_paye)

    @property
    def est_payee(self):
        return self.solde_du <= 0

    @property
    def est_en_retard(self):
        from datetime import date
        if self.est_payee or not self.date_echeance:
            return False
        return self.date_echeance < date.today()


# ============================================================
# PAIEMENT FOURNISSEUR
# ============================================================

class PaiementFournisseur(BaseModel, NumeroAutoMixin):
    """Paiement effectué à un fournisseur."""

    PREFIX = 'PAI-FOU'

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
        max_length=50, unique=True, verbose_name="Numéro"
    )

    facture = models.ForeignKey(
        FactureFournisseur, on_delete=models.CASCADE,
        related_name='paiements', verbose_name="Facture"
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='paiements', verbose_name="Fournisseur"
    )

    montant = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant payé (GNF)"
    )
    date_paiement = models.DateField(verbose_name="Date du paiement")
    mode = models.CharField(
        max_length=30, choices=MODE_CHOICES, default='virement',
        verbose_name="Mode de paiement"
    )

    reference = models.CharField(
        max_length=100, blank=True,
        verbose_name="Référence",
        help_text="N° chèque, N° virement, etc."
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='valide',
        verbose_name="Statut"
    )

    justificatif = models.FileField(
        upload_to='paiements_fournisseurs/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif"
    )

    class Meta:
        verbose_name = "Paiement fournisseur"
        verbose_name_plural = "Paiements fournisseurs"
        ordering = ['-date_paiement', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['facture', 'statut']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.fournisseur.nom} ({self.montant} GNF)"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.statut == 'valide':
            self._update_facture()

    def _update_facture(self):
        """Met à jour le montant payé sur la facture."""
        from django.db.models import Sum
        total_paye = PaiementFournisseur.objects.filter(
            facture=self.facture, statut='valide'
        ).aggregate(t=Sum('montant'))['t'] or 0

        self.facture.montant_paye = total_paye

        if self.facture.solde_du <= 0:
            self.facture.statut = 'payee'
        elif total_paye > 0:
            self.facture.statut = 'partiellement_payee'

        self.facture.save(update_fields=['montant_paye', 'statut'])
