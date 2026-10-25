# alertes/views.py
"""
Agrégateur d'alertes APG.

Toutes les alertes sont calculées à la volée en interrogeant les autres modules.
Aucune donnée n'est stockée en base (sauf ConfigAlerte et CanalNotification qui
sont des placeholders).

✅ Compatible production Render / derrière proxy :
   - utilise request.get_host() au lieu de build_absolute_uri()
   - respecte X-Forwarded-Proto (HTTPS terminé par le proxy)
   - timeout 5s par appel
   - logs structurés pour diagnostic
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from datetime import date, timedelta

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination
from .models import ConfigAlerte, CanalNotification
from .serializers import ConfigAlerteSerializer, CanalNotificationSerializer


logger = logging.getLogger(__name__)


# ============================================================
# HELPERS D'AGRÉGATION
# ============================================================

def _get_base_url(request):
    """
    Construit l'URL de base du backend en respectant le proxy Render.

    ✅ Correction production :
    - Render termine le HTTPS puis transmet en HTTP au conteneur
    - request.get_host() retourne le vrai domaine public
    - HTTP_X_FORWARDED_PROTO = 'https' quand derrière le proxy
    """
    host = request.get_host()
    scheme = 'https' if (
        request.is_secure() or
        request.META.get('HTTP_X_FORWARDED_PROTO') == 'https'
    ) else 'http'
    return f"{scheme}://{host}"


def _safe_get(request, url):
    """
    Appelle un endpoint en absorbant les erreurs.
    Retourne une liste normalisée (toujours un tableau).

    ✅ Corrigé pour production : utilise _get_base_url() au lieu de
    request.build_absolute_uri() qui casse derrière un proxy.
    """
    import requests

    try:
        base = _get_base_url(request)
        full_url = f"{base}{url}"

        headers = {}
        if request.auth:
            headers['Authorization'] = f"Token {request.auth}"

        logger.debug(f"[alertes] GET {full_url}")

        resp = requests.get(full_url, headers=headers, timeout=5)

        if resp.status_code != 200:
            logger.warning(
                f"[alertes] {full_url} → HTTP {resp.status_code}"
            )
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
    except Exception as e:
        logger.warning(f"[alertes] Erreur {url}: {type(e).__name__}: {e}")
        return []


def _normaliser_alerte(item, type_alerte, module, gravite='warning', url_detail=None):
    """Transforme n'importe quel objet en alerte normalisée."""
    if not isinstance(item, dict):
        item = {}

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

    description = (
        item.get('description') or
        item.get('observation') or
        item.get('motif') or
        item.get('notes') or
        item.get('commentaire') or
        ''
    )

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

    id_alerte = item.get('id') or item.get(
        'numero') or item.get('reference') or '?'
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
        'data': item,
    }


def _fetch_alertes_module(request, module_name, sources):
    """sources = liste de tuples (url, type_alerte, gravite, url_detail_prefix)"""
    alertes = []
    for url, type_alerte, gravite, url_prefix in sources:
        items = _safe_get(request, url)
        for item in items:
            item_id = item.get('id') if isinstance(item, dict) else None
            url_detail = f"{url_prefix}{item_id}/" if item_id else '#'
            alertes.append(
                _normaliser_alerte(item, type_alerte,
                                   module_name, gravite, url_detail)
            )
    return alertes


# ============================================================
# AGRÉGATEURS PAR MODULE
# ============================================================

def _fetch_alertes_rh(request):
    sources = [
        ('/conges/en-attente/', 'conge_en_attente', 'warning', '/conges/'),
        ('/contrats/expirant/', 'contrat_expirant', 'error', '/contrats/'),
        ('/presences/en-attente/', 'presence_en_attente', 'info', '/presences/'),
        ('/absences/non-justifiees/', 'absence_non_justifiee', 'warning', '/absences/'),
    ]
    return _fetch_alertes_module(request, 'rh', sources)


def _fetch_alertes_paie(request):
    sources = [
        ('/paie/en-attente/', 'paie_en_attente', 'warning', '/paie/'),
        ('/paie-periodes/?statut=en_attente',
         'periode_paie', 'info', '/paie-periodes/'),
        ('/avances-salaire/?statut=en_attente',
         'avance_salaire', 'info', '/avances-salaire/'),
    ]
    return _fetch_alertes_module(request, 'paie', sources)


def _fetch_alertes_achats(request):
    sources = [
        ('/factures-fournisseurs/impayees/', 'facture_impayee',
         'error', '/factures-fournisseurs/'),
        ('/factures-fournisseurs/echues/', 'facture_echue',
         'critical', '/factures-fournisseurs/'),
        ('/demandes-achat/en_attente/', 'demande_achat_en_attente',
         'warning', '/demandes-achat/'),
        ('/validations/en-attente/', 'validation_en_attente', 'info', '/validations/'),
        ('/depenses/en-attente/', 'depense_en_attente', 'info', '/decaissements/'),
        ('/bons-commande/?statut=brouillon',
         'bon_commande_brouillon', 'info', '/bons-commande/'),
    ]
    return _fetch_alertes_module(request, 'achats', sources)


def _fetch_alertes_stocks(request):
    sources = [
        ('/articles/stock_critique/', 'stock_critique', 'critical', '/articles/'),
        ('/articles/en_alerte/', 'stock_alerte', 'warning', '/articles/'),
        ('/inventaires/?statut=en_cours',
         'inventaire_en_cours', 'info', '/inventaire/'),
        ('/maintenances/?statut=planifiee',
         'maintenance_planifiee', 'info', '/maintenances/'),
    ]
    return _fetch_alertes_module(request, 'stocks', sources)


