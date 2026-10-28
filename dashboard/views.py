# dashboard/views.py
"""
Agrégateur de statistiques pour le tableau de bord APG.

⚠️ Aucun modèle en base.
Toutes les données sont calculées via les models des autres modules.

Compatibilité production Render : utilise les models directement,
pas d'appel HTTP interne.
"""
import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from datetime import date, timedelta

from core.permissions import CanViewPersonnel


logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def _debut_mois():
    return date.today().replace(day=1)


def _debut_annee():
    return date.today().replace(month=1, day=1)


def _formater_montant(val):
    """Formatte un montant avec sécurité."""
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0


# ============================================================
# STATS FINANCIÈRES
# ============================================================

def _stats_financieres():
    """Statistiques financières (comptabilite + tresorerie)."""
    try:
        from comptabilite.models import Facture
        from tresorerie.models import Encaissement, Decaissement

        debut_mois = _debut_mois()
        debut_annee = _debut_annee()

        factures_qs = Facture.objects.all()
        factures_mois = factures_qs.filter(date_emission__gte=debut_mois)
        factures_annee = factures_qs.filter(date_emission__gte=debut_annee)

        creances = factures_qs.filter(
            statut__in=['emise', 'envoyee', 'partiellement_payee', 'en_retard']
        )

        enc_qs = Encaissement.objects.filter(statut='valide')
        enc_mois = enc_qs.filter(date_encaissement__gte=debut_mois)
        enc_annee = enc_qs.filter(date_encaissement__gte=debut_annee)

        dec_qs = Decaissement.objects.filter(statut__in=['valide', 'paye'])
        dec_mois = dec_qs.filter(date_demande__gte=debut_mois)
        dec_annee = dec_qs.filter(date_demande__gte=debut_annee)

        return {
            'factures': {
                'total': factures_qs.count(),
                'mois': factures_mois.count(),
                'annee': factures_annee.count(),
                'montant_total': _formater_montant(
                    factures_qs.aggregate(t=Sum('montant_ttc'))['t']
                ),
                'montant_mois': _formater_montant(
                    factures_mois.aggregate(t=Sum('montant_ttc'))['t']
                ),
                'montant_annee': _formater_montant(
                    factures_annee.aggregate(t=Sum('montant_ttc'))['t']
                ),
                'payees': factures_qs.filter(statut='payee').count(),
                'impayees': creances.count(),
            },
            'creances': {
                'total': _formater_montant(
                    creances.aggregate(t=Sum('montant_ttc'))['t']
                ),
                'nombre': creances.count(),
            },
            'encaissements': {
                'total': _formater_montant(
                    enc_qs.aggregate(t=Sum('montant'))['t']
                ),
                'mois': _formater_montant(
                    enc_mois.aggregate(t=Sum('montant'))['t']
                ),
                'annee': _formater_montant(
                    enc_annee.aggregate(t=Sum('montant'))['t']
                ),
                'nombre': enc_qs.count(),
            },
            'decaissements': {
                'total': _formater_montant(
                    dec_qs.aggregate(t=Sum('montant'))['t']
                ),
                'mois': _formater_montant(
                    dec_mois.aggregate(t=Sum('montant'))['t']
                ),
                'annee': _formater_montant(
                    dec_annee.aggregate(t=Sum('montant'))['t']
                ),
                'nombre': dec_qs.count(),
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] financier: {e}")
        return {
            'factures': {},
            'creances': {},
            'encaissements': {},
            'decaissements': {},
        }


# ============================================================
# STATS CLIENTS
# ============================================================

def _stats_clients():
    """Statistiques clients."""
    try:
        from clients.models import Client, ContratClient
        debut_mois = _debut_mois()

        qs = Client.objects.filter(is_deleted=False)
        contrats_qs = ContratClient.objects.all()

        expirant_30j = 0
        if contrats_qs.exists():
            expirant_30j = contrats_qs.filter(
                statut='actif',
                date_fin__lte=date.today() + timedelta(days=30),
                date_fin__gte=date.today(),
            ).count()

        return {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'nouveaux_mois': qs.filter(created_at__gte=debut_mois).count(),
            'par_type': list(
                qs.values('type').annotate(
                    total=Count('id')).order_by('-total')
            ),
            'contrats': {
                'total': contrats_qs.count(),
                'actifs': contrats_qs.filter(statut='actif').count(),
                'expirant_30j': expirant_30j,
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] clients: {e}")
        return {}


# ============================================================
# STATS STOCKS
# ============================================================

def _stats_stocks():
    """Statistiques stocks et articles."""
    try:
        from stocks.models import Article, Equipement, MouvementStock

        articles_qs = Article.objects.filter(is_deleted=False)
        equipements_qs = Equipement.objects.filter(is_deleted=False)
        mouvements_qs = MouvementStock.objects.all()

        critiques = 0
        alertes = 0
        valeur_stock = 0
        for a in articles_qs:
            if a.est_critique:
                critiques += 1
            elif a.est_en_alerte:
                alertes += 1
            valeur_stock += _formater_montant(
                a.stock_total
            ) * _formater_montant(a.prix_achat)

        return {
            'articles': {
                'total': articles_qs.count(),
                'actifs': articles_qs.filter(actif=True).count(),
                'critiques': critiques,
                'alertes': alertes,
                'valeur_stock': valeur_stock,
            },
            'equipements': {
                'total': equipements_qs.count(),
                'actifs': equipements_qs.filter(actif=True).count(),
                'valeur_acquisition': _formater_montant(
                    equipements_qs.aggregate(t=Sum('cout_acquisition'))['t']
                ),
            },
            'mouvements': {
                'total': mouvements_qs.count(),
                'ce_mois': mouvements_qs.filter(
                    date_mouvement__gte=_debut_mois()
                ).count(),
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] stocks: {e}")
        return {}


# ============================================================
# STATS VÉHICULES
# ============================================================

def _stats_vehicules():
    """Statistiques véhicules et carburant."""
    try:
        from vehicules.models import (
            Tricycle, Vehicule, Conducteur, PleinCarburant, Assurance
        )

        tricycles_qs = Tricycle.objects.filter(is_deleted=False)
        vehicules_qs = Vehicule.objects.filter(is_deleted=False)
        conducteurs_qs = Conducteur.objects.all()
        pleins_qs = PleinCarburant.objects.filter(date__gte=_debut_mois())
        assurances_qs = Assurance.objects.all()

        return {
            'tricycles': {
                'total': tricycles_qs.count(),
                'disponibles': tricycles_qs.filter(etat='disponible').count(),
                'en_mission': tricycles_qs.filter(etat='en_mission').count(),
                'en_panne': tricycles_qs.filter(
                    etat__in=['en_panne', 'hors_service']
                ).count(),
            },
            'vehicules': {
                'total': vehicules_qs.count(),
                'disponibles': vehicules_qs.filter(etat='disponible').count(),
            },
            'conducteurs': {
                'total': conducteurs_qs.count(),
                'actifs': conducteurs_qs.filter(actif=True).count(),
                'permis_expires': conducteurs_qs.filter(
                    date_expiration_permis__lt=date.today()
                ).count(),
            },
            'carburant': {
                'litres_mois': _formater_montant(
                    pleins_qs.aggregate(t=Sum('litres'))['t']
                ),
                'montant_mois': _formater_montant(
                    pleins_qs.aggregate(t=Sum('montant'))['t']
                ),
                'nombre_pleins': pleins_qs.count(),
            },
            'assurances': {
                'total': assurances_qs.count(),
                'expirees': assurances_qs.filter(
                    date_fin__lt=date.today()
                ).count(),
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] vehicules: {e}")
        return {}


# ============================================================
# STATS ACHATS
# ============================================================

def _stats_achats():
    """Statistiques achats."""
    try:
        from achats.models import (
            Fournisseur, BonCommande, FactureFournisseur, PaiementFournisseur
        )

        fournisseurs_qs = Fournisseur.objects.filter(is_deleted=False)
        bc_qs = BonCommande.objects.all()
        factures_qs = FactureFournisseur.objects.all()
        paiements_qs = PaiementFournisseur.objects.filter(statut='valide')

        return {
            'fournisseurs': {
                'total': fournisseurs_qs.count(),
                'actifs': fournisseurs_qs.filter(statut='actif').count(),
            },
            'bons_commande': {
                'total': bc_qs.count(),
                'en_cours': bc_qs.filter(
                    statut__in=['envoye', 'confirme', 'partiellement_recu']
                ).count(),
                'recus': bc_qs.filter(statut='recu').count(),
                'montant_total': _formater_montant(
                    bc_qs.aggregate(t=Sum('montant_ttc'))['t']
                ),
            },
            'factures': {
                'total': factures_qs.count(),
                'impayees': factures_qs.filter(
                    statut__in=['recue', 'controlee',
                                'validee', 'partiellement_payee']
                ).count(),
                'montant_total': _formater_montant(
                    factures_qs.aggregate(t=Sum('montant_ttc'))['t']
                ),
                'montant_paye': _formater_montant(
                    factures_qs.aggregate(t=Sum('montant_paye'))['t']
                ),
            },
            'paiements': {
                'total': paiements_qs.count(),
                'montant_total': _formater_montant(
                    paiements_qs.aggregate(t=Sum('montant'))['t']
                ),
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] achats: {e}")
        return {}


# ============================================================
# STATS EXPLOITATION
# ============================================================

def _stats_exploitation():
    """Statistiques exploitation."""
    try:
        from exploitation.models import Mission, Equipe, Incident, ActiviteTerrain

        debut_mois = _debut_mois()

        missions_qs = Mission.objects.all()
        equipes_qs = Equipe.objects.filter(actif=True)
        incidents_qs = Incident.objects.all()
        activites_qs = ActiviteTerrain.objects.filter(
            mission__date_mission__gte=debut_mois
        )

        tonnage_mois = _formater_montant(
            activites_qs.aggregate(t=Sum('quantite_collectee'))['t']
        )

        return {
            'missions': {
                'total': missions_qs.count(),
                'en_cours': missions_qs.filter(statut='en_cours').count(),
                'terminees': missions_qs.filter(statut='terminee').count(),
                'ce_mois': missions_qs.filter(
                    date_mission__gte=debut_mois
                ).count(),
            },
            'equipes': {
                'total': equipes_qs.count(),
                'disponibles': equipes_qs.filter(statut='disponible').count(),
                'en_mission': equipes_qs.filter(statut='en_mission').count(),
            },
            'incidents': {
                'total': incidents_qs.count(),
                'ouverts': incidents_qs.filter(
                    statut__in=['ouvert', 'en_cours']
                ).count(),
                'critiques': incidents_qs.filter(
                    gravite='critique', statut='ouvert'
                ).count(),
            },
            'activites': {
                'ce_mois': activites_qs.count(),
                'tonnage_mois': tonnage_mois,
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] exploitation: {e}")
        return {}


# ============================================================
# STATS RH ✅ CORRIGÉ
# ============================================================

def _stats_rh():
    """Statistiques RH."""
    try:
        from rh.models import Employe

        # Filter selon l'attribut is_deleted si présent
        if hasattr(Employe, 'is_deleted'):
            qs = Employe.objects.filter(is_deleted=False)
        else:
            qs = Employe.objects.all()

        # ✅ CORRIGÉ : plus de ternaire imbriquée
        actifs_count = qs.count()
        if qs.exists() and hasattr(qs.first(), 'statut'):
            actifs_count = qs.filter(statut='actif').count()

        return {
            'employes': {
                'total': qs.count(),
                'actifs': actifs_count,
            },
        }
    except Exception as e:
        logger.warning(f"[dashboard] rh: {e}")
        return {}


# ============================================================
# AGRÉGATEUR GLOBAL
# ============================================================

def _stats_globales():
    """Toutes les statistiques agrégées."""
    return {
        'date': date.today().isoformat(),
        'financier': _stats_financieres(),
        'clients': _stats_clients(),
        'stocks': _stats_stocks(),
        'vehicules': _stats_vehicules(),
        'achats': _stats_achats(),
        'exploitation': _stats_exploitation(),
        'rh': _stats_rh(),
    }


# ============================================================
# VIEWSETS
# ============================================================

class DashboardViewset(viewsets.ViewSet):
    """Tableau de bord principal (page /dashboard)."""

    def get_permissions(self):
        return [CanViewPersonnel()]

    def list(self, request):
        try:
            return Response(_stats_globales())
        except Exception as e:
            logger.exception("[dashboard] list")
            return Response({
                'error': 'Erreur lors du chargement du tableau de bord',
                'detail': str(e),
            }, status=500)


class StatistiquesViewset(viewsets.ViewSet):
    """Statistiques détaillées par module (page /statistiques)."""

    def get_permissions(self):
        return [CanViewPersonnel()]

    def list(self, request):
        try:
            return Response({
                'financier': _stats_financieres(),
                'clients': _stats_clients(),
                'stocks': _stats_stocks(),
                'vehicules': _stats_vehicules(),
                'achats': _stats_achats(),
                'exploitation': _stats_exploitation(),
                'rh': _stats_rh(),
            })
        except Exception as e:
            logger.exception("[dashboard] statistiques")
            return Response({
                'error': 'Erreur lors du chargement des statistiques',
                'detail': str(e),
            }, status=500)

    @action(detail=False, methods=['get'])
    def financier(self, request):
        return Response(_stats_financieres())

    @action(detail=False, methods=['get'])
    def clients(self, request):
        return Response(_stats_clients())

    @action(detail=False, methods=['get'])
    def stocks(self, request):
        return Response(_stats_stocks())

    @action(detail=False, methods=['get'])
    def vehicules(self, request):
        return Response(_stats_vehicules())

    @action(detail=False, methods=['get'])
    def achats(self, request):
        return Response(_stats_achats())

    @action(detail=False, methods=['get'])
    def exploitation(self, request):
        return Response(_stats_exploitation())

    @action(detail=False, methods=['get'])
    def rh(self, request):
        return Response(_stats_rh())


class AnalysesViewset(viewsets.ViewSet):
    """Analyses & rapports avancés (page /analyses)."""

    def get_permissions(self):
        return [CanViewPersonnel()]

    def list(self, request):
        try:
            return Response({
                'evolution_ca': self._evolution_ca(),
                'top_clients': self._top_clients(),
                'top_articles': self._top_articles(),
                'consommation_carburant': self._consommation_carburant(),
                'performances_missions': self._performances_missions(),
            })
        except Exception as e:
            logger.exception("[dashboard] analyses")
            return Response({
                'error': 'Erreur lors du chargement des analyses',
                'detail': str(e),
            }, status=500)

    @action(detail=False, methods=['get'])
    def evolution_ca(self, request):
        return Response(self._evolution_ca())

    @action(detail=False, methods=['get'])
    def top_clients(self, request):
        return Response(self._top_clients())

    @action(detail=False, methods=['get'])
    def top_articles(self, request):
        return Response(self._top_articles())

    @action(detail=False, methods=['get'])
    def consommation_carburant(self, request):
        return Response(self._consommation_carburant())

    @action(detail=False, methods=['get'])
    def performances_missions(self, request):
        return Response(self._performances_missions())

    @staticmethod
    def _evolution_ca():
        try:
            from comptabilite.models import Facture
            today = date.today()
            evolution = []
            for i in range(11, -1, -1):
                mois = today.month - i
                annee = today.year
                while mois <= 0:
                    mois += 12
                    annee -= 1

                debut = date(annee, mois, 1)
                if mois == 12:
                    fin = date(annee + 1, 1, 1) - timedelta(days=1)
                else:
                    fin = date(annee, mois + 1, 1) - timedelta(days=1)

                factures = Facture.objects.filter(
                    date_emission__gte=debut,
                    date_emission__lte=fin,
                    statut__in=['emise', 'envoyee',
                                'partiellement_payee', 'payee'],
                )
                evolution.append({
                    'mois': f"{mois:02d}/{annee}",
                    'montant': _formater_montant(
                        factures.aggregate(t=Sum('montant_ttc'))['t']
                    ),
                    'nombre': factures.count(),
                })
            return evolution
        except Exception as e:
            logger.warning(f"[dashboard] evolution_ca: {e}")
            return []

    @staticmethod
    def _top_clients():
        try:
            from comptabilite.models import Facture

            top = (
                Facture.objects
                .filter(statut__in=['emise', 'envoyee',
                                    'partiellement_payee', 'payee'])
                .values('client__id', 'client__code',
                        'client__nom', 'client__prenom')
                .annotate(
                    montant_total=Sum('montant_ttc'),
                    nombre_factures=Count('id'),
                )
                .order_by('-montant_total')[:10]
            )
            return [
                {
                    'client_id': t['client__id'],
                    'code': t['client__code'],
                    'nom': f"{t['client__prenom'] or ''} {t['client__nom']}".strip(),
                    'montant_total': _formater_montant(t['montant_total']),
                    'nombre_factures': t['nombre_factures'],
                }
                for t in top
            ]
        except Exception as e:
            logger.warning(f"[dashboard] top_clients: {e}")
            return []

    @staticmethod
    def _top_articles():
        try:
            from stocks.models import MouvementStock

            top = (
                MouvementStock.objects
                .values('article__id', 'article__code', 'article__designation')
                .annotate(
                    quantite_totale=Sum('quantite'),
                    nombre_mouvements=Count('id'),
                )
                .order_by('-quantite_totale')[:10]
            )
            return [
                {
                    'article_id': t['article__id'],
                    'code': t['article__code'],
                    'designation': t['article__designation'],
                    'quantite_totale': _formater_montant(t['quantite_totale']),
                    'nombre_mouvements': t['nombre_mouvements'],
                }
                for t in top
            ]
        except Exception as e:
            logger.warning(f"[dashboard] top_articles: {e}")
            return []

    @staticmethod
    def _consommation_carburant():
        try:
            from vehicules.models import Tricycle, PleinCarburant

            data = []
            for tricycle in Tricycle.objects.filter(is_deleted=False)[:20]:
                pleins = PleinCarburant.objects.filter(
                    tricycle=tricycle
                ).order_by('km_compteur')
                if pleins.count() >= 2:
                    total_litres = sum(float(p.litres or 0) for p in pleins)
                    km_debut = float(pleins.first().km_compteur or 0)
                    km_fin = float(pleins.last().km_compteur or 0)
                    distance = km_fin - km_debut
                    conso = (
                        round(total_litres / distance * 100, 2)
                        if distance > 0 else None
                    )
                    data.append({
                        'tricycle': tricycle.numero_interne,
                        'consommation_l_100km': conso,
                        'total_litres': round(total_litres, 2),
                        'distance_km': round(distance, 2),
                    })
            return data
        except Exception as e:
            logger.warning(f"[dashboard] consommation_carburant: {e}")
            return []

    @staticmethod
    def _performances_missions():
        try:
            from exploitation.models import Mission

            qs = Mission.objects.all()
            total = qs.count()
            if total == 0:
                return {}

            terminees = qs.filter(statut='terminee').count()
            annulees = qs.filter(statut='annulee').count()
            incidents = qs.filter(statut='incident').count()

            tonnage_total = _formater_montant(
                qs.aggregate(t=Sum('tonnage_reel'))['t']
            )

            return {
                'total': total,
                'terminees': terminees,
                'annulees': annulees,
                'incidents': incidents,
                'taux_reussite': round(terminees / total * 100, 2) if total else 0,
                'tonnage_total': tonnage_total,
            }
        except Exception as e:
            logger.warning(f"[dashboard] performances_missions: {e}")
            return {}
