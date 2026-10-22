# stocks/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


# ============================================================
# CATÉGORIE (matériels & consommables)
# ============================================================

class CategorieMateriel(BaseModel):
    """
    Catégories de matériels APG :
    - EPI (gants, bottes, masques, combinaisons)
    - Outils (pelles, râteaux, balais)
    - Pièces détachées (pour tricycles)
    - Consommables (sacs poubelles, désinfectants)
    - Équipements lourds (tricycles, containers)
    """

    TYPE_CHOICES = [
        ('epi', 'EPI (Équipement de protection)'),
        ('outil', 'Outil manuel'),
        ('consommable', 'Consommable'),
        ('piece', 'Pièce détachée'),
        ('equipement', 'Équipement / Matériel'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom")

    # ✅ CODE AUTO-GÉNÉRÉ : CAT-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code",
        help_text="Généré automatiquement au format CAT-YYYY-NNNNNN"
    )

    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='autre',
        verbose_name="Type de catégorie"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Catégorie de matériel"
        verbose_name_plural = "Catégories de matériels"
        ordering = ['type', 'nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.code or self.nom} — {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique CAT-YYYY-NNNNNN."""
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"CAT-{year}-"
        dernier = CategorieMateriel.objects.filter(
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
        """Retourne le prochain code SANS l'enregistrer."""
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"CAT-{year}-"
        dernier = CategorieMateriel.objects.filter(
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
# MAGASIN / DÉPÔT
# ============================================================

class Magasin(BaseModel):
    """Dépôts / magasins de stockage des matériels APG."""

    TYPE_CHOICES = [
        ('principal', 'Dépôt principal'),
        ('secondaire', 'Dépôt secondaire'),
        ('vehicule', 'Stock véhicule'),
        ('chantier', 'Stock chantier'),
    ]

    # ✅ CODE AUTO-GÉNÉRÉ : MAG-YYYY-NNNNNN
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code",
        help_text="Généré automatiquement au format MAG-YYYY-NNNNNN"
    )

    nom = models.CharField(max_length=100, verbose_name="Nom")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='principal',
        verbose_name="Type de dépôt"
    )
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    zone = models.CharField(max_length=100, blank=True, verbose_name="Zone")
    responsable = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='magasins_geres',
        verbose_name="Responsable",
    )
    telephone = models.CharField(
        max_length=30, blank=True, verbose_name="Téléphone")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Magasin / Dépôt"
        verbose_name_plural = "Magasins / Dépôts"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.code} — {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code unique MAG-YYYY-NNNNNN."""
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"MAG-{year}-"
        dernier = Magasin.objects.filter(
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
        """Retourne le prochain code SANS l'enregistrer."""
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"MAG-{year}-"
        dernier = Magasin.objects.filter(
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
# ARTICLE (consommables & pièces détachées)
# ============================================================

class Article(SoftDeleteModel):
    """
    Article consommable ou pièce détachée.
    Ex : gants, bottes, sacs poubelles, pièces détachées tricycle.

    ⚠️ Ce ne sont PAS des produits à vendre, mais des consommables
    internes pour l'activité de collecte des déchets.
    """

    UNITE_CHOICES = [
        ('unite', 'Unité'),
        ('paire', 'Paire'),
        ('carton', 'Carton'),
        ('kg', 'Kilogramme'),
        ('litre', 'Litre'),
        ('metre', 'Mètre'),
        ('rouleau', 'Rouleau'),
        ('lot', 'Lot'),
    ]

    code = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Code article",
        help_text="Généré automatiquement au format ART-YYYY-NNNNNN"
    )
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    categorie = models.ForeignKey(
        CategorieMateriel, on_delete=models.PROTECT,
        related_name='articles', verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, verbose_name="Description")

    unite = models.CharField(
        max_length=20, choices=UNITE_CHOICES, default='unite',
        verbose_name="Unité de mesure"
    )

    # Stock
    stock_minimum = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Stock minimum",
        help_text="Seuil en dessous duquel il faut commander"
    )
    seuil_alerte = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Seuil d'alerte"
    )

    # Prix (coût d'achat uniquement, PAS de prix de vente)
    prix_achat = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prix d'achat unitaire (GNF)"
    )

    # Fournisseur d'achat (texte libre pour éviter dépendance achats)
    fournisseur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name="Fournisseur habituel"
    )

    photo = models.ImageField(
        upload_to='articles/', null=True, blank=True, verbose_name="Photo"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Article (consommable)"
        verbose_name_plural = "Articles (consommables)"
        ordering = ['designation']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return f"{self.code} — {self.designation}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"ART-{year}-"
        dernier = Article.objects.filter(
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
        prefixe = f"ART-{year}-"
        dernier = Article.objects.filter(
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

    @property
    def stock_total(self):
        """Stock total sur tous les magasins."""
        from django.db.models import Sum
        result = self.stocks_magasins.aggregate(t=Sum('quantite'))['t']
        return result or 0

    @property
    def est_en_alerte(self):
        return self.stock_total <= self.seuil_alerte

    @property
    def est_critique(self):
        return self.stock_total <= self.stock_minimum


# ============================================================
# STOCK PAR MAGASIN
# ============================================================

class StockMagasin(BaseModel):
    """Quantité d'un article dans un magasin donné."""

    article = models.ForeignKey(
        Article, on_delete=models.CASCADE,
        related_name='stocks_magasins', verbose_name="Article"
    )
    magasin = models.ForeignKey(
        Magasin, on_delete=models.CASCADE,
        related_name='stocks', verbose_name="Magasin"
    )
    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Quantité"
    )
    emplacement = models.CharField(
        max_length=100, blank=True, verbose_name="Emplacement"
    )

    class Meta:
        verbose_name = "Stock par magasin"
        verbose_name_plural = "Stocks par magasin"
        unique_together = ['article', 'magasin']

    def __str__(self):
        return f"{self.article.code} @ {self.magasin.nom} : {self.quantite}"


# ============================================================
# ÉQUIPEMENT DURABLE (matériel de travail)
# ============================================================

class Equipement(SoftDeleteModel):
    """
    Équipement durable APG (tricycles, containers, outils lourds, EPI réutilisable).

    ⚠️ Ce n'est PAS un consommable, mais un BIEN DURABLE identifié
    qui a un numéro de série et un cycle de vie.
    """

    ETAT_CHOICES = [
        ('neuf', 'Neuf'),
        ('bon', 'Bon état'),
        ('usage', 'Usagé'),
        ('defectueux', 'Défectueux'),
        ('hors_service', 'Hors service'),
        ('rebut', 'Mis au rebut'),
    ]

    code = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Code équipement",
        help_text="Généré automatiquement au format EQP-YYYY-NNNNNN"
    )
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    categorie = models.ForeignKey(
        CategorieMateriel, on_delete=models.PROTECT,
        related_name='equipements', verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, verbose_name="Description")

    # Identification matérielle
    numero_serie = models.CharField(
        max_length=100, blank=True, verbose_name="Numéro de série"
    )
    marque = models.CharField(
        max_length=100, blank=True, verbose_name="Marque"
    )
    modele = models.CharField(
        max_length=100, blank=True, verbose_name="Modèle"
    )
    annee_fabrication = models.IntegerField(
        null=True, blank=True, verbose_name="Année de fabrication"
    )

    # Acquisition
    date_acquisition = models.DateField(
        null=True, blank=True, verbose_name="Date d'acquisition"
    )
    cout_acquisition = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Coût d'acquisition (GNF)"
    )
    fournisseur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name="Fournisseur d'achat"
    )

    # Garantie
    duree_garantie_mois = models.IntegerField(
        null=True, blank=True, verbose_name="Durée de garantie (mois)"
    )
    date_fin_garantie = models.DateField(
        null=True, blank=True, verbose_name="Fin de garantie"
    )

    # Amortissement
    duree_amortissement_mois = models.IntegerField(
        null=True, blank=True,
        verbose_name="Durée d'amortissement (mois)",
        help_text="Ex : 60 mois (5 ans) pour un tricycle"
    )
    valeur_residuelle = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Valeur résiduelle (GNF)"
    )

    # État & localisation
    etat = models.CharField(
        max_length=20, choices=ETAT_CHOICES, default='neuf',
        verbose_name="État actuel"
    )
    localisation = models.CharField(
        max_length=200, blank=True, verbose_name="Localisation actuelle"
    )
    magasin = models.ForeignKey(
        Magasin,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements',
        verbose_name="Magasin de rattachement"
    )

    # Responsable
    responsable = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements_geres',
        verbose_name="Responsable"
    )

    # Média
    photo = models.ImageField(
        upload_to='equipements/', null=True, blank=True, verbose_name="Photo"
    )
    fiche_technique = models.FileField(
        upload_to='equipements/fiches/', null=True, blank=True,
        verbose_name="Fiche technique (PDF)"
    )

    actif = models.BooleanField(default=True, verbose_name="Actif")
    notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"
        ordering = ['designation']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['etat']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return f"{self.code} — {self.designation}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"EQP-{year}-"
        dernier = Equipement.objects.filter(
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
        prefixe = f"EQP-{year}-"
        dernier = Equipement.objects.filter(
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

    @property
    def valeur_actuelle(self):
        """Valeur comptable actuelle après amortissement linéaire."""
        from datetime import date
        if not self.date_acquisition or not self.duree_amortissement_mois:
            return self.cout_acquisition

        mois_ecoules = (
            (date.today().year - self.date_acquisition.year) * 12
            + (date.today().month - self.date_acquisition.month)
        )
        if mois_ecoules <= 0:
            return self.cout_acquisition
        if mois_ecoules >= self.duree_amortissement_mois:
            return self.valeur_residuelle

        amortissement_mensuel = (
            (self.cout_acquisition - self.valeur_residuelle)
            / self.duree_amortissement_mois
        )
        valeur = self.cout_acquisition - (amortissement_mensuel * mois_ecoules)
        return max(valeur, self.valeur_residuelle)

    @property
    def est_sous_garantie(self):
        from datetime import date
        if not self.date_fin_garantie:
            return False
        return self.date_fin_garantie >= date.today()

    @property
    def age_mois(self):
        from datetime import date
        if not self.date_acquisition:
            return 0
        return (
            (date.today().year - self.date_acquisition.year) * 12
            + (date.today().month - self.date_acquisition.month)
        )


# ============================================================
# AFFECTATION D'ÉQUIPEMENT
# ============================================================

class AffectationEquipement(BaseModel):
    """
    Affectation d'un équipement à un employé (ou responsable).

    ⚠️ Pas de FK vers 'exploitation.Equipe' (séparation des modules).
    Si une équipe est concernée, on la mentionne dans 'equipe_nom'.
    """

    equipement = models.ForeignKey(
        Equipement, on_delete=models.CASCADE,
        related_name='affectations', verbose_name="Équipement"
    )
    employe = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements_affectes',
        verbose_name="Employé affecté"
    )
    equipe_nom = models.CharField(
        max_length=100, blank=True,
        verbose_name="Équipe (nom libre)",
        help_text="Nom de l'équipe si affecté à une équipe entière"
    )

    date_affectation = models.DateField(
        auto_now_add=True, verbose_name="Date d'affectation"
    )
    date_retour = models.DateField(
        null=True, blank=True, verbose_name="Date de retour"
    )

    etat_avant = models.CharField(
        max_length=50, blank=True, verbose_name="État avant affectation"
    )
    etat_apres = models.CharField(
        max_length=50, blank=True, verbose_name="État au retour"
    )

    # Documents
    bon_sortie = models.FileField(
        upload_to='affectations/%Y/%m/', null=True, blank=True,
        verbose_name="Bon de sortie"
    )
    bon_retour = models.FileField(
        upload_to='affectations/%Y/%m/', null=True, blank=True,
        verbose_name="Bon de retour"
    )

    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Affectation d'équipement"
        verbose_name_plural = "Affectations d'équipements"
        ordering = ['-date_affectation']
        indexes = [
            models.Index(fields=['equipement', 'date_affectation']),
            models.Index(fields=['employe']),
        ]

    def __str__(self):
        cible = self.employe.nom_complet if self.employe else (
            self.equipe_nom or '—'
        )
        return f"{self.equipement.code} → {cible}"

    @property
    def est_en_cours(self):
        return self.date_retour is None


# ============================================================
# MOUVEMENT DE STOCK
# ============================================================

class MouvementStock(BaseModel, NumeroAutoMixin):
    """
    Mouvements de stock des ARTICLES (consommables / pièces).
    Pour les équipements durables, utiliser AffectationEquipement.
    """

    PREFIX = 'MVT-STK'

    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('transfert', 'Transfert'),
        ('ajustement', 'Ajustement'),
        ('retour', 'Retour'),
    ]

    MOTIF_CHOICES = [
        # Entrées
        ('achat', 'Achat'),
        ('don', 'Don'),
        ('retour_magasin', 'Retour au magasin'),
        ('correction', 'Correction'),
        # Sorties
        ('consommation', 'Consommation'),
        ('affectation', 'Affectation'),
        ('perte', 'Perte'),
        ('deterioration', 'Détérioration'),
        ('retour_fournisseur', 'Retour fournisseur'),
        # Transferts
        ('transfert_magasin', 'Transfert entre magasins'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro"
    )
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type"
    )
    motif = models.CharField(
        max_length=30, choices=MOTIF_CHOICES, verbose_name="Motif"
    )
    date_mouvement = models.DateField(
        auto_now_add=True, verbose_name="Date du mouvement"
    )

    article = models.ForeignKey(
        Article, on_delete=models.PROTECT,
        related_name='mouvements', verbose_name="Article"
    )
    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Quantité"
    )
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Prix unitaire (GNF)"
    )

    magasin_source = models.ForeignKey(
        Magasin, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_sortie',
        verbose_name="Magasin source"
    )
    magasin_destination = models.ForeignKey(
        Magasin, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_entree',
        verbose_name="Magasin destination"
    )

    # Bénéficiaire (employé qui reçoit le matériel)
    beneficiaire = models.CharField(
        max_length=200, blank=True, verbose_name="Bénéficiaire"
    )
    employe_beneficiaire = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_recus',
        verbose_name="Employé bénéficiaire"
    )

    # Fournisseur (texte libre — pas de FK)
    fournisseur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name="Fournisseur"
    )

    reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence externe"
    )
    observation = models.TextField(blank=True, verbose_name="Observation")
    justificatif = models.FileField(
        upload_to='mouvements_stock/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif"
    )

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-date_mouvement', '-numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['type', 'date_mouvement']),
            models.Index(fields=['article']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.get_type_display()} {self.article.code} x {self.quantite}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self._appliquer_mouvement()

    # ✅ NOUVEAU : proposer_numero() — aligné sur NumeroAutoMixin.generate_numero()
    @classmethod
    def proposer_numero(cls):
        """
        Retourne le prochain numéro SANS l'enregistrer ni incrémenter le compteur.
        Utilise la même configuration (config.models.Numerotation) que generate_numero().
        """
        from django.utils import timezone
        from config.models import Numerotation

        year = timezone.now().year
        num_config = Numerotation.objects.filter(
            type_document=cls.PREFIX,
            annee=year,
        ).first()

        if not num_config:
            # Aucun compteur n'existe encore → prochain numéro = 1
            prefixe = cls.PREFIX
            dernier = 0
        else:
            prefixe = num_config.prefixe or cls.PREFIX
            dernier = num_config.dernier_numero or 0

        prochain = dernier + 1
        try:
            return num_config.format.format(
                prefix=prefixe,
                year=year,
                num=prochain,
            ) if num_config else f"{prefixe}-{year}-{prochain:06d}"
        except (KeyError, IndexError, AttributeError):
            return f"{prefixe}-{year}-{prochain:06d}"

    def _appliquer_mouvement(self):
        """Met à jour les stocks par magasin."""
        if self.type == 'entree' and self.magasin_destination:
            stock, _ = StockMagasin.objects.get_or_create(
                article=self.article,
                magasin=self.magasin_destination,
            )
            stock.quantite += self.quantite
            stock.save()

        elif self.type == 'sortie' and self.magasin_source:
            try:
                stock = StockMagasin.objects.get(
                    article=self.article, magasin=self.magasin_source
                )
                stock.quantite -= self.quantite
                stock.save()
            except StockMagasin.DoesNotExist:
                pass

        elif self.type == 'transfert':
            if self.magasin_source:
                try:
                    stock_src = StockMagasin.objects.get(
                        article=self.article, magasin=self.magasin_source
                    )
                    stock_src.quantite -= self.quantite
                    stock_src.save()
                except StockMagasin.DoesNotExist:
                    pass
            if self.magasin_destination:
                stock_dst, _ = StockMagasin.objects.get_or_create(
                    article=self.article,
                    magasin=self.magasin_destination,
                )
                stock_dst.quantite += self.quantite
                stock_dst.save()


