# alertes/models.py
"""
Module alertes = agrégateur.
Pas de modèle principal : les alertes sont calculées à la volée
depuis les autres modules (RH, Paie, Achats, Stocks, Véhicules, Documents, Exploitation).

On garde 2 modèles utilitaires :
- ConfigAlerte : seuils configurables (placeholder pour plus tard)
- CanalNotification : canaux de diffusion (placeholder pour plus tard)
"""
from django.db import models
from django.conf import settings
from core.models import BaseModel


# ============================================================
# CONFIGURATION ALERTES (placeholder)
# ============================================================

class ConfigAlerte(BaseModel):
    """
    Configuration des seuils d'alerte.

    ⚠️ Placeholder pour l'instant : sera utilisé plus tard pour
    personnaliser les seuils (ex : 30 jours avant expiration).
    """

    TYPE_CHOICES = [
        ('stock_critique', 'Stock critique'),
        ('stock_alerte', 'Stock en alerte'),
        ('contrat_expirant', 'Contrat expirant'),
        ('document_expirant', 'Document expirant'),
        ('assurance_expirant', 'Assurance expirant'),
        ('facture_impayee', 'Facture impayée'),
        ('conge_en_attente', 'Congé en attente'),
        ('paie_en_attente', 'Paie en attente'),
        ('mission_en_cours', 'Mission en cours'),
        ('incident_ouvert', 'Incident ouvert'),
        ('permis_expire', 'Permis expiré'),
        ('consommation_alerte', 'Consommation carburant élevée'),
    ]

    GRAVITE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('critical', 'Critique'),
    ]

    type = models.CharField(
        max_length=50, choices=TYPE_CHOICES, unique=True,
        verbose_name="Type d'alerte"
    )
    libelle = models.CharField(
        max_length=200, verbose_name="Libellé")
    description = models.TextField(
        blank=True, verbose_name="Description")
    gravite = models.CharField(
        max_length=20, choices=GRAVITE_CHOICES, default='warning',
        verbose_name="Gravité"
    )
    seuil_jours = models.IntegerField(
        default=30, verbose_name="Seuil en jours",
        help_text="Nombre de jours avant l'échéance pour déclencher l'alerte"
    )
    seuil_valeur = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Seuil en valeur",
        help_text="Quantité ou montant seuil (0 = non utilisé)"
    )
    active = models.BooleanField(
        default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Configuration d'alerte"
        verbose_name_plural = "Configurations d'alertes"
        ordering = ['type']

    def __str__(self):
        return f"{self.get_type_display()} — {self.libelle}"


# ============================================================
# CANAL DE NOTIFICATION (placeholder)
# ============================================================

class CanalNotification(BaseModel):
    """
    Canaux de diffusion des notifications.

    ⚠️ Placeholder : permet de configurer comment les alertes
    sont envoyées (email, SMS, push…).
    """

    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification push'),
        ('in_app', 'Notification in-app'),
        ('whatsapp', 'WhatsApp'),
    ]

    nom = models.CharField(
        max_length=100, verbose_name="Nom du canal")
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, verbose_name="Type de canal")
    configuration = models.JSONField(
        default=dict, blank=True,
        verbose_name="Configuration JSON",
        help_text="Paramètres spécifiques (SMTP, API key, etc.)"
    )
    actif = models.BooleanField(
        default=True, verbose_name="Actif")
    ordre = models.IntegerField(
        default=0, verbose_name="Ordre de priorité")

    class Meta:
        verbose_name = "Canal de notification"
        verbose_name_plural = "Canaux de notification"
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
