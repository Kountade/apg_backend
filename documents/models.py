from django.db import models

# Create your models here.
# documents/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel, SoftDeleteModel, NumeroAutoMixin


# ============================================================
# CATÉGORIE DE DOCUMENT
# ============================================================

class CategorieDocument(BaseModel):
    """
    Catégories de documents APG (RH, comptable, véhicule, client, etc.).
    
    Permet de classer les documents par domaine métier.
    """

    TYPE_CHOICES = [
        ('rh', 'Ressources Humaines'),
        ('comptable', 'Comptabilité'),
        ('client', 'Client'),
        ('fournisseur', 'Fournisseur'),
        ('vehicule', 'Véhicule'),
        ('exploitation', 'Exploitation'),
        ('contrat', 'Contrat'),
        ('facture', 'Facture'),
        ('administratif', 'Administratif'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(
        max_length=100, unique=True, verbose_name="Nom")
    code = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name="Code",
        help_text="Généré automatiquement au format DOCAT-YYYY-NNNNNN"
    )
    type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default='autre',
        verbose_name="Type de catégorie"
    )
    description = models.TextField(
        blank=True, verbose_name="Description")
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sous_categories',
        verbose_name="Catégorie parente",
        help_text="Pour créer une hiérarchie (plan de classement)"
    )
    ordre = models.IntegerField(
        default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(
        default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Catégorie de document"
        verbose_name_plural = "Catégories de documents"
        ordering = ['ordre', 'nom']
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
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"DOCAT-{year}-"
        dernier = CategorieDocument.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']
        if dernier:
            try:
                nouveau = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau = 1
        else:
            nouveau = 1
        return f"{prefixe}{nouveau:06d}"

    @staticmethod
    def proposer_code():
        from django.utils import timezone
        from django.db.models import Max
        year = timezone.now().year
        prefixe = f"DOCAT-{year}-"
        dernier = CategorieDocument.objects.filter(
            code__startswith=prefixe
        ).aggregate(max_code=Max('code'))['max_code']
        if dernier:
            try:
                nouveau = int(dernier.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nouveau = 1
        else:
            nouveau = 1
        return f"{prefixe}{nouveau:06d}"


# ============================================================
# DOCUMENT (métadonnées)
# ============================================================

class Document(SoftDeleteModel, NumeroAutoMixin):
    """
    Document métier APG (fichier + métadonnées).
    
    ⚠️ Le fichier physique est stocké via FileField.
    Les métadonnées permettent de classer, rechercher et tracer.
    """

    PREFIX = 'DOC'

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('archive', 'Archivé'),
        ('obsolete', 'Obsolète'),
    ]

    CONFIDENTIALITE_CHOICES = [
        ('public', 'Public'),
        ('interne', 'Interne'),
        ('confidentiel', 'Confidentiel'),
        ('secret', 'Secret'),
    ]

    # Numéro auto : DOC-YYYY-NNNNNN
    numero = models.CharField(
        max_length=50, unique=True,
        verbose_name="Numéro du document"
    )

    # Classification
    categorie = models.ForeignKey(
        CategorieDocument, on_delete=models.PROTECT,
        related_name='documents', verbose_name="Catégorie"
    )
    titre = models.CharField(
        max_length=200, verbose_name="Titre")
    description = models.TextField(
        blank=True, verbose_name="Description")

    # Fichier
    fichier = models.FileField(
        upload_to='documents/%Y/%m/', 
        verbose_name="Fichier",
        help_text="Le fichier physique du document"
    )
    nom_fichier_original = models.CharField(
        max_length=255, blank=True,
        verbose_name="Nom du fichier original",
        help_text="Rempli automatiquement si non fourni"
    )
    taille_octets = models.BigIntegerField(
        default=0, verbose_name="Taille (octets)")
    type_mime = models.CharField(
        max_length=100, blank=True,
        verbose_name="Type MIME",
        help_text="Ex : application/pdf, image/jpeg"
    )
    hash_sha256 = models.CharField(
        max_length=64, blank=True,
        verbose_name="Hash SHA-256",
        help_text="Empreinte du fichier pour détecter les doublons"
    )

    # Métadonnées
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon',
        verbose_name="Statut"
    )
    confidentialite = models.CharField(
        max_length=20, choices=CONFIDENTIALITE_CHOICES, default='interne',
        verbose_name="Niveau de confidentialité"
    )

    # Dates
    date_document = models.DateField(
        null=True, blank=True,
        verbose_name="Date du document",
        help_text="Date figurant sur le document lui-même"
    )
    date_expiration = models.DateField(
        null=True, blank=True,
        verbose_name="Date d'expiration",
        help_text="Pour les contrats, assurances, etc."
    )

    # Traçabilité
    uploade_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='documents_uploades',
        verbose_name="Uploadé par"
    )

    # Mots-clés pour la recherche
    mots_cles = models.CharField(
        max_length=500, blank=True,
        verbose_name="Mots-clés",
        help_text="Séparés par des virgules pour la recherche"
    )

    # Versioning simple
    version = models.CharField(
        max_length=20, default='1.0',
        verbose_name="Version"
    )
    est_version_active = models.BooleanField(
        default=True,
        verbose_name="Version active",
        help_text="Si False, une version plus récente existe"
    )

    # Lien vers d'autres objets (optionnel)
    # On utilise des champs texte pour éviter les FK circulaires
    objet_lie_type = models.CharField(
        max_length=100, blank=True,
        verbose_name="Type d'objet lié",
        help_text="Ex : vehicules.Tricycle, achats.BonCommande, rh.Employe"
    )
    objet_lie_id = models.CharField(
        max_length=50, blank=True,
        verbose_name="ID de l'objet lié"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['categorie', 'statut']),
            models.Index(fields=['date_expiration']),
            models.Index(fields=['objet_lie_type', 'objet_lie_id']),
            models.Index(fields=['hash_sha256']),
        ]

    def __str__(self):
        return f"{self.numero} — {self.titre}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.generate_numero()
        # Taille auto
        if self.fichier and not self.taille_octets:
            try:
                self.taille_octets = self.fichier.size
            except (ValueError, OSError):
                pass
        # Nom original auto
        if self.fichier and not self.nom_fichier_original:
            self.nom_fichier_original = self.fichier.name.split('/')[-1]
        super().save(*args, **kwargs)

    @property
    def est_expire(self):
        from datetime import date
        if not self.date_expiration:
            return False
        return self.date_expiration < date.today()

    @property
    def jours_avant_expiration(self):
        from datetime import date
        if not self.date_expiration:
            return None
        return (self.date_expiration - date.today()).days

    @property
    def taille_formatee(self):
        """Retourne la taille lisible (Ko, Mo, Go)."""
        taille = float(self.taille_octets or 0)
        for unite in ['o', 'Ko', 'Mo', 'Go']:
            if taille < 1024:
                return f"{taille:.1f} {unite}"
            taille /= 1024
        return f"{taille:.1f} To"


