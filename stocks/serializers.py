# stocks/serializers.py
from rest_framework import serializers
from .models import (
    CategorieMateriel, Magasin, Article, StockMagasin,
    Equipement, AffectationEquipement, MouvementStock,
    MaintenanceEquipement, Inventaire, LigneInventaire,
)


# ============================================================
# CATÉGORIE MATÉRIEL
# ============================================================

class CategorieMaterielSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    nombre_articles = serializers.SerializerMethodField(read_only=True)
    nombre_equipements = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CategorieMateriel
        fields = [
            'id', 'nom', 'code', 'type', 'type_display',
            'description', 'actif',
            'nombre_articles', 'nombre_equipements',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nombre_articles(self, obj):
        return obj.articles.filter(is_deleted=False).count()

    def get_nombre_equipements(self, obj):
        return obj.equipements.filter(is_deleted=False).count()


class CategorieMaterielListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = CategorieMateriel
        fields = ['id', 'nom', 'code', 'type', 'type_display', 'actif']


# ============================================================
# MAGASIN
# ============================================================

class MagasinSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    responsable_nom = serializers.SerializerMethodField(read_only=True)
    nombre_articles = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Magasin
        fields = [
            'id', 'code', 'nom', 'type', 'type_display',
            'adresse', 'zone',
            'responsable', 'responsable_nom',
            'telephone', 'actif', 'notes',
            'nombre_articles',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_responsable_nom(self, obj):
        return obj.responsable.nom_complet if obj.responsable else None

    def get_nombre_articles(self, obj):
        return obj.stocks.count()


class MagasinListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Magasin
        fields = ['id', 'code', 'nom', 'type', 'type_display', 'zone', 'actif']


# ============================================================
# STOCK PAR MAGASIN
# ============================================================

class StockMagasinSerializer(serializers.ModelSerializer):
    article_code = serializers.SerializerMethodField(read_only=True)
    article_designation = serializers.SerializerMethodField(read_only=True)
    magasin_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StockMagasin
        fields = [
            'id', 'article', 'article_code', 'article_designation',
            'magasin', 'magasin_nom',
            'quantite', 'emplacement',
        ]
        read_only_fields = ['id']

    def get_article_code(self, obj):
        return obj.article.code if obj.article else None

    def get_article_designation(self, obj):
        return obj.article.designation if obj.article else None

    def get_magasin_nom(self, obj):
        return obj.magasin.nom if obj.magasin else None


# ============================================================
# ARTICLE (consommable)
# ============================================================

class ArticleSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    categorie_type = serializers.SerializerMethodField(read_only=True)
    unite_display = serializers.CharField(source='get_unite_display', read_only=True)
    stock_total = serializers.ReadOnlyField()
    est_en_alerte = serializers.ReadOnlyField()
    est_critique = serializers.ReadOnlyField()
    stocks_magasins = StockMagasinSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'designation',
            'categorie', 'categorie_nom', 'categorie_type',
            'description', 'unite', 'unite_display',
            'stock_minimum', 'seuil_alerte', 'prix_achat',
            'fournisseur_nom',
            'photo', 'actif',
            'stock_total', 'est_en_alerte', 'est_critique',
            'stocks_magasins',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'updated_at', 'is_deleted',
            'stock_total', 'est_en_alerte', 'est_critique',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None

    def get_categorie_type(self, obj):
        return obj.categorie.get_type_display() if obj.categorie else None


class ArticleListSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField()
    stock_total = serializers.ReadOnlyField()
    est_critique = serializers.ReadOnlyField()
    est_en_alerte = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'designation',
            'categorie_nom',
            'unite', 'prix_achat',
            'stock_total', 'stock_minimum', 'seuil_alerte',
            'est_critique', 'est_en_alerte', 'actif',
            'photo',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None


class ArticleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'id', 'code', 'designation',
            'categorie', 'description',
            'unite', 'stock_minimum', 'seuil_alerte',
            'prix_achat', 'fournisseur_nom',
            'photo', 'actif',
        ]

    def validate_code(self, value):
        if not value:
            return value
        qs = Article.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ce code article est déjà utilisé.")
        return value


# ============================================================
# ÉQUIPEMENT
# ============================================================

class EquipementSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    magasin_nom = serializers.SerializerMethodField(read_only=True)
    responsable_nom = serializers.SerializerMethodField(read_only=True)
    valeur_actuelle = serializers.ReadOnlyField()
    est_sous_garantie = serializers.ReadOnlyField()
    age_mois = serializers.ReadOnlyField()

    class Meta:
        model = Equipement
        fields = [
            'id', 'code', 'designation',
            'categorie', 'categorie_nom',
            'description',
            'numero_serie', 'marque', 'modele', 'annee_fabrication',
            'date_acquisition', 'cout_acquisition', 'fournisseur_nom',
            'duree_garantie_mois', 'date_fin_garantie',
            'duree_amortissement_mois', 'valeur_residuelle',
            'etat', 'etat_display',
            'localisation',
            'magasin', 'magasin_nom',
            'responsable', 'responsable_nom',
            'photo', 'fiche_technique',
            'actif', 'notes',
            'valeur_actuelle', 'est_sous_garantie', 'age_mois',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'updated_at', 'is_deleted',
            'valeur_actuelle', 'est_sous_garantie', 'age_mois',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None

    def get_magasin_nom(self, obj):
        return obj.magasin.nom if obj.magasin else None

    def get_responsable_nom(self, obj):
        return obj.responsable.nom_complet if obj.responsable else None


class EquipementListSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.SerializerMethodField()
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    valeur_actuelle = serializers.ReadOnlyField()

    class Meta:
        model = Equipement
        fields = [
            'id', 'code', 'designation',
            'categorie_nom',
            'numero_serie', 'marque', 'modele',
            'etat', 'etat_display',
            'localisation',
            'cout_acquisition', 'valeur_actuelle',
            'photo', 'actif',
        ]

    def get_categorie_nom(self, obj):
        return obj.categorie.nom if obj.categorie else None


# ============================================================
# AFFECTATION ÉQUIPEMENT
# ============================================================

class AffectationEquipementSerializer(serializers.ModelSerializer):
    equipement_code = serializers.SerializerMethodField(read_only=True)
    equipement_designation = serializers.SerializerMethodField(read_only=True)
    employe_nom = serializers.SerializerMethodField(read_only=True)
    est_en_cours = serializers.ReadOnlyField()

    class Meta:
        model = AffectationEquipement
        fields = [
            'id',
            'equipement', 'equipement_code', 'equipement_designation',
            'employe', 'employe_nom',
            'equipe_nom',
            'date_affectation', 'date_retour',
            'etat_avant', 'etat_apres',
            'bon_sortie', 'bon_retour',
            'observation',
            'est_en_cours',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'date_affectation', 'created_at', 'updated_at']

    def get_equipement_code(self, obj):
        return obj.equipement.code if obj.equipement else None

    def get_equipement_designation(self, obj):
        return obj.equipement.designation if obj.equipement else None

    def get_employe_nom(self, obj):
        return obj.employe.nom_complet if obj.employe else None


# ============================================================
# MOUVEMENT DE STOCK
# ============================================================

class MouvementStockSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    motif_display = serializers.CharField(source='get_motif_display', read_only=True)
    article_code = serializers.SerializerMethodField(read_only=True)
    article_designation = serializers.SerializerMethodField(read_only=True)
    magasin_source_nom = serializers.SerializerMethodField(read_only=True)
    magasin_destination_nom = serializers.SerializerMethodField(read_only=True)
    employe_beneficiaire_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MouvementStock
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'motif', 'motif_display',
            'date_mouvement',
            'article', 'article_code', 'article_designation',
            'quantite', 'prix_unitaire',
            'magasin_source', 'magasin_source_nom',
            'magasin_destination', 'magasin_destination_nom',
            'beneficiaire',
            'employe_beneficiaire', 'employe_beneficiaire_nom',
            'fournisseur_nom',
            'reference', 'observation', 'justificatif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'date_mouvement', 'created_at', 'updated_at']

    def get_article_code(self, obj):
        return obj.article.code if obj.article else None

    def get_article_designation(self, obj):
        return obj.article.designation if obj.article else None

    def get_magasin_source_nom(self, obj):
        return obj.magasin_source.nom if obj.magasin_source else None

    def get_magasin_destination_nom(self, obj):
        return obj.magasin_destination.nom if obj.magasin_destination else None

    def get_employe_beneficiaire_nom(self, obj):
        return obj.employe_beneficiaire.nom_complet if obj.employe_beneficiaire else None

    def validate(self, data):
        type_mvt = data.get('type')
        if type_mvt == 'entree' and not data.get('magasin_destination'):
            raise serializers.ValidationError(
                "Une entrée nécessite un magasin de destination."
            )
        if type_mvt == 'sortie' and not data.get('magasin_source'):
            raise serializers.ValidationError(
                "Une sortie nécessite un magasin source."
            )
        if type_mvt == 'transfert':
            if not data.get('magasin_source'):
                raise serializers.ValidationError(
                    "Un transfert nécessite un magasin source."
                )
            if not data.get('magasin_destination'):
                raise serializers.ValidationError(
                    "Un transfert nécessite un magasin de destination."
                )
        return data


class MouvementStockListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    article_code = serializers.SerializerMethodField()
    article_designation = serializers.SerializerMethodField()

    class Meta:
        model = MouvementStock
        fields = [
            'id', 'numero',
            'type', 'type_display',
            'date_mouvement',
            'article', 'article_code', 'article_designation',
            'quantite',
            'magasin_source_nom', 'magasin_destination_nom',
        ]

    def get_article_code(self, obj):
        return obj.article.code if obj.article else None

    def get_article_designation(self, obj):
        return obj.article.designation if obj.article else None

    magasin_source_nom = serializers.SerializerMethodField()

    def get_magasin_source_nom(self, obj):
        return obj.magasin_source.nom if obj.magasin_source else None

    magasin_destination_nom = serializers.SerializerMethodField()

    def get_magasin_destination_nom(self, obj):
        return obj.magasin_destination.nom if obj.magasin_destination else None


# ============================================================
# MAINTENANCE ÉQUIPEMENT
# ============================================================

class MaintenanceEquipementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    equipement_code = serializers.SerializerMethodField(read_only=True)
    equipement_designation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MaintenanceEquipement
        fields = [
            'id', 'numero',
            'equipement', 'equipement_code', 'equipement_designation',
            'type', 'type_display',
            'statut', 'statut_display',
            'date_debut', 'date_fin',
            'description', 'technicien',
            'cout_main_oeuvre', 'cout_pieces', 'cout_total',
            'observations', 'justificatif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'cout_total', 'created_at', 'updated_at']

    def get_equipement_code(self, obj):
        return obj.equipement.code if obj.equipement else None

    def get_equipement_designation(self, obj):
        return obj.equipement.designation if obj.equipement else None


# ============================================================
# INVENTAIRE
# ============================================================

class LigneInventaireSerializer(serializers.ModelSerializer):
    article_code = serializers.SerializerMethodField(read_only=True)
    article_designation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LigneInventaire
        fields = [
            'id', 'inventaire',
            'article', 'article_code', 'article_designation',
            'quantite_theorique', 'quantite_comptee', 'ecart',
            'observation',
        ]
        read_only_fields = ['id', 'ecart']

    def get_article_code(self, obj):
        return obj.article.code if obj.article else None

    def get_article_designation(self, obj):
        return obj.article.designation if obj.article else None


class InventaireSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    magasin_nom = serializers.SerializerMethodField(read_only=True)
    responsable_nom = serializers.SerializerMethodField(read_only=True)
    lignes = LigneInventaireSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inventaire
        fields = [
            'id', 'reference',
            'magasin', 'magasin_nom',
            'date_inventaire',
            'statut', 'statut_display',
            'responsable', 'responsable_nom',
            'notes',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'date_inventaire', 'created_at', 'updated_at']

    def get_magasin_nom(self, obj):
        return obj.magasin.nom if obj.magasin else None

    def get_responsable_nom(self, obj):
        if not obj.responsable:
            return None
        return obj.responsable.get_full_name() or obj.responsable.email

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()


class InventaireListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    magasin_nom = serializers.SerializerMethodField()

    class Meta:
        model = Inventaire
        fields = [
            'id', 'reference',
            'magasin_nom',
            'date_inventaire',
            'statut', 'statut_display',
        ]

    def get_magasin_nom(self, obj):
        return obj.magasin.nom if obj.magasin else None