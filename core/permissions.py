# core/permissions.py
"""
Permissions DRF centralisées pour toute la plateforme APG.
Copiées depuis users/permissions.py pour être accessibles sans import circulaire.
"""
from rest_framework import permissions


# ============================================================
# RÔLES DE BASE
# ============================================================

class IsPDG(permissions.BasePermission):
    """PDG / Administrateur Général uniquement."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsRH(permissions.BasePermission):
    """RH + PDG."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin', 'rh']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsComptable(permissions.BasePermission):
    """Comptable + PDG."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin', 'comptable']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsLogistique(permissions.BasePermission):
    """Logistique + PDG."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin', 'logistique']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsSuperviseur(permissions.BasePermission):
    """Superviseur + PDG."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin', 'superviseur']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsEmploye(permissions.BasePermission):
    """Tout utilisateur authentifié."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated


# ============================================================
# PERMISSIONS COMBINÉES
# ============================================================

class IsStaff(permissions.BasePermission):
    """Tous les responsables + PDG (sauf 'employe')."""
    STAFF_ROLES = ['pdg', 'admin', 'rh',
                   'comptable', 'logistique', 'superviseur']

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in self.STAFF_ROLES
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsStaffOrReadOnly(permissions.BasePermission):
    """Lecture pour tous, écriture pour staff."""
    STAFF_ROLES = ['pdg', 'admin', 'rh',
                   'comptable', 'logistique', 'superviseur']

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user and request.user.is_authenticated
            and request.user.role in self.STAFF_ROLES
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsPDGOrReadOnly(permissions.BasePermission):
    """Lecture pour tous, écriture pour PDG."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ['pdg', 'admin']
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


# ============================================================
# PROPRIÉTÉ
# ============================================================

class IsOwnerOrStaff(permissions.BasePermission):
    """L'utilisateur peut modifier ses propres données, le staff tout."""
    STAFF_ROLES = ['pdg', 'admin', 'rh',
                   'comptable', 'logistique', 'superviseur']

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.role in self.STAFF_ROLES:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif obj == request.user:
            return True
        return False


# ============================================================
# PERMISSION GRANULAIRE (basée sur CustomUser.has_permission)
# ============================================================

class HasRolePermission(permissions.BasePermission):
    """Vérifie user.has_permission('xxx')."""

    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_permission(self.required_permission)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


# ============================================================
# FACTORY — Génère des permissions dynamiquement
# ============================================================

class PermissionFactory:
    @staticmethod
    def require_permission(permission_name):
        return type(
            f'Require_{permission_name}',
            (permissions.BasePermission,),
            {
                'has_permission': lambda self, request, view: (
                    request.user and request.user.is_authenticated
                    and request.user.has_permission(permission_name)
                ),
                'has_object_permission': lambda self, request, view, obj: (
                    request.user and request.user.is_authenticated
                    and request.user.has_permission(permission_name)
                ),
            },
        )

    @staticmethod
    def require_any_role(roles):
        return type(
            'RequireAnyRole',
            (permissions.BasePermission,),
            {
                'has_permission': lambda self, request, view: (
                    request.user and request.user.is_authenticated
                    and request.user.role in roles
                ),
                'has_object_permission': lambda self, request, view, obj: (
                    request.user and request.user.is_authenticated
                    and request.user.role in roles
                ),
            },
        )


# ============================================================
# PERMISSIONS MÉTIER APG
# ============================================================

# ----- RH -----
class CanViewPersonnel(permissions.BasePermission):
    ALLOWED = ['pdg', 'admin', 'rh', 'comptable', 'logistique', 'superviseur']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditPersonnel(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'rh'])


class CanViewPaie(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'rh', 'comptable'])


class CanPreparePaie(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'rh'])


class CanValidatePaie(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin'])


class CanValidateConges(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'rh'])


# ----- Facturation / Comptabilité -----
class CanViewFactures(permissions.BasePermission):
    ALLOWED = ['pdg', 'admin', 'comptable', 'rh', 'logistique', 'superviseur']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditFactures(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'comptable'])


class CanValidateFactures(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'comptable'])


class CanViewFinances(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'comptable'])


class CanManageFinances(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'comptable'])