def _fetch_alertes_vehicules(request):
    sources = [
        ('/assurances/qui_expirent/', 'assurance_expirant', 'warning', '/assurances/'),
        ('/assurances/expirees/', 'assurance_expiree', 'error', '/assurances/'),
        ('/conducteurs/permis_expires/', 'permis_expire', 'error', '/conducteurs/'),
        ('/documents-vehicules/qui_expirent/',
         'document_vehicule_expirant', 'warning', '/documents-vehicules/'),
        ('/pleins-carburant/alertes/', 'consommation_alerte', 'warning', '/carburant/'),
        ('/vehicules/maintenance/', 'vehicule_en_maintenance', 'info', '/tricycles/'),
    ]
    return _fetch_alertes_module(request, 'vehicules', sources)


def _fetch_alertes_documents(request):
    sources = [
        ('/documents/expirent/', 'document_expirant', 'warning', '/documents/'),
        ('/documents/expires/', 'document_expire', 'error', '/documents/'),
    ]
    return _fetch_alertes_module(request, 'documents', sources)


def _fetch_alertes_exploitation(request):
    sources = [
        ('/missions/en-cours/', 'mission_en_cours', 'info', '/missions/'),
        ('/incidents/ouverts/', 'incident_ouvert', 'error', '/incidents/'),
        ('/incidents/?gravite=critique&statut=ouvert',
         'incident_critique', 'critical', '/incidents/'),
    ]
    return _fetch_alertes_module(request, 'exploitation', sources)


def _toutes_alertes(request):
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
        alertes = _fetch_alertes_rh(request)
        return Response({'module': 'rh', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def paie(self, request):
        alertes = _fetch_alertes_paie(request)
        return Response({'module': 'paie', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def finance(self, request):
        alertes = _fetch_alertes_achats(request) + _fetch_alertes_paie(request)
        return Response({'module': 'finance', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def logistique(self, request):
        alertes = _fetch_alertes_stocks(request)
        return Response({'module': 'logistique', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def vehicules(self, request):
        alertes = _fetch_alertes_vehicules(request)
        return Response({'module': 'vehicules', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def exploitation(self, request):
        alertes = _fetch_alertes_exploitation(request)
        return Response({'module': 'exploitation', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def documents(self, request):
        alertes = _fetch_alertes_documents(request)
        return Response({'module': 'documents', 'total': len(alertes), 'alertes': alertes})

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        alertes = _toutes_alertes(request)
        return Response({
            'total': len(alertes),
            'par_module': self._compter_par_module(alertes),
            'par_gravite': self._compter_par_gravite(alertes),
        })

    # ============================================================
    # ✅ NOUVEAU — Endpoint de debug
    # ============================================================

    @action(detail=False, methods=['get'])
    def debug(self, request):
        """
        Diagnostic de connectivité des endpoints agrégés.

        Retourne pour chaque endpoint :
        - l'URL testée
        - le statut HTTP
        - le nombre d'items
        - l'erreur éventuelle

        ⚠️ À utiliser uniquement pour le diagnostic.
        """
        import requests

        base = _get_base_url(request)
        headers = {}
        if request.auth:
            headers['Authorization'] = f"Token {request.auth}"

        endpoints_a_tester = [
            # RH
            '/conges/en-attente/',
            '/contrats/expirant/',
            '/presences/en-attente/',
            '/absences/non-justifiees/',
            # Paie
            '/paie/en-attente/',
            '/paie-periodes/?statut=en_attente',
            '/avances-salaire/?statut=en_attente',
            # Achats
            '/factures-fournisseurs/impayees/',
            '/factures-fournisseurs/echues/',
            '/demandes-achat/en_attente/',
            '/validations/en-attente/',
            '/depenses/en-attente/',
            '/bons-commande/?statut=brouillon',
            # Stocks
            '/articles/stock_critique/',
            '/articles/en_alerte/',
            '/inventaires/?statut=en_cours',
            '/maintenances/?statut=planifiee',
            # Véhicules
            '/assurances/qui_expirent/',
            '/assurances/expirees/',
            '/conducteurs/permis_expires/',
            '/documents-vehicules/qui_expirent/',
            '/pleins-carburant/alertes/',
            '/vehicules/maintenance/',
            # Documents
            '/documents/expirent/',
            '/documents/expires/',
            # Exploitation
            '/missions/en-cours/',
            '/incidents/ouverts/',
            '/incidents/?gravite=critique&statut=ouvert',
        ]

        resultats = []
        for endpoint in endpoints_a_tester:
            full_url = f"{base}{endpoint}"
            try:
                resp = requests.get(full_url, headers=headers, timeout=5)
                items = []
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = data.get(
                                'results', data.get('alertes', []))
                    except Exception:
                        pass

                resultats.append({
                    'endpoint': endpoint,
                    'full_url': full_url,
                    'status': resp.status_code,
                    'count': len(items) if isinstance(items, list) else 0,
                    'error': None if resp.status_code == 200 else f"HTTP {resp.status_code}",
                })
            except Exception as e:
                resultats.append({
                    'endpoint': endpoint,
                    'full_url': full_url,
                    'status': None,
                    'count': 0,
                    'error': f"{type(e).__name__}: {str(e)}",
                })

        # Résumé
        ok = sum(1 for r in resultats if r['status'] == 200)
        ko = len(resultats) - ok

        return Response({
            'base_url': base,
            'auth': bool(request.auth),
            'total_endpoints': len(resultats),
            'ok': ok,
            'ko': ko,
            'details': resultats,
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
