# core/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


# ============================================================
# MODÈLES ABSTRAITS DE BASE
# ============================================================

class BaseModel(models.Model):
    """
    Modèle abstrait : horodatage + utilisateur créateur/modificateur.
    À hériter dans tous les modèles métier APG.
    """
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_created',
        on_delete=models.SET_NULL,
        verbose_name="Créé par",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        on_delete=models.SET_NULL,
        verbose_name="Modifié par",
    )

    class Meta:
        abstract = True


class SoftDeleteModel(BaseModel):
    """
    Ajoute la suppression logique : rien n'est supprimé physiquement.
    Conforme au cahier des charges APG (principe d'archivage).
    """
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Supprimé le")
    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        on_delete=models.SET_NULL,
        verbose_name="Supprimé par",
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, user=None):
        """Suppression logique (soft delete)."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def hard_delete(self):
        """Suppression physique réelle (à utiliser avec précaution)."""
        super().delete()

    def restore(self):
        """Restaure un objet supprimé."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


# ============================================================
# MANAGERS PERSONNALISÉS
# ============================================================

class SoftDeleteManager(models.Manager):
    """Manager par défaut : exclut les objets supprimés."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager qui inclut TOUS les objets (même supprimés)."""

    def get_queryset(self):
        return super().get_queryset()


# ============================================================
# MIXIN — NUMÉROTATION AUTOMATIQUE
# ============================================================

class NumeroAutoMixin:
    """
    Mixin pour générer automatiquement des numéros type FACT-2026-000001.
    À utiliser dans les modèles qui ont un champ 'numero'.

    Exemple :
        class Facture(BaseModel, NumeroAutoMixin):
            PREFIX = 'FACT'
            numero = models.CharField(max_length=50, unique=True)
    """
    PREFIX = 'DOC'  # À surcharger dans chaque modèle

    def generate_numero(self):
        """Génère un numéro unique basé sur le préfixe + année + compteur."""
        from config.models import Numerotation  # ✅ CORRIGÉ : config au lieu de administration

        year = timezone.now().year
        num_config, created = Numerotation.objects.get_or_create(
            type_document=self.PREFIX,
            annee=year,
            defaults={
                'prefixe': self.PREFIX,
                'dernier_numero': 0,
            },
        )
        num_config.dernier_numero += 1
        num_config.save(update_fields=['dernier_numero'])

        try:
            return num_config.format.format(
                prefix=num_config.prefixe,
                year=year,
                num=num_config.dernier_numero,
            )
        except (KeyError, IndexError):
            # Fallback si le format est incorrect
            return f"{num_config.prefixe}-{year}-{num_config.dernier_numero:06d}"


# ============================================================
# MIXIN — AUDIT AUTOMATIQUE
# ============================================================

class AuditMixin:
    """
    Mixin pour tracer automatiquement les modifications.
    À utiliser avec BaseModel.
    """

    def save(self, *args, **kwargs):
        # Détecter si c'est une création ou modification
        if self.pk:
            self._log_audit('update')
        else:
            self._log_audit('create')
        super().save(*args, **kwargs)

    def _log_audit(self, action):
        """Enregistre dans le journal d'audit (import local pour éviter les cycles)."""
        try:
            from config.models import AuditLog  # ✅ CORRIGÉ : config au lieu de administration

            old_values = None
            if action == 'update' and self.pk:
                try:
                    old = self.__class__.objects.get(pk=self.pk)
                    old_values = {
                        field.name: str(getattr(old, field.name))
                        for field in self._meta.fields
                        if field.name not in ['updated_at']
                    }
                except self.__class__.DoesNotExist:
                    pass

            new_values = {
                field.name: str(getattr(self, field.name))
                for field in self._meta.fields
                if field.name not in ['updated_at']
            }

            AuditLog.objects.create(
                module=self._meta.app_label,
                action=action,
                model_name=self.__class__.__name__,
                object_id=self.pk,
                old_values=old_values,
                new_values=new_values,
            )
        except Exception:
            pass  # Ne jamais bloquer une opération métier à cause de l'audit
