# stocks/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


# ============================================================
# CATÉGORIE D'ARTICLE
# ============================================================

class CategorieArticle(BaseModel):
    """Catégories d'articles (EPI, outils, pièces, etc.)."""

    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    code = models.CharField(max_length=20, blank=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Catégorie d'article"
        verbose_name_plural = "Catégories d'articles"
        ordering = ['nom']

    def __str__(self):
        return self.nom


# ============================================================
# ARTICLE
# ============================================================

class Article(SoftDeleteModel):
    """Article en stock (EPI, gants, bottes, pièces...)."""

    code = models.CharField(max_length=50, unique=True,
                            verbose_name="Code article")
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    categorie = models.ForeignKey(
        CategorieArticle, on_delete=models.PROTECT, related_name='articles', verbose_name="Catégorie")
    description = models.TextField(blank=True, verbose_name="Description")

    unite = models.CharField(
        max_length=30, default='unité', verbose_name="Unité de mesure")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Prix unitaire (GNF)")
    stock_minimum = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Stock minimum")
    stock_maximum = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Stock maximum")
    seuil_alerte = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Seuil d'alerte")

    photo = models.ImageField(upload_to='articles/',
                              null=True, blank=True, verbose_name="Photo")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['designation']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['categorie']),
        ]

    def __str__(self):
        return f"{self.code} — {self.designation}"

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
# MAGASIN
# ============================================================

