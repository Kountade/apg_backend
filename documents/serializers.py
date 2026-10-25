# documents/serializers.py
import hashlib
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    CategorieDocument,
    Document,
    DocumentVersion,
    AccesDocument,
    TelechargementDocument,
    PartageDocument,
)


# ============================================================
# CONSTANTES
# ============================================================

TAILLE_MAX_FICHIER = 20 * 1024 * 1024  # 20 Mo

TYPES_MIME_AUTORISES = [
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    # Archives
    'application/zip',
    'application/x-zip-compressed',
]


# ============================================================
# CATÉGORIE DE DOCUMENT
# ============================================================

class CategorieDocumentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    parent_nom = serializers.SerializerMethodField(read_only=True)
    nombre_documents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CategorieDocument
        fields = [
            'id', 'code', 'nom',
            'type', 'type_display',
            'description',
            'parent', 'parent_nom',
            'ordre', 'actif',
            'nombre_documents',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'nombre_documents']

    def get_parent_nom(self, obj):
        return obj.parent.nom if obj.parent else None

    def get_nombre_documents(self, obj):
        return obj.documents.filter(is_deleted=False).count()


class CategorieDocumentListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    nombre_documents = serializers.SerializerMethodField()

    class Meta:
        model = CategorieDocument
        fields = [
            'id', 'code', 'nom',
            'type', 'type_display',
            'parent', 'ordre', 'actif',
            'nombre_documents',
        ]

    def get_nombre_documents(self, obj):
        return obj.documents.filter(is_deleted=False).count()


# ============================================================
# DOCUMENT — LECTURE
# ============================================================

class DocumentSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    categorie_type = serializers.SerializerMethodField(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    confidentialite_display = serializers.CharField(source='get_confidentialite_display', read_only=True)
    uploade_par_nom = serializers.SerializerMethodField(read_only=True)

    # Propriétés calculées
    est_expire = serializers.ReadOnlyField()
    jours_avant_expiration = serializers.ReadOnlyField()
    taille_formatee = serializers.ReadOnlyField()

    # URL absolue du fichier
    fichier_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'numero',
            'categorie', 'categorie_nom', 'categorie_type',
            'titre', 'description',
            'fichier', 'fichier_url',
            'nom_fichier_original', 'taille_octets', 'taille_formatee',
            'type_mime', 'hash_sha256',
            'statut', 'statut_display',
            'confidentialite', 'confidentialite_display',
            'date_document', 'date_expiration',
            'uploade_par', 'uploade_par_nom',
            'mots_cles',
            'version', 'est_version_active',
            'objet_lie_type', 'objet_lie_id',
            'notes',
            'est_expire', 'jours_avant_expiration',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'numero',
            'nom_fichier_original', 'taille_octets', 'taille_formatee',
            'type_mime', 'hash_sha256',
            'uploade_par',
            'est_expire', 'jours_avant_expiration',
            'created_at', 'updated_at', 'is_deleted',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None

    def get_categorie_type(self, obj):
        return obj.categorie.get_type_display() if obj.categorie else None

    def get_uploade_par_nom(self, obj):
        if not obj.uploade_par:
            return None
        return obj.uploade_par.get_full_name() or obj.uploade_par.email

    def get_fichier_url(self, obj):
        if not obj.fichier:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.fichier.url)
        return obj.fichier.url


# ============================================================
# DOCUMENT — LISTE
# ============================================================

class DocumentListSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    confidentialite_display = serializers.CharField(source='get_confidentialite_display', read_only=True)
    est_expire = serializers.ReadOnlyField()
    taille_formatee = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = [
            'id', 'numero', 'titre',
            'categorie', 'categorie_nom',
            'fichier',
            'taille_formatee',
            'statut', 'statut_display',
            'confidentialite', 'confidentialite_display',
            'date_document', 'date_expiration',
            'est_expire',
            'version',
            'created_at',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None


# ============================================================
# DOCUMENT — ÉCRITURE (upload fichier)
# ============================================================

class DocumentWriteSerializer(serializers.ModelSerializer):
    """
    Serializer d'écriture pour upload de fichier.
    
    Calcule automatiquement :
    - la taille (octets)
    - le hash SHA-256
    - le nom original
    - le type MIME
    """
    class Meta:
        model = Document
        fields = [
            'id', 'numero',
            'categorie',
            'titre', 'description',
            'fichier',
            'statut',
            'confidentialite',
            'date_document', 'date_expiration',
            'mots_cles',
            'version',
            'objet_lie_type', 'objet_lie_id',
            'notes',
        ]
        read_only_fields = ['id', 'numero']

    def validate_fichier(self, value):
        """Valide la taille et le type MIME du fichier."""
        if not value:
            return value

        # Taille
        if value.size > TAILLE_MAX_FICHIER:
            taille_mo = TAILLE_MAX_FICHIER // (1024 * 1024)
            raise serializers.ValidationError(
                f"Le fichier dépasse la taille maximale autorisée de {taille_mo} Mo."
            )

        # Type MIME (si fourni par le navigateur)
        content_type = getattr(value, 'content_type', None)
        if content_type and content_type not in TYPES_MIME_AUTORISES:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé ({content_type}). "
                f"Types acceptés : PDF, Word, Excel, PowerPoint, images, ZIP."
            )

        return value

    def _compute_hash(self, fichier):
        """Calcule le hash SHA-256 du fichier."""
        sha256 = hashlib.sha256()
        fichier.seek(0)
        for chunk in iter(lambda: fichier.read(8192), b''):
            sha256.update(chunk)
        fichier.seek(0)
        return sha256.hexdigest()

    def _prepare_payload(self, validated_data):
        """Prépare les métadonnées du fichier."""
        fichier = validated_data.get('fichier')
        if not fichier:
            return validated_data

        # Taille
        validated_data['taille_octets'] = fichier.size

        # Nom original
        if not validated_data.get('nom_fichier_original'):
            validated_data['nom_fichier_original'] = fichier.name.split('/')[-1]

        # Type MIME
        content_type = getattr(fichier, 'content_type', None)
        if content_type:
            validated_data['type_mime'] = content_type

        # Hash SHA-256
        try:
            validated_data['hash_sha256'] = self._compute_hash(fichier)
        except Exception:
            validated_data['hash_sha256'] = ''

        return validated_data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploade_par'] = request.user
        validated_data = self._prepare_payload(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si un nouveau fichier est fourni, on le remplace
        if 'fichier' in validated_data and validated_data['fichier']:
            validated_data = self._prepare_payload(validated_data)
        return super().update(instance, validated_data)


# ============================================================
# VERSION DE DOCUMENT
# ============================================================

class DocumentVersionSerializer(serializers.ModelSerializer):
    uploade_par_nom = serializers.SerializerMethodField(read_only=True)
    fichier_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DocumentVersion
        fields = [
            'id',
            'document',
            'version',
            'fichier', 'fichier_url',
            'commentaire',
            'uploade_par', 'uploade_par_nom',
            'created_at',
        ]
        read_only_fields = ['id', 'uploade_par', 'created_at']

    def get_uploade_par_nom(self, obj):
        if not obj.uploade_par:
            return None
        return obj.uploade_par.get_full_name() or obj.uploade_par.email

    def get_fichier_url(self, obj):
        if not obj.fichier:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.fichier.url)
        return obj.fichier.url

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploade_par'] = request.user
        return super().create(validated_data)


class DocumentVersionListSerializer(serializers.ModelSerializer):
    uploade_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'version',
            'commentaire',
            'uploade_par_nom',
            'created_at',
        ]

    def get_uploade_par_nom(self, obj):
        if not obj.uploade_par:
            return None
        return obj.uploade_par.get_full_name() or obj.uploade_par.email


# ============================================================
# ACCÈS DOCUMENT
# ============================================================

