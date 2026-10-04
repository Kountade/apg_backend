# config/models.py
from django.db import models
from django.conf import settings
from core.models import BaseModel


# ============================================================
# ✅ ÉTABLISSEMENT — VOTRE VERSION EXISTANTE (ne pas modifier)
# ============================================================

class Etablissement(models.Model):
    nom = models.CharField(max_length=200)
    sigle = models.CharField(max_length=20, blank=True)
    adresse = models.TextField()

    telephone1 = models.CharField(
        max_length=20,
        verbose_name="Téléphone principal",
        blank=True,
        null=True
    )
    telephone2 = models.CharField(
        max_length=20,
        verbose_name="Téléphone secondaire",
        blank=True,
        null=True
    )

    email = models.EmailField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='etablissement/', blank=True, null=True)
    devise = models.CharField(max_length=10, default='F CFA')

    systeme_notation = models.CharField(
        max_length=20,
        choices=[
            ('sur20', 'Sur 20'),
            ('sur100', 'Sur 100'),
            ('lettre', 'Lettres'),
        ],
        default='sur20'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"

    def __str__(self):
        return self.nom


# ============================================================
# 🆕 NUMÉROTATION AUTOMATIQUE (cahier des charges §30)
# ============================================================

class Numerotation(BaseModel):
    """Règles de numérotation automatique des documents."""
    type_document = models.CharField(
        max_length=50,
        verbose_name="Type de document",
        help_text="Ex: FACT, BC, DEP, ENC, DEC, RH-EMP, TR, VEH"
    )
    prefixe = models.CharField(max_length=20, verbose_name="Préfixe")
    annee = models.IntegerField(verbose_name="Année")
    dernier_numero = models.IntegerField(
        default=0, verbose_name="Dernier numéro")
    format = models.CharField(
        max_length=100,
        default='{prefix}-{year}-{num:06d}',
        verbose_name="Format",
        help_text="Variables : {prefix}, {year}, {num}"
    )

    class Meta:
        verbose_name = "Numérotation"
        verbose_name_plural = "Numérotations"
        unique_together = ['type_document', 'annee']
        ordering = ['-annee', 'type_document']

    def __str__(self):
        return f"{self.type_document} — {self.annee} ({self.dernier_numero})"


# ============================================================
# 🆕 NOTIFICATIONS (cahier des charges §22)
# ============================================================

class Notification(BaseModel):
    """Notifications utilisateurs (in-app, email, SMS en évolution)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire",
    )
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    type = models.CharField(
        max_length=50,
        choices=[
            ('info', 'Information'),
            ('alerte', 'Alerte'),
            ('validation', 'Validation'),
            ('systeme', 'Système'),
        ],
        default='info',
        verbose_name="Type",
    )
    module = models.CharField(
        max_length=50, blank=True,
        verbose_name="Module source",
        help_text="Ex: rh, paie, tresorerie, stocks..."
    )
    lien = models.CharField(
        max_length=300, blank=True,
        verbose_name="Lien d'action",
        help_text="URL vers lequel rediriger l'utilisateur"
    )
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.titre} → {self.user.email}"


# ============================================================
# 🆕 JOURNAL D'AUDIT (cahier des charges §25, §35)
# ============================================================

class AuditLog(models.Model):
    """
    Journal d'audit : trace TOUTES les opérations sensibles.
    Conforme au principe 4 (traçabilité) du cahier des charges.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name="Utilisateur",
    )
    module = models.CharField(max_length=50, verbose_name="Module")
    action = models.CharField(
        max_length=50, verbose_name="Action",
        help_text="create, update, delete, validate, cancel..."
    )
    model_name = models.CharField(max_length=100, verbose_name="Modèle")
    object_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID objet")
    old_values = models.JSONField(
        null=True, blank=True,
        verbose_name="Anciennes valeurs"
    )
    new_values = models.JSONField(
        null=True, blank=True,
        verbose_name="Nouvelles valeurs"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['module', 'model_name']),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.user} — {self.module}.{self.action}"


# ============================================================
# 🆕 HISTORIQUE DES CONNEXIONS (cahier des charges §25)
# ============================================================

class LoginHistory(models.Model):
    """Historique des connexions utilisateurs."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name="Utilisateur",
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    login_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Connexion")
    logout_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Déconnexion")
    success = models.BooleanField(default=True, verbose_name="Succès")

    class Meta:
        verbose_name = "Historique de connexion"
        verbose_name_plural = "Historique des connexions"
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.user.email} — {self.login_at}"


# ============================================================
# 🆕 DOCUMENTS (cahier des charges §23)
# ============================================================

class Document(BaseModel):
    """
    Documents archivés, rattachables à n'importe quel objet
    via (module, object_id).
    """
    nom = models.CharField(max_length=200, verbose_name="Nom du fichier")
    fichier = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name="Fichier"
    )
    type = models.CharField(
        max_length=50,
        choices=[
            ('contrat', 'Contrat'),
            ('facture', 'Facture'),
            ('recu', 'Reçu'),
            ('bon_commande', 'Bon de commande'),
            ('bon_livraison', 'Bon de livraison'),
            ('justificatif', 'Justificatif'),
            ('contrat_travail', 'Contrat de travail'),
            ('piece_admin', 'Pièce administrative'),
            ('document_vehicule', 'Document véhicule'),
            ('document_fournisseur', 'Document fournisseur'),
            ('autre', 'Autre'),
        ],
        verbose_name="Type",
    )
    module = models.CharField(
        max_length=50, verbose_name="Module",
        help_text="Ex: rh, paie, tresorerie, stocks..."
    )
    reference = models.CharField(
        max_length=100, blank=True, verbose_name="Référence")
    object_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID objet lié")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module', 'object_id']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