# ============================================================
# INTERVENTION DE MAINTENANCE
# ============================================================

class MaintenanceEquipement(BaseModel):
    """
    Intervention de maintenance sur un équipement (réparation, entretien).
    """

    TYPE_CHOICES = [
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('urgence', 'Urgence'),
        ('revision', 'Révision'),
    ]

    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Numéro",
        help_text="Généré automatiquement au format MNT-YYYY-NNNNNN"
    )
    equipement = models.ForeignKey(
        Equipement, on_delete=models.CASCADE,
        related_name='maintenances', verbose_name="Équipement"
    )
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='corrective',
        verbose_name="Type d'intervention"
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='planifiee',
        verbose_name="Statut"
    )

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True, blank=True, verbose_name="Date de fin"
    )

    description = models.TextField(verbose_name="Description des travaux")
    technicien = models.CharField(
        max_length=200, blank=True, verbose_name="Technicien / Prestataire"
    )

    cout_main_oeuvre = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Coût main d'œuvre (GNF)"
    )
    cout_pieces = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Coût pièces (GNF)"
    )
    cout_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Coût total (GNF)"
    )

    observations = models.TextField(blank=True, verbose_name="Observations")
    justificatif = models.FileField(
        upload_to='maintenances/%Y/%m/', null=True, blank=True,
        verbose_name="Justificatif (facture, rapport)"
    )

    class Meta:
        verbose_name = "Maintenance d'équipement"
        verbose_name_plural = "Maintenances d'équipements"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['equipement', 'statut']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.equipement.code} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero()
        self.cout_total = self.cout_main_oeuvre + self.cout_pieces
        super().save(*args, **kwargs)

    def _generer_numero(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"MNT-{year}-"
        dernier = MaintenanceEquipement.objects.filter(
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
        prefixe = f"MNT-{year}-"
        dernier = MaintenanceEquipement.objects.filter(
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
# INVENTAIRE (comptage physique)
# ============================================================

class Inventaire(BaseModel):
    """Session d'inventaire physique des articles d'un magasin."""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    ]

    reference = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="Référence",
        help_text="Généré automatiquement au format INV-YYYY-NNNNNN"
    )
    magasin = models.ForeignKey(
        Magasin, on_delete=models.CASCADE,
        related_name='inventaires', verbose_name="Magasin"
    )
    date_inventaire = models.DateField(
        auto_now_add=True, verbose_name="Date de l'inventaire"
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_cours',
        verbose_name="Statut"
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='inventaires',
        verbose_name="Responsable"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
        ordering = ['-date_inventaire']

    def __str__(self):
        return f"{self.reference} — {self.magasin.nom} ({self.date_inventaire})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generer_reference()
        super().save(*args, **kwargs)

    def _generer_reference(self):
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"INV-{year}-"
        dernier = Inventaire.objects.filter(
            reference__startswith=prefixe
        ).aggregate(max_ref=Max('reference'))['max_ref']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"

    @staticmethod
    def proposer_reference():
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"INV-{year}-"
        dernier = Inventaire.objects.filter(
            reference__startswith=prefixe
        ).aggregate(max_ref=Max('reference'))['max_ref']
        if dernier:
            try:
                nouveau_numero = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        return f"{prefixe}{nouveau_numero:06d}"


class LigneInventaire(BaseModel):
    """Ligne d'inventaire (article + quantité comptée)."""

    inventaire = models.ForeignKey(
        Inventaire, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Inventaire"
    )
    article = models.ForeignKey(
        Article, on_delete=models.PROTECT,
        related_name='lignes_inventaire', verbose_name="Article"
    )

    quantite_theorique = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité théorique"
    )
    quantite_comptee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantité comptée"
    )
    ecart = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Écart"
    )

    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Ligne d'inventaire"
        verbose_name_plural = "Lignes d'inventaire"
        unique_together = ['inventaire', 'article']

    def __str__(self):
        return f"{self.article.code} — Théorique:{self.quantite_theorique} / Compté:{self.quantite_comptee}"

    def save(self, *args, **kwargs):
        self.ecart = self.quantite_comptee - self.quantite_theorique
        super().save(*args, **kwargs)