# ============================================================
# VERSION DE DOCUMENT
# ============================================================

class DocumentVersion(BaseModel):
    """
    Version d'un document.
    
    Permet de conserver l'historique des révisions.
    """

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='versions', verbose_name="Document"
    )
    version = models.CharField(
        max_length=20, verbose_name="Version")
    fichier = models.FileField(
        upload_to='documents/versions/%Y/%m/',
        verbose_name="Fichier de la version"
    )
    commentaire = models.TextField(
        blank=True, verbose_name="Commentaire de révision")
    uploade_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='versions_documents',
        verbose_name="Uploadé par"
    )

    class Meta:
        verbose_name = "Version de document"
        verbose_name_plural = "Versions de documents"
        ordering = ['-created_at']
        unique_together = ['document', 'version']

    def __str__(self):
        return f"{self.document.numero} — v{self.version}"


# ============================================================
# ACCÈS DOCUMENT (permissions granulaires)
# ============================================================

class AccesDocument(BaseModel):
    """
    Droit d'accès spécifique à un document pour un utilisateur.
    
    Complète les permissions globales (par rôle) avec des
    autorisations explicites par document.
    """

    NIVEAU_CHOICES = [
        ('lecture', 'Lecture seule'),
        ('ecriture', 'Lecture + Écriture'),
        ('admin', 'Administration'),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='acces', verbose_name="Document"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='acces_documents',
        verbose_name="Utilisateur"
    )
    niveau = models.CharField(
        max_length=20, choices=NIVEAU_CHOICES, default='lecture',
        verbose_name="Niveau d'accès"
    )
    date_expiration = models.DateField(
        null=True, blank=True,
        verbose_name="Date d'expiration de l'accès"
    )

    class Meta:
        verbose_name = "Accès document"
        verbose_name_plural = "Accès documents"
        unique_together = ['document', 'utilisateur']
        ordering = ['document', 'utilisateur']

    def __str__(self):
        return f"{self.document.numero} → {self.utilisateur} ({self.get_niveau_display()})"

    @property
    def est_actif(self):
        from datetime import date
        if not self.date_expiration:
            return True
        return self.date_expiration >= date.today()


