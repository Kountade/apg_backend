from django.shortcuts import render

# Create your views here.
# rh/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q

from core.permissions import (
    IsStaff, IsRH, IsPDG,
    CanViewPersonnel, CanEditPersonnel,
    CanValidateConges,
)
from core.pagination import StandardPagination

from .models import (
    Departement, Poste, Employe, Contrat,
    Presence, JoursTravailles, Conge, SoldeConge,
    Absence, Evaluation, Formation,
)
from .serializers import (
    DepartementSerializer,
    PosteSerializer,
    EmployeSerializer, EmployeListSerializer, EmployeWriteSerializer,
    ContratSerializer,
    PresenceSerializer,
    JoursTravaillesSerializer,
    CongeSerializer, CongeValidationSerializer,
    SoldeCongeSerializer,
    AbsenceSerializer,
    EvaluationSerializer,
    FormationSerializer,
)


# ============================================================
# DÉPARTEMENTS
# ============================================================

class DepartementViewset(viewsets.ModelViewSet):
    """CRUD Départements."""
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer
    permission_classes = [CanViewPersonnel]
    pagination_class = StandardPagination
    search_fields = ['nom', 'code']
    ordering_fields = ['nom', 'created_at']

    def get_permissions(self):
        # Écriture réservée RH/PDG
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# POSTES
# ============================================================

class PosteViewset(viewsets.ModelViewSet):
    """CRUD Postes."""
    queryset = Poste.objects.select_related('departement').all()
    serializer_class = PosteSerializer
    pagination_class = StandardPagination
    search_fields = ['nom', 'departement__nom']
    filterset_fields = ['departement']
    ordering_fields = ['nom', 'salaire_min', 'salaire_max']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# EMPLOYÉS
# ============================================================