class AccesDocumentSerializer(serializers.ModelSerializer):
    document_numero = serializers.SerializerMethodField(read_only=True)
    utilisateur_nom = serializers.SerializerMethodField(read_only=True)
    niveau_display = serializers.CharField(source='get_niveau_display', read_only=True)
    est_actif = serializers.ReadOnlyField()

    class Meta:
        model = AccesDocument
        fields = [
            'id',
            'document', 'document_numero',
            'utilisateur', 'utilisateur_nom',
            'niveau', 'niveau_display',
            'date_expiration',
            'est_actif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'est_actif']

    def get_document_numero(self, obj):
        return obj.document.numero if obj.document else None

    def get_utilisateur_nom(self, obj):
        if not obj.utilisateur:
            return None
        return obj.utilisateur.get_full_name() or obj.utilisateur.email

    def validate(self, data):
        # Vérifie qu'on ne crée pas un doublon
        document = data.get('document') or (self.instance.document if self.instance else None)
        utilisateur = data.get('utilisateur') or (self.instance.utilisateur if self.instance else None)

        if document and utilisateur:
            qs = AccesDocument.objects.filter(
                document=document, utilisateur=utilisateur
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Cet utilisateur a déjà un accès à ce document."
                )
        return data


# ============================================================
# TÉLÉCHARGEMENT DOCUMENT (lecture seule)
# ============================================================

class TelechargementDocumentSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.SerializerMethodField(read_only=True)
    document_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TelechargementDocument
        fields = [
            'id',
            'document', 'document_numero',
            'utilisateur', 'utilisateur_nom',
            'date_telechargement',
            'adresse_ip',
            'user_agent',
        ]
        read_only_fields = '__all__'

    def get_utilisateur_nom(self, obj):
        if not obj.utilisateur:
            return None
        return obj.utilisateur.get_full_name() or obj.utilisateur.email

    def get_document_numero(self, obj):
        return obj.document.numero if obj.document else None


# ============================================================
# PARTAGE DOCUMENT
# ============================================================

class PartageDocumentSerializer(serializers.ModelSerializer):
    document_numero = serializers.SerializerMethodField(read_only=True)
    cree_par_nom = serializers.SerializerMethodField(read_only=True)
    est_valide = serializers.ReadOnlyField()
    lien_partage = serializers.ReadOnlyField()
    # Ne JAMAIS exposer le mot de passe (même hashé)
    a_mot_de_passe = serializers.SerializerMethodField(read_only=True)
    mot_de_passe = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = PartageDocument
        fields = [
            'id',
            'document', 'document_numero',
            'token',
            'lien_partage',
            'cree_par', 'cree_par_nom',
            'date_expiration',
            'mot_de_passe', 'a_mot_de_passe',
            'nombre_max_telechargements',
            'nombre_telechargements',
            'actif',
            'est_valide',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'token',
            'nombre_telechargements',
            'cree_par',
            'created_at', 'updated_at',
            'est_valide', 'lien_partage', 'a_mot_de_passe',
        ]

    def get_document_numero(self, obj):
        return obj.document.numero if obj.document else None

    def get_cree_par_nom(self, obj):
        if not obj.cree_par:
            return None
        return obj.cree_par.get_full_name() or obj.cree_par.email

    def get_a_mot_de_passe(self, obj):
        return bool(obj.mot_de_passe)

    def validate_date_expiration(self, value):
        from django.utils import timezone
        if value and value < timezone.now():
            raise serializers.ValidationError(
                "La date d'expiration doit être dans le futur."
            )
        return value

    def validate_nombre_max_telechargements(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Le nombre maximum de téléchargements ne peut pas être négatif."
            )
        return value

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['cree_par'] = request.user

        # Hash du mot de passe s'il est fourni
        mot_de_passe = validated_data.pop('mot_de_passe', '')
        if mot_de_passe:
            validated_data['mot_de_passe'] = make_password(mot_de_passe)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from django.contrib.auth.hashers import make_password

        mot_de_passe = validated_data.pop('mot_de_passe', None)
        if mot_de_passe:
            validated_data['mot_de_passe'] = make_password(mot_de_passe)

        return super().update(instance, validated_data)


class PartageDocumentPublicSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'accès PUBLIC (via token).
    Ne retourne QUE les infos minimales nécessaires.
    """
    document_titre = serializers.SerializerMethodField(read_only=True)
    document_fichier_url = serializers.SerializerMethodField(read_only=True)
    document_taille = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PartageDocument
        fields = [
            'token',
            'document_titre',
            'document_fichier_url',
            'document_taille',
            'date_expiration',
            'nombre_max_telechargements',
            'nombre_telechargements',
            'a_mot_de_passe',
        ]

    def get_document_titre(self, obj):
        return obj.document.titre if obj.document else None

    def get_document_fichier_url(self, obj):
        if not obj.document or not obj.document.fichier:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.document.fichier.url)
        return obj.document.fichier.url

    def get_document_taille(self, obj):
        if not obj.document:
            return 0
        return obj.document.taille_formatee