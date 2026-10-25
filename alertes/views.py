# alertes/views.py
"""
Agrégateur d'alertes APG.

Toutes les alertes sont calculées à la volée en interrogeant les autres modules.
Aucune donnée n'est stockée en base (sauf ConfigAlerte et CanalNotification qui
sont des placeholders).

Le pattern _safe_get() garantit que :
- si un endpoint n'existe pas → on ignore silencieusement
- si la réponse est {results: []} ou [] → on normalise
- si la réponse est {count: N} → on génère N alertes génériques
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from datetime import date, timedelta

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination
from .models import ConfigAlerte, CanalNotification
from .serializers import ConfigAlerteSerializer, CanalNotificationSerializer


# ============================================================
# HELPERS D'AGRÉGATION
# ============================================================

def _safe_get(request, url):
    """
    Appelle un endpoint en absorbant les erreurs.
    Retourne une liste normalisée (toujours un tableau).
    """
    import requests
    from django.conf import settings

    try:
        base = request.build_absolute_uri('/').rstrip('/')
        full_url = f"{base}{url}"
        headers = {}
        if request.auth:
            headers['Authorization'] = f"Token {request.auth}"
        # Ou si auth est un Token object
        elif hasattr(request, 'user') and request.user.is_authenticated:
            headers['Authorization'] = f"Token {request.user.auth_token.key}" if hasattr(request.user, 'auth_token') else ''

        resp = requests.get(full_url, headers=headers, timeout=3)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'results' in data:
                return data['results']
            if 'count' in data and data['count'] > 0:
                return [{'id': i} for i in range(data['count'])]
        return []
    except Exception:
        return []


def _normaliser_alerte(item, type_alerte, module, gravite='warning', url_detail=None):
    """
    Transforme n'importe quel objet en alerte normalisée.
    Utilise getattr/defensive pour absorber les variations de format.
    """
    if not isinstance(item, dict):
        item = {}

    # Titre : on cherche dans plusieurs champs possibles
    titre = (
        item.get('titre') or
        item.get('nom') or
        item.get('objet') or
        item.get('designation') or
        item.get('numero') or
        item.get('reference') or
        item.get('label') or
        f"{module} #{item.get('id', '?')}"
    )

    # Description
    description = (
        item.get('description') or
        item.get('observation') or
        item.get('motif') or
        item.get('notes') or
        item.get('commentaire') or
        ''
    )

    # Date
    date_val = (
        item.get('created_at') or
        item.get('date_creation') or
        item.get('date') or
        item.get('date_document') or
        item.get('date_echeance') or
        item.get('date_expiration') or
        item.get('date_fin') or
        item.get('date_mission') or
        None
    )

    # ID unique
    id_alerte = item.get('id') or item.get('numero') or item.get('reference') or '?'
    unique_id = f"{module}-{type_alerte}-{id_alerte}"

    return {
        'id': unique_id,
        'type': type_alerte,
        'module': module,
        'titre': str(titre)[:200],
        'description': str(description)[:500],
        'date': date_val,
        'gravite': gravite,
        'url': url_detail or '#',
        'data': item,  # objet brut pour debug/référence
    }


def _fetch_alertes_module(request, module_name, sources):
    """
    sources = liste de tuples (url, type_alerte, gravite, url_detail_prefix)
    Retourne une liste d'alertes normalisées.
    """
    alertes = []
    for url, type_alerte, gravite, url_prefix in sources:
        items = _safe_get(request, url)
        for item in items:
            item_id = item.get('id') if isinstance(item, dict) else None
            url_detail = f"{url_prefix}{item_id}/" if item_id else '#'
            alertes.append(
                _normaliser_alerte(item, type_alerte, module_name, gravite, url_detail)
            )
    return alertes


def _fetch_alertes_rh(request):
    """Agrège les alertes RH."""
    sources = [
        ('/conges/en-attente/', 'conge_en_attente', 'warning', '/conges/'),
        ('/contrats/expirant/', 'contrat_expirant', 'error', '/contrats/'),
        ('/presences/en-attente/', 'presence_en_attente', 'info', '/presences/'),
        ('/absences/non-justifiees/', 'absence_non_justifiee', 'warning', '/absences/'),
    ]
    return _fetch_alertes_module(request, 'rh', sources)


def _fetch_alertes_paie(request):
    """Agrège les alertes Paie."""
    sources = [
        ('/paie/en-attente/', 'paie_en_attente', 'warning', '/paie/'),
        ('/paie-periodes/?statut=en_attente', 'periode_paie', 'info', '/paie-periodes/'),
        ('/avances-salaire/?statut=en_attente', 'avance_salaire', 'info', '/avances-salaire/'),
    ]
    return _fetch_alertes_module(request, 'paie', sources)


def _fetch_alertes_achats(request):
    """Agrège les alertes Achats."""
    sources = [
        ('/factures-fournisseurs/impayees/', 'facture_impayee', 'error', '/factures-fournisseurs/'),
        ('/factures-fournisseurs/echues/', 'facture_echue', 'critical', '/factures-fournisseurs/'),
        ('/demandes-achat/en_attente/', 'demande_achat_en_attente', 'warning', '/demandes-achat/'),
        ('/validations/en-attente/', 'validation_en_attente', 'info', '/validations/'),
        ('/depenses/en-attente/', 'depense_en_attente', 'info', '/decaissements/'),
        ('/bons-commande/?statut=brouillon', 'bon_commande_brouillon', 'info', '/bons-commande/'),
    ]
    return _fetch_alertes_module(request, 'achats', sources)


def _fetch_alertes_stocks(request):
    """Agrège les alertes Stocks."""
    sources = [
        ('/articles/stock_critique/', 'stock_critique', 'critical', '/articles/'),
        ('/articles/en_alerte/', 'stock_alerte', 'warning', '/articles/'),
        ('/inventaires/?statut=en_cours', 'inventaire_en_cours', 'info', '/inventaire/'),
        ('/maintenances/?statut=planifiee', 'maintenance_planifiee', 'info', '/maintenances/'),
    ]
    return _fetch_alertes_module(request, 'stocks', sources)


def _fetch_alertes_vehicules(request):
    """Agrège les alertes Véhicules."""
    sources = [
        ('/assurances/qui_expirent/', 'assurance_expirant', 'warning', '/assurances/'),
        ('/assurances/expirees/', 'assurance_expiree', 'error', '/assurances/'),
        ('/conducteurs/permis_expires/', 'permis_expire', 'error', '/conducteurs/'),
        ('/documents-vehicules/qui_expirent/', 'document_vehicule_expirant', 'warning', '/documents-vehicules/'),
        ('/pleins-carburant/alertes/', 'consommation_alerte', 'warning', '/carburant/'),
        ('/vehicules/maintenance/', 'vehicule_en_maintenance', 'info', '/tricycles/'),
    ]
    return _fetch_alertes_module(request, 'vehicules', sources)


def _fetch_alertes_documents(request):
    """Agrège les alertes Documents."""
    sources = [
        ('/documents/expirent/', 'document_expirant', 'warning', '/documents/'),
        ('/documents/expires/', 'document_expire', 'error', '/documents/'),
    ]
    return _fetch_alertes_module(request, 'documents', sources)


def _fetch_alertes_exploitation(request):
    """Agrège les alertes Exploitation."""
    sources = [
        ('/missions/en-cours/', 'mission_en_cours', 'info', '/missions/'),
        ('/incidents/ouverts/', 'incident_ouvert', 'error', '/incidents/'),
        ('/incidents/?gravite=critique&statut=ouvert', 'incident_critique', 'critical', '/incidents/'),
    ]
    return _fetch_alertes_module(request, 'exploitation', sources)


def _toutes_alertes(request):
    """Récupère TOUTES les alertes de tous les modules."""
    return (
        _fetch_alertes_rh(request) +
        _fetch_alertes_paie(request) +
        _fetch_alertes_achats(request) +
        _fetch_alertes_stocks(request) +
        _fetch_alertes_vehicules(request) +
        _fetch_alertes_documents(request) +
        _fetch_alertes_exploitation(request)
    )


# ============================================================
# VUES
# ============================================================

class AlertesViewset(viewsets.ViewSet):
    """
    Vue agrégée des alertes.
    Pas de CRUD — uniquement des actions de lecture.
    """

    def get_permissions(self):
        return [CanViewPersonnel()]

    @action(detail=False, methods=['get'])
    def toutes(self, request):
        """Toutes les alertes de tous les modules."""
        alertes = _toutes_alertes(request)
        # Trier par gravité (critical > error > warning > info) puis par date
        ordre_gravite = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}
        alertes.sort(key=lambda a: (
            ordre_gravite.get(a['gravite'], 9),
            a['date'] or '9999',
        ))
        return Response({
            'total': len(alertes),
            'alertes': alertes,
            'par_module': self._compter_par_module(alertes),
            'par_gravite': self._compter_par_gravite(alertes),
        })

    @action(detail=False, methods=['get'])
    def rh(self, request):
        """Alertes RH."""
        alertes = _fetch_alertes_rh(request)
        return Response({
            'module': 'rh',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def paie(self, request):
        """Alertes Paie."""
        alertes = _fetch_alertes_paie(request)
        return Response({
            'module': 'paie',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def finance(self, request):
        """Alertes Finance (Achats + Paie + Trésorerie)."""
        alertes = _fetch_alertes_achats(request) + _fetch_alertes_paie(request)
        return Response({
            'module': 'finance',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def logistique(self, request):
        """Alertes Logistique (Stocks + Carburant)."""
        alertes = _fetch_alertes_stocks(request)
        return Response({
            'module': 'logistique',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def vehicules(self, request):
        """Alertes Véhicules."""
        alertes = _fetch_alertes_vehicules(request)
        return Response({
            'module': 'vehicules',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def exploitation(self, request):
        """Alertes Exploitation."""
        alertes = _fetch_alertes_exploitation(request)
        return Response({
            'module': 'exploitation',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def documents(self, request):
        """Alertes Documents."""
        alertes = _fetch_alertes_documents(request)
        return Response({
            'module': 'documents',
            'total': len(alertes),
            'alertes': alertes,
        })

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales (sans le détail)."""
        alertes = _toutes_alertes(request)
        return Response({
            'total': len(alertes),
            'par_module': self._compter_par_module(alertes),
            'par_gravite': self._compter_par_gravite(alertes),
        })

    # ============================================================
    # HELPERS DE COMPTAGE
    # ============================================================

    @staticmethod
    def _compter_par_module(alertes):
        counts = {}
        for a in alertes:
            m = a['module']
            counts[m] = counts.get(m, 0) + 1
        return counts

    @staticmethod
    def _compter_par_gravite(alertes):
        counts = {}
        for a in alertes:
            g = a['gravite']
            counts[g] = counts.get(g, 0) + 1
        return counts


# ============================================================
# CONFIG & CANAUX (CRUD standards)
# ============================================================

class ConfigAlerteViewset(viewsets.ModelViewSet):
    """CRUD Configurations d'alertes."""
    queryset = ConfigAlerte.objects.all()
    serializer_class = ConfigAlerteSerializer
    pagination_class = StandardPagination
    filterset_fields = ['type', 'gravite', 'active']
    ordering_fields = ['type', 'gravite']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CanalNotificationViewset(viewsets.ModelViewSet):
    """CRUD Canaux de notification."""
    queryset = CanalNotification.objects.all()
    serializer_class = CanalNotificationSerializer
    pagination_class = StandardPagination
    filterset_fields = ['type', 'actif']
    ordering_fields = ['ordre', 'nom']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)