# ----- Logistique -----
class CanViewStocks(permissions.BasePermission):
    ALLOWED = ['pdg', 'admin', 'logistique', 'comptable', 'rh', 'superviseur']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanManageStocks(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique'])


class CanManageTricycles(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique'])


class CanManageVehicules(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique'])


class CanManageCarburant(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique'])


class CanManageMaintenance(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique'])


# ----- Exploitation -----
class CanManageMissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'superviseur'])


class CanManageEquipes(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'superviseur'])


# ----- Workflow -----
class CanCreateDemandeDecaissement(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'logistique', 'superviseur'])


class CanValidateDemandeDecaissement(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin'])


class CanEffectuerPaiement(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin', 'comptable'])


# ----- Administration -----
class CanViewUsers(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin'])


class CanManageUsers(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin'])


class CanViewAuditLog(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in ['pdg', 'admin'])


class CanViewReports(permissions.BasePermission):
    ALLOWED = ['pdg', 'admin', 'rh', 'comptable', 'logistique', 'superviseur']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ALIAS DE COMPATIBILITÉ
# ============================================================
IsAdmin = IsPDG
IsGestionnaire = IsStaff
IsMagasinier = IsLogistique
IsCaissier = IsComptable
IsLivreur = IsSuperviseur
IsAdminOrReadOnly = IsPDGOrReadOnly
# ============================================================
# ✅ PERMISSIONS CLIENTS (ajout)
# ============================================================


class CanViewClients(permissions.BasePermission):
    """Lecture des clients : PDG, Comptable, RH, Superviseur, Logistique, Trésorier."""
    ALLOWED = ['pdg', 'admin', 'comptable', 'rh',
               'superviseur', 'logistique', 'tresorier']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanEditClients(permissions.BasePermission):
    """Écriture sur les clients : PDG et Comptable."""
    ALLOWED = ['pdg', 'admin', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


# ============================================================
# ✅ PERMISSIONS COMPTABILITÉ (ajout)
# ============================================================

class CanViewComptabilite(permissions.BasePermission):
    """Lecture comptabilité : PDG, Comptable."""
    ALLOWED = ['pdg', 'admin', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditComptabilite(permissions.BasePermission):
    """Écriture comptabilité : PDG, Comptable."""
    ALLOWED = ['pdg', 'admin', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS TRÉSORERIE (ajout)
# ============================================================

class CanViewTresorerie(permissions.BasePermission):
    """Lecture trésorerie : PDG, Comptable, Trésorier."""
    ALLOWED = ['pdg', 'admin', 'comptable', 'tresorier']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditTresorerie(permissions.BasePermission):
    """Écriture trésorerie : PDG, Comptable, Trésorier."""
    ALLOWED = ['pdg', 'admin', 'comptable', 'tresorier']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanValidatePaiements(permissions.BasePermission):
    """Validation paiements : PDG, Comptable."""
    ALLOWED = ['pdg', 'admin', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS VÉHICULES (ajout)
# ============================================================

class CanViewVehicules(permissions.BasePermission):
    """Lecture véhicules : PDG, Logistique, Superviseur, Comptable."""
    ALLOWED = ['pdg', 'admin', 'logistique', 'superviseur', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditVehicules(permissions.BasePermission):
    """Écriture véhicules : PDG, Logistique."""
    ALLOWED = ['pdg', 'admin', 'logistique']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS CARBURANT (ajout)
# ============================================================

class CanViewCarburant(permissions.BasePermission):
    """Lecture carburant : PDG, Logistique, Comptable."""
    ALLOWED = ['pdg', 'admin', 'logistique', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditCarburant(permissions.BasePermission):
    """Écriture carburant : PDG, Logistique."""
    ALLOWED = ['pdg', 'admin', 'logistique']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS MAINTENANCE (ajout)
# ============================================================

class CanViewMaintenance(permissions.BasePermission):
    """Lecture maintenance : PDG, Logistique, Superviseur, Comptable."""
    ALLOWED = ['pdg', 'admin', 'logistique', 'superviseur', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditMaintenance(permissions.BasePermission):
    """Écriture maintenance : PDG, Logistique."""
    ALLOWED = ['pdg', 'admin', 'logistique']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS EXPLOITATION (ajout)
# ============================================================

class CanViewExploitation(permissions.BasePermission):
    """Lecture exploitation : PDG, Superviseur, RH, Logistique."""
    ALLOWED = ['pdg', 'admin', 'superviseur', 'rh', 'logistique']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditExploitation(permissions.BasePermission):
    """Écriture exploitation : PDG, Superviseur."""
    ALLOWED = ['pdg', 'admin', 'superviseur']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS ACHATS (ajout)
# ============================================================

class CanViewAchats(permissions.BasePermission):
    """Lecture achats : PDG, Logistique, Comptable."""
    ALLOWED = ['pdg', 'admin', 'logistique', 'comptable']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanEditAchats(permissions.BasePermission):
    """Écriture achats : PDG, Logistique."""
    ALLOWED = ['pdg', 'admin', 'logistique']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


class CanValidateAchats(permissions.BasePermission):
    """Validation achats : PDG uniquement."""
    ALLOWED = ['pdg', 'admin']

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated
                and request.user.role in self.ALLOWED)


# ============================================================
# ✅ PERMISSIONS DOCUMENTS (ajout)
# ============================================================

class CanViewDocuments(permissions.BasePermission):
    """Lecture documents : tout utilisateur authentifié."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanEditDocuments(permissions.BasePermission):
    """Écriture documents : tout utilisateur authentifié."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
