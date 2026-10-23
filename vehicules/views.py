from django.shortcuts import render

# Create your views here.
# vehicules/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import date, timedelta

from core.permissions import CanViewPersonnel, CanEditPersonnel
from core.pagination import StandardPagination

from .models import (
    Tricycle, Vehicule, Conducteur,
    AffectationVehicule, DocumentVehicule, Assurance,
    SuiviGPS, PleinCarburant,
)
from .serializers import (
    TricycleSerializer, TricycleListSerializer,
    VehiculeSerializer, VehiculeListSerializer,
    ConducteurSerializer, ConducteurListSerializer,
    AffectationVehiculeSerializer, AffectationVehiculeListSerializer,
    DocumentVehiculeSerializer,
    AssuranceSerializer, AssuranceListSerializer,
    SuiviGPSSerializer,
    PleinCarburantSerializer, PleinCarburantListSerializer,
)


# ============================================================
# TRICYCLE
# ============================================================

class TricycleViewset(viewsets.ModelViewSet):
    """CRUD Tricycles."""
    queryset = Tricycle.objects.filter(is_deleted=False).select_related(
        'conducteur_affecte', 'equipement', 'equipement__categorie'
    )
    pagination_class = StandardPagination
    search_fields = ['numero_interne', 'immatriculation', 'marque', 'modele', 'zone_exploitation']
    filterset_fields = ['etat', 'statut', 'conducteur_affecte']
    ordering_fields = ['numero_interne', 'marque', 'kilometrage_actuel']

    def get_serializer_class(self):
        if self.action == 'list':
            return TricycleListSerializer
        return TricycleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        return Response({'numero_interne': Tricycle.proposer_numero_interne()})

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Tricycles disponibles (pas en mission, pas en maintenance)."""
        qs = Tricycle.objects.filter(
            etat='disponible', statut='actif', is_deleted=False
        ).select_related('conducteur_affecte')
        serializer = TricycleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Tricycle.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'par_etat': list(qs.values('etat').annotate(total=Count('id')).order_by('-total')),
            'par_statut': list(qs.values('statut').annotate(total=Count('id')).order_by('-total')),
            'kilometrage_total': qs.aggregate(t=Sum('kilometrage_actuel'))['t'] or 0,
            'valeur_totale': qs.aggregate(t=Sum('cout_acquisition'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# VÉHICULE
# ============================================================

class VehiculeViewset(viewsets.ModelViewSet):
    """CRUD Véhicules."""
    queryset = Vehicule.objects.filter(is_deleted=False).select_related(
        'conducteur_affecte', 'equipement', 'equipement__categorie'
    )
    pagination_class = StandardPagination
    search_fields = ['numero_interne', 'immatriculation', 'marque', 'modele', 'zone_exploitation']
    filterset_fields = ['type', 'etat', 'statut', 'conducteur_affecte']
    ordering_fields = ['numero_interne', 'marque', 'kilometrage_actuel']

    def get_serializer_class(self):
        if self.action == 'list':
            return VehiculeListSerializer
        return VehiculeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def prochain_numero(self, request):
        return Response({'numero_interne': Vehicule.proposer_numero_interne()})

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        qs = Vehicule.objects.filter(
            etat='disponible', statut='actif', is_deleted=False
        ).select_related('conducteur_affecte')
        serializer = VehiculeListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Vehicule.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'par_type': list(qs.values('type').annotate(total=Count('id')).order_by('-total')),
            'par_etat': list(qs.values('etat').annotate(total=Count('id')).order_by('-total')),
            'kilometrage_total': qs.aggregate(t=Sum('kilometrage_actuel'))['t'] or 0,
            'valeur_totale': qs.aggregate(t=Sum('cout_acquisition'))['t'] or 0,
        }
        return Response(data)


# ============================================================
# CONDUCTEUR
# ============================================================

class ConducteurViewset(viewsets.ModelViewSet):
    """CRUD Conducteurs."""
    queryset = Conducteur.objects.select_related('employe').all()
    pagination_class = StandardPagination
    search_fields = ['employe__nom', 'employe__prenom', 'numero_permis', 'categorie_permis']
    filterset_fields = ['actif', 'categorie_permis']
    ordering_fields = ['employe__nom', 'annees_experience']

    def get_serializer_class(self):
        if self.action == 'list':
            return ConducteurListSerializer
        return ConducteurSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def actifs(self, request):
        qs = Conducteur.objects.filter(actif=True).select_related('employe')
        serializer = ConducteurListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def permis_expires(self, request):
        today = date.today()
        qs = Conducteur.objects.filter(
            date_expiration_permis__lt=today,
            actif=True,
        ).select_related('employe')
        serializer = ConducteurListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Conducteur.objects.all()
        data = {
            'total': qs.count(),
            'actifs': qs.filter(actif=True).count(),
            'permis_expires': qs.filter(date_expiration_permis__lt=date.today()).count(),
            'experience_moyenne': qs.aggregate(m=Avg('annees_experience'))['m'] or 0,
        }
        return Response(data)


# ============================================================
# AFFECTATION VÉHICULE
# ============================================================

class AffectationVehiculeViewset(viewsets.ModelViewSet):
    """CRUD Affectations véhicules."""
    queryset = AffectationVehicule.objects.select_related(
        'tricycle', 'vehicule', 'conducteur', 'conducteur__employe'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['conducteur__employe__nom', 'zone']
    filterset_fields = ['conducteur', 'tricycle', 'vehicule']
    ordering_fields = ['date_debut', 'date_fin']

    def get_serializer_class(self):
        if self.action == 'list':
            return AffectationVehiculeListSerializer
        return AffectationVehiculeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        qs = AffectationVehicule.objects.filter(
            date_fin__isnull=True
        ).select_related('tricycle', 'vehicule', 'conducteur__employe')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """Termine une affectation (date_fin = aujourd'hui)."""
        affectation = self.get_object()
        if affectation.date_fin:
            return Response(
                {"error": "Cette affectation est déjà terminée."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        affectation.date_fin = request.data.get('date_fin', date.today())
        affectation.observation = request.data.get('observation', affectation.observation)
        affectation.save()
        return Response(self.get_serializer(affectation).data)


# ============================================================
# DOCUMENT VÉHICULE
# ============================================================

class DocumentVehiculeViewset(viewsets.ModelViewSet):
    """CRUD Documents véhicules."""
    queryset = DocumentVehicule.objects.select_related(
        'tricycle', 'vehicule'
    ).all()
    serializer_class = DocumentVehiculeSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'organisme', 'notes']
    filterset_fields = ['type', 'tricycle', 'vehicule']
    ordering_fields = ['date_expiration', 'date_emission']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def qui_expirent(self, request):
        """Documents qui expirent dans les 30 jours (ou déjà expirés)."""
        jours = int(request.query_params.get('jours', 30))
        seuil = date.today() + timedelta(days=jours)
        qs = DocumentVehicule.objects.filter(
            date_expiration__lte=seuil,
        ).select_related('tricycle', 'vehicule').order_by('date_expiration')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expires(self, request):
        """Documents déjà expirés."""
        qs = DocumentVehicule.objects.filter(
            date_expiration__lt=date.today(),
        ).select_related('tricycle', 'vehicule').order_by('date_expiration')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# ASSURANCE
# ============================================================

class AssuranceViewset(viewsets.ModelViewSet):
    """CRUD Assurances."""
    queryset = Assurance.objects.select_related(
        'tricycle', 'vehicule'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['compagnie', 'numero_police', 'type_couverture']
    filterset_fields = ['compagnie', 'tricycle', 'vehicule']
    ordering_fields = ['date_fin', 'date_debut', 'prime_annuelle']

    def get_serializer_class(self):
        if self.action == 'list':
            return AssuranceListSerializer
        return AssuranceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def qui_expirent(self, request):
        """Assurances qui expirent dans les 30 jours."""
        jours = int(request.query_params.get('jours', 30))
        seuil = date.today() + timedelta(days=jours)
        qs = Assurance.objects.filter(
            date_fin__lte=seuil,
        ).select_related('tricycle', 'vehicule').order_by('date_fin')
        serializer = AssuranceListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expirees(self, request):
        """Assurances déjà expirées."""
        qs = Assurance.objects.filter(
            date_fin__lt=date.today(),
        ).select_related('tricycle', 'vehicule').order_by('date_fin')
        serializer = AssuranceListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = Assurance.objects.all()
        data = {
            'total': qs.count(),
            'prime_totale': qs.aggregate(t=Sum('prime_annuelle'))['t'] or 0,
            'expirees': qs.filter(date_fin__lt=date.today()).count(),
            'par_compagnie': list(
                qs.values('compagnie').annotate(
                    total=Count('id'),
                    prime=Sum('prime_annuelle'),
                ).order_by('-total')
            ),
        }
        return Response(data)


# ============================================================
# SUIVI GPS
# ============================================================

class SuiviGPSViewset(viewsets.ModelViewSet):
    """CRUD Suivi GPS."""
    queryset = SuiviGPS.objects.select_related(
        'tricycle', 'vehicule'
    ).all()
    serializer_class = SuiviGPSSerializer
    pagination_class = StandardPagination
    filterset_fields = ['tricycle', 'vehicule']
    ordering_fields = ['date_position']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def derniere_position(self, request):
        """Dernière position connue par engin."""
        # On récupère la dernière position de chaque tricycle/vehicule
        positions = []
        for tricycle in Tricycle.objects.filter(is_deleted=False):
            last = SuiviGPS.objects.filter(tricycle=tricycle).order_by('-date_position').first()
            if last:
                positions.append(self.get_serializer(last).data)
        for vehicule in Vehicule.objects.filter(is_deleted=False):
            last = SuiviGPS.objects.filter(vehicule=vehicule).order_by('-date_position').first()
            if last:
                positions.append(self.get_serializer(last).data)
        return Response(positions)


# ============================================================
# PLEIN CARBURANT
# ============================================================

class PleinCarburantViewset(viewsets.ModelViewSet):
    """CRUD Pleins de carburant."""
    queryset = PleinCarburant.objects.select_related(
        'tricycle', 'vehicule', 'conducteur'
    ).all()
    pagination_class = StandardPagination
    search_fields = ['station', 'notes']
    filterset_fields = ['type_carburant', 'tricycle', 'vehicule', 'conducteur']
    ordering_fields = ['date', 'montant', 'litres']

    def get_serializer_class(self):
        if self.action == 'list':
            return PleinCarburantListSerializer
        return PleinCarburantSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        qs = PleinCarburant.objects.all()

        # Statistiques globales
        data = {
            'total': qs.count(),
            'litres_total': qs.aggregate(t=Sum('litres'))['t'] or 0,
            'montant_total': qs.aggregate(t=Sum('montant'))['t'] or 0,
            'par_type': list(
                qs.values('type_carburant').annotate(
                    total=Count('id'),
                    litres=Sum('litres'),
                    montant=Sum('montant'),
                )
            ),
        }

        # Consommation moyenne par engin
        consommations = []
        for tricycle in Tricycle.objects.filter(is_deleted=False):
            pleins = PleinCarburant.objects.filter(tricycle=tricycle).order_by('km_compteur')
            if pleins.count() >= 2:
                total_litres = sum(float(p.litres) for p in pleins)
                km_debut = float(pleins.first().km_compteur)
                km_fin = float(pleins.last().km_compteur)
                if km_fin > km_debut:
                    conso = round(total_litres / (km_fin - km_debut) * 100, 2)
                    consommations.append({
                        'engin': f"Tricycle {tricycle.numero_interne}",
                        'consommation_l_100km': conso,
                        'total_litres': total_litres,
                        'distance_km': km_fin - km_debut,
                    })

        data['consommations'] = consommations
        return Response(data)

    @action(detail=False, methods=['get'])
    def par_vehicule(self, request):
        """Pleins d'un engin spécifique (?tricycle=X ou ?vehicule=Y)."""
        tricycle_id = request.query_params.get('tricycle')
        vehicule_id = request.query_params.get('vehicule')

        qs = PleinCarburant.objects.all()
        if tricycle_id:
            qs = qs.filter(tricycle_id=tricycle_id)
        elif vehicule_id:
            qs = qs.filter(vehicule_id=vehicule_id)
        else:
            return Response(
                {"error": "Paramètre 'tricycle' ou 'vehicule' requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = qs.order_by('-date')
        serializer = PleinCarburantListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def alertes(self, request):
        """Pleins où la consommation dépasse un seuil (défaut 20 L/100km)."""
        seuil = float(request.query_params.get('seuil', 20))
        alertes = []

        for plein in PleinCarburant.objects.select_related('tricycle', 'vehicule').all():
            conso = plein.consommation
            if conso is not None and conso > seuil:
                alertes.append({
                    'plein_id': plein.id,
                    'engin': (
                        f"Tricycle {plein.tricycle.numero_interne}" if plein.tricycle
                        else f"Véhicule {plein.vehicule.numero_interne}"
                    ),
                    'date': plein.date,
                    'consommation': conso,
                    'seuil': seuil,
                })

        return Response(alertes)