class EmployeViewset(viewsets.ModelViewSet):
    """CRUD Employés."""
    queryset = Employe.objects.filter(is_deleted=False).select_related(
        'poste', 'departement', 'superieur', 'user'
    )
    pagination_class = StandardPagination
    search_fields = ['matricule', 'nom', 'prenom', 'telephone', 'email']
    filterset_fields = ['statut', 'type_contrat', 'departement', 'poste']
    ordering_fields = ['nom', 'prenom', 'date_embauche', 'salaire_base']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmployeWriteSerializer
        if self.action == 'list':
            return EmployeListSerializer
        return EmployeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete : ne supprime pas physiquement."""
        instance = self.get_object()
        instance.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def contrats(self, request, pk=None):
        """Liste les contrats d'un employé."""
        employe = self.get_object()
        contrats = employe.contrats.all()
        serializer = ContratSerializer(contrats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def presences(self, request, pk=None):
        """Liste les présences d'un employé."""
        employe = self.get_object()
        presences = employe.presences.all()[:50]
        serializer = PresenceSerializer(presences, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def conges(self, request, pk=None):
        """Liste les congés d'un employé."""
        employe = self.get_object()
        conges = employe.conges.all()
        serializer = CongeSerializer(conges, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques globales du personnel."""
        qs = Employe.objects.filter(is_deleted=False)
        data = {
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'suspendus': qs.filter(statut='suspendu').count(),
            'partis': qs.filter(statut='parti').count(),
            'par_departement': list(
                qs.values('departement__nom').annotate(
                    total=Count('id')).order_by('-total')
            ),
            'par_type_contrat': list(
                qs.values('type_contrat').annotate(
                    total=Count('id')).order_by('-total')
            ),
        }
        return Response(data)


# ============================================================
# CONTRATS
# ============================================================

class ContratViewset(viewsets.ModelViewSet):
    """CRUD Contrats."""
    queryset = Contrat.objects.select_related('employe').all()
    serializer_class = ContratSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'employe__nom', 'employe__prenom']
    filterset_fields = ['statut', 'type', 'employe']
    ordering_fields = ['date_debut', 'date_fin', 'salaire']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def expirant(self, request):
        """Contrats qui expirent dans les 30 prochains jours."""
        from datetime import date, timedelta
        seuil = date.today() + timedelta(days=30)
        qs = Contrat.objects.filter(
            statut='actif',
            date_fin__lte=seuil,
            date_fin__gte=date.today()
        ).select_related('employe')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# PRÉSENCES
# ============================================================

class PresenceViewset(viewsets.ModelViewSet):
    """CRUD Présences."""
    queryset = Presence.objects.select_related('employe').all()
    serializer_class = PresenceSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'statut', 'date']
    ordering_fields = ['date', 'employe__nom']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def aujourdhui(self, request):
        """Présences du jour."""
        qs = Presence.objects.filter(date=timezone.now().date())
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_employe(self, request):
        """Présences d'un employé donné (?employe_id=X&mois=Y&annee=Z)."""
        employe_id = request.query_params.get('employe_id')
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')

        qs = Presence.objects.all()
        if employe_id:
            qs = qs.filter(employe_id=employe_id)
        if mois:
            qs = qs.filter(date__month=mois)
        if annee:
            qs = qs.filter(date__year=annee)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# JOURS TRAVAILLÉS
# ============================================================

class JoursTravaillesViewset(viewsets.ModelViewSet):
    """CRUD Jours travaillés."""
    queryset = JoursTravailles.objects.select_related('employe').all()
    serializer_class = JoursTravaillesSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'mois', 'annee']
    ordering_fields = ['annee', 'mois']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# CONGÉS
# ============================================================

class CongeViewset(viewsets.ModelViewSet):
    """CRUD Congés + validation."""
    queryset = Conge.objects.select_related('employe', 'valide_par').all()
    serializer_class = CongeSerializer
    pagination_class = StandardPagination
    search_fields = ['numero', 'employe__nom', 'employe__prenom']
    filterset_fields = ['statut', 'type', 'employe']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']

    def get_permissions(self):
        # Validation réservée RH/PDG
        if self.action in ['valider', 'refuser']:
            return [CanValidateConges()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un congé."""
        conge = self.get_object()
        if conge.statut != 'en_attente':
            return Response(
                {"error": "Ce congé a déjà été traité."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conge.statut = 'valide'
        conge.valide_par = request.user
        conge.date_validation = timezone.now()
        conge.commentaire = request.data.get('commentaire', '')
        conge.save()

        # Mise à jour du solde de congés
        try:
            solde, _ = SoldeConge.objects.get_or_create(
                employe=conge.employe,
                annee=conge.date_debut.year,
            )
            solde.jours_pris += conge.nombre_jours
            solde.solde_restant = (
                solde.solde_initial + solde.jours_acquis - solde.jours_pris
            )
            solde.save()
        except Exception:
            pass

        return Response(CongeSerializer(conge).data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """Refuse un congé."""
        conge = self.get_object()
        if conge.statut != 'en_attente':
            return Response(
                {"error": "Ce congé a déjà été traité."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conge.statut = 'refuse'
        conge.valide_par = request.user
        conge.date_validation = timezone.now()
        conge.commentaire = request.data.get('commentaire', '')
        conge.save()
        return Response(CongeSerializer(conge).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """Congés en attente de validation."""
        qs = Conge.objects.filter(statut='en_attente').select_related('employe')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mes_conges(self, request):
        """Congés de l'utilisateur connecté (via son profil employé)."""
        try:
            employe = request.user.employe_profile
        except Exception:
            return Response(
                {"error": "Aucun profil employé lié à ce compte."},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = Conge.objects.filter(employe=employe)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ============================================================
# SOLDES DE CONGÉS
# ============================================================

class SoldeCongeViewset(viewsets.ModelViewSet):
    """CRUD Soldes de congés."""
    queryset = SoldeConge.objects.select_related('employe').all()
    serializer_class = SoldeCongeSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'annee']
    ordering_fields = ['annee']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]


# ============================================================
# ABSENCES
# ============================================================

class AbsenceViewset(viewsets.ModelViewSet):
    """CRUD Absences."""
    queryset = Absence.objects.select_related('employe').all()
    serializer_class = AbsenceSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'type', 'statut']
    ordering_fields = ['date_debut', 'date_fin']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# ÉVALUATIONS
# ============================================================

class EvaluationViewset(viewsets.ModelViewSet):
    """CRUD Évaluations."""
    queryset = Evaluation.objects.select_related('employe', 'evaluateur').all()
    serializer_class = EvaluationSerializer
    pagination_class = StandardPagination
    filterset_fields = ['employe', 'evaluateur', 'periode']
    ordering_fields = ['date_evaluation', 'note_globale']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================
# FORMATIONS
# ============================================================

class FormationViewset(viewsets.ModelViewSet):
    """CRUD Formations."""
    queryset = Formation.objects.prefetch_related('participants').all()
    serializer_class = FormationSerializer
    pagination_class = StandardPagination
    search_fields = ['titre', 'formateur']
    ordering_fields = ['date_debut', 'date_fin', 'cout']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [CanEditPersonnel()]
        return [CanViewPersonnel()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)