# ============================================================
# JOURNAL DE TÉLÉCHARGEMENT (traçabilité)
# ============================================================

class TelechargementDocument(BaseModel):
    """
    Trace chaque téléchargement de document.
    
    Conforme aux exigences d'audit et de traçabilité.
    """

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='telechargements', verbose_name="Document"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='telechargements_documents',
        verbose_name="Utilisateur"
    )
    date_telechargement = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de téléchargement"
    )
    adresse_ip = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.CharField(
        max_length=500, blank=True,
        verbose_name="User-Agent"
    )

    class Meta:
        verbose_name = "Téléchargement de document"
        verbose_name_plural = "Téléchargements de documents"
        ordering = ['-date_telechargement']
        indexes = [
            models.Index(fields=['document', 'date_telechargement']),
            models.Index(fields=['utilisateur']),
        ]

    def __str__(self):
        return f"{self.document.numero} — {self.date_telechargement:%d/%m/%Y %H:%M}"


# ============================================================
# PARTAGE DE DOCUMENT (lien public)
# ============================================================

class PartageDocument(BaseModel):
    """
    Partage d'un document via un lien public.
    
    Permet de générer une URL unique avec expiration.
    """

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='partages', verbose_name="Document"
    )
    token = models.CharField(
        max_length=64, unique=True,
        verbose_name="Token d'accès",
        help_text="Généré automatiquement"
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='partages_crees',
        verbose_name="Créé par"
    )
    date_expiration = models.DateTimeField(
        verbose_name="Date d'expiration du partage"
    )
    mot_de_passe = models.CharField(
        max_length=128, blank=True,
        verbose_name="Mot de passe (hash)",
        help_text="Optionnel — si vide, pas de protection"
    )
    nombre_max_telechargements = models.IntegerField(
        default=0, verbose_name="Nombre max de téléchargements",
        help_text="0 = illimité"
    )
    nombre_telechargements = models.IntegerField(
        default=0, verbose_name="Nombre de téléchargements effectués"
    )
    actif = models.BooleanField(
        default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Partage de document"
        verbose_name_plural = "Partages de documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['date_expiration']),
        ]

    def __str__(self):
        return f"Partage {self.token[:8]}… — {self.document.numero}"

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    @property
    def est_valide(self):
        from django.utils import timezone
        if not self.actif:
            return False
        if self.date_expiration < timezone.now():
            return False
        if self.nombre_max_telechargements > 0:
            if self.nombre_telechargements >= self.nombre_max_telechargements:
                return False
        return True

    @property
    def lien_partage(self):
        """Retourne l'URL relative de partage."""
        return f"/documents/partage/{self.token}/"