class Magasin(BaseModel):
    """Magasins / entrepôts."""

    code = models.CharField(max_length=30, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    responsable = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='magasins_gerees',
        verbose_name="Responsable",
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Magasin"
        verbose_name_plural = "Magasins"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"


# ============================================================
# STOCK PAR MAGASIN
# ============================================================

class StockMagasin(BaseModel):
    """Quantité d'un article dans un magasin donné."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE,
                                related_name='stocks_magasins', verbose_name="Article")
    magasin = models.ForeignKey(
        Magasin, on_delete=models.CASCADE, related_name='stocks', verbose_name="Magasin")
    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Quantité")
    emplacement = models.CharField(
        max_length=100, blank=True, verbose_name="Emplacement")

    class Meta:
        verbose_name = "Stock par magasin"
        verbose_name_plural = "Stocks par magasin"
        unique_together = ['article', 'magasin']

    def __str__(self):
        return f"{self.article.code} @ {self.magasin.nom} : {self.quantite}"


# ============================================================
# MOUVEMENT DE STOCK (Module 14)
# ============================================================

class MouvementStock(BaseModel, NumeroAutoMixin):
    """Mouvements de stock (entrée/sortie/transfert)."""

    PREFIX = 'MVT-STK'

    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('transfert', 'Transfert'),
        ('ajustement', 'Ajustement'),
    ]

    MOTIF_CHOICES = [
        # Entrées
        ('achat', 'Achat'),
        ('retour', 'Retour'),
        ('don', 'Don'),
        ('correction', 'Correction'),
        # Sorties
        ('affectation', 'Affectation'),
        ('consommation', 'Consommation'),
        ('perte', 'Perte'),
        ('deterioration', 'Détérioration'),
        ('retour_fournisseur', 'Retour fournisseur'),
        # Transferts
        ('transfert_magasin', 'Transfert magasin'),
    ]

    numero = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    motif = models.CharField(
        max_length=30, choices=MOTIF_CHOICES, verbose_name="Motif")
    date_mouvement = models.DateField(auto_now_add=True, verbose_name="Date")

    article = models.ForeignKey(
        Article, on_delete=models.PROTECT, related_name='mouvements', verbose_name="Article")
    quantite = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Prix unitaire")

    magasin_source = models.ForeignKey(
        Magasin, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_sortie',
        verbose_name="Magasin source",
    )
    magasin_destination = models.ForeignKey(
        Magasin, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_entree',
        verbose_name="Magasin destination",
    )

    # Lien vers bénéficiaire / fournisseur
    beneficiaire = models.CharField(
        max_length=200, blank=True, verbose_name="Bénéficiaire")
    fournisseur = models.ForeignKey(
        'achats.Fournisseur',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements_stock',
        verbose_name="Fournisseur",
    )
    equipement = models.ForeignKey(
        'stocks.Equipement',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mouvements',
        verbose_name="Équipement concerné",
    )

    reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence")
    observation = models.TextField(blank=True, verbose_name="Observation")
    justificatif = models.FileField(
        upload_to='mouvements_stock/%Y/%m/', null=True, blank=True, verbose_name="Justificatif")

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
        super().save(*args, **kwargs)
        self._appliquer_mouvement()

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
                    article=self.article, magasin=self.magasin_source)
                stock.quantite -= self.quantite
                stock.save()
            except StockMagasin.DoesNotExist:
                pass

        elif self.type == 'transfert':
            if self.magasin_source:
                try:
                    stock_src = StockMagasin.objects.get(
                        article=self.article, magasin=self.magasin_source)
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
# ÉQUIPEMENT
# ============================================================

class Equipement(SoftDeleteModel):
    """Équipements de travail (outils, matériel lourd, EPI)."""

    ETAT_CHOICES = [
        ('neuf', 'Neuf'),
        ('bon', 'Bon état'),
        ('usage', 'Usagé'),
        ('defectueux', 'Défectueux'),
        ('hors_service', 'Hors service'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    categorie = models.ForeignKey(CategorieArticle, on_delete=models.PROTECT,
                                  related_name='equipements', verbose_name="Catégorie")
    description = models.TextField(blank=True, verbose_name="Description")

    numero_serie = models.CharField(
        max_length=100, blank=True, verbose_name="Numéro de série")
    marque = models.CharField(
        max_length=100, blank=True, verbose_name="Marque")
    modele = models.CharField(
        max_length=100, blank=True, verbose_name="Modèle")
    date_acquisition = models.DateField(
        null=True, blank=True, verbose_name="Date d'acquisition")
    cout_acquisition = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name="Coût d'acquisition")

    etat = models.CharField(
        max_length=20, choices=ETAT_CHOICES, default='bon', verbose_name="État")
    localisation = models.CharField(
        max_length=200, blank=True, verbose_name="Localisation")
    responsable = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements_geres',
        verbose_name="Responsable",
    )

    photo = models.ImageField(upload_to='equipements/',
                              null=True, blank=True, verbose_name="Photo")

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"
        ordering = ['designation']

    def __str__(self):
        return f"{self.code} — {self.designation}"


# ============================================================
# AFFECTATION D'ÉQUIPEMENT
# ============================================================

class AffectationEquipement(BaseModel):
    """Affectation d'un équipement à un employé ou une équipe."""

    equipement = models.ForeignKey(
        Equipement, on_delete=models.CASCADE, related_name='affectations', verbose_name="Équipement")
    employe = models.ForeignKey(
        'rh.Employe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements_affectes',
        verbose_name="Employé",
    )
    equipe = models.ForeignKey(
        'exploitation.Equipe',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='equipements_affectes',
        verbose_name="Équipe",
    )

    date_affectation = models.DateField(
        auto_now_add=True, verbose_name="Date d'affectation")
    date_retour = models.DateField(
        null=True, blank=True, verbose_name="Date de retour")

    etat_avant = models.CharField(
        max_length=50, blank=True, verbose_name="État avant")
    etat_apres = models.CharField(
        max_length=50, blank=True, verbose_name="État après")

    observation = models.TextField(blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Affectation d'équipement"
        verbose_name_plural = "Affectations d'équipements"
        ordering = ['-date_affectation']

    def __str__(self):
        cible = self.employe.nom_complet if self.employe else (
            self.equipe.nom if self.equipe else '—')
        return f"{self.equipement.code} → {cible}"


# ============================================================
# INVENTAIRE
# ============================================================

class Inventaire(BaseModel):
    """Session d'inventaire physique."""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    ]

    reference = models.CharField(
        max_length=50, unique=True, verbose_name="Référence")
    magasin = models.ForeignKey(
        Magasin, on_delete=models.CASCADE, related_name='inventaires', verbose_name="Magasin")
    date_inventaire = models.DateField(auto_now_add=True, verbose_name="Date")
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_cours', verbose_name="Statut")

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='inventaires',
        verbose_name="Responsable",
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
        ordering = ['-date_inventaire']

    def __str__(self):
        return f"{self.reference} — {self.magasin.nom} ({self.date_inventaire})"


class LigneInventaire(BaseModel):
    """Ligne d'inventaire (article + quantité comptée)."""

    inventaire = models.ForeignKey(
        Inventaire, on_delete=models.CASCADE, related_name='lignes', verbose_name="Inventaire")
    article = models.ForeignKey(Article, on_delete=models.PROTECT,
                                related_name='lignes_inventaire', verbose_name="Article")

    quantite_theorique = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Quantité théorique")
    quantite_comptee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Quantité comptée")
    ecart = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Écart")

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
