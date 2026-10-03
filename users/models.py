from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django_rest_passwordreset.signals import reset_password_token_created
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is a required field')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'pdg')
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

    def create_pdg(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'pdg')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def create_rh(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'rh')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(email, password, **extra_fields)

    def create_comptable(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'comptable')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(email, password, **extra_fields)

    def create_logistique(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'logistique')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(email, password, **extra_fields)

    def create_superviseur(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'superviseur')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(email, password, **extra_fields)

    def create_employe(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'employe')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'PDG / Administrateur Général'),  # Compatibilité ancienne base
        ('pdg', 'PDG / Administrateur Général'),
        ('rh', 'Responsable RH'),
        ('comptable', 'Responsable Comptabilité'),
        ('logistique', 'Responsable Logistique'),
        ('superviseur', 'Responsable Exploitation / Superviseur'),
        ('employe', 'Employé'),
    )

    email = models.EmailField(max_length=200, unique=True)
    birthday = models.DateField(null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', null=True, blank=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employe'
    )

    is_online = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"

    # ---------- Propriétés de rôle (admin ET pdg = PDG) ----------

    @property
    def is_pdg(self):
        return self.role in ['pdg', 'admin']

    @property
    def is_rh(self):
        return self.role == 'rh'

    @property
    def is_comptable(self):
        return self.role == 'comptable'

    @property
    def is_logistique(self):
        return self.role == 'logistique'

    @property
    def is_superviseur(self):
        return self.role == 'superviseur'

    @property
    def is_employe(self):
        return self.role == 'employe'

    @property
    def has_admin_access(self):
        return self.role in ['pdg', 'admin']

    # ---------- Changement de rôle ----------

    def change_role(self, new_role):
        if new_role in dict(self.ROLE_CHOICES).keys():
            self.role = new_role
            if new_role in ['pdg', 'admin']:
                self.is_staff = True
                self.is_superuser = True
            else:
                self.is_staff = False
                self.is_superuser = False
            self.save()
            return True
        return False

    # ---------- Permissions granulaires ----------

    def get_permissions(self):
        # 'admin' est traité comme 'pdg'
        role = 'pdg' if self.role == 'admin' else self.role

        permissions = {
            'pdg': ['*'],
            'rh': [
                'view_personnel', 'edit_personnel',
                'view_contracts', 'edit_contracts',
                'view_presences', 'edit_presences',
                'view_conges', 'edit_conges', 'validate_conges',
                'prepare_paie', 'view_paie',
                'view_rh_reports', 'export_rh_reports',
                'view_own_profile', 'edit_own_profile',
            ],
            'comptable': [
                'view_factures', 'create_factures', 'edit_factures', 'validate_factures',
                'view_clients', 'edit_clients',
                'view_recouvrement', 'edit_recouvrement',
                'view_contrats', 'edit_contrats',
                'view_paiements', 'validate_paiements',
                'view_finances', 'manage_finances',
                'effectuer_paiement',
                'view_compta_reports', 'export_compta_reports',
                'view_personnel_readonly',
                'view_stocks_readonly',
                'view_own_profile', 'edit_own_profile',
            ],
            'logistique': [
                'view_stocks', 'edit_stocks', 'validate_stocks',
                'view_mouvements_stock', 'create_mouvements_stock',
                'view_equipements', 'edit_equipements',
                'view_tricycles', 'edit_tricycles',
                'view_vehicules', 'edit_vehicules',
                'view_carburant', 'edit_carburant',
                'view_maintenance', 'edit_maintenance',
                'view_affectations', 'edit_affectations',
                'create_demande_decaissement',
                'view_logistique_reports', 'export_logistique_reports',
                'view_personnel_readonly',
                'view_own_profile', 'edit_own_profile',
            ],
            'superviseur': [
                'view_missions', 'create_missions', 'edit_missions',
                'view_equipes', 'edit_equipes',
                'view_presences_terrain', 'edit_presences_terrain',
                'view_activites', 'edit_activites',
                'view_incidents', 'edit_incidents',
                'create_demande_decaissement',
                'view_rapports_terrain', 'export_rapports_terrain',
                'view_personnel_readonly',
                'view_stocks_readonly',
                'view_vehicules_readonly',
                'view_own_profile', 'edit_own_profile',
            ],
            'employe': [
                'view_own_profile', 'edit_own_profile',
                'view_own_presences',
                'view_own_conges', 'create_own_conge',
                'view_own_paie', 'download_own_bulletin',
                'view_own_notifications',
            ],
        }
        return permissions.get(role, [])

    def has_permission(self, permission):
        perms = self.get_permissions()
        if '*' in perms:
            return True
        return permission in perms

    def has_any_permission(self, *permissions):
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, *permissions):
        return all(self.has_permission(p) for p in permissions)


@receiver(reset_password_token_created)
def password_reset_token_created(reset_password_token, *args, **kwargs):
    sitelink = "http://localhost:5173/"
    token = "{}".format(reset_password_token.key)
    full_link = str(sitelink) + str("password-reset/") + str(token)

    print(f"Token généré: {token}")
    print(f"Lien complet: {full_link}")

    context = {
        'full_link': full_link,
        'email_address': reset_password_token.user.email,
        'user_name': reset_password_token.user.get_full_name() or reset_password_token.user.email,
        'role': reset_password_token.user.get_role_display(),
    }

    html_message = render_to_string("backend/email.html", context=context)
    plain_message = strip_tags(html_message)

    msg = EmailMultiAlternatives(
        subject="Réinitialisation de votre mot de passe - {}".format(
            reset_password_token.user.get_full_name() or reset_password_token.user.email
        ),
        body=plain_message,
        from_email="codelivecamp@gmail.com",
        to=[reset_password_token.user.email],
    )
    msg.attach_alternative(html_message, "text/html")
    msg.send()
