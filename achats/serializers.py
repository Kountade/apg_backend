# achats/serializers.py
from rest_framework import serializers
from .models import (
    Fournisseur, EvaluationFournisseur,
    DemandeAchat, LigneDemandeAchat,
    DevisFournisseur, LigneDevisFournisseur,
    BonCommande, LigneBonCommande,
    Reception, LigneReception,
    FactureFournisseur, PaiementFournisseur,
)


# ============================================================
# FOURNISSEUR
# ============================================================

class FournisseurSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    nombre_devis = serializers.SerializerMethodField(read_only=True)
    nombre_bons_commande = serializers.SerializerMethodField(read_only=True)
    nombre_factures = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Fournisseur
        fields = [
            'id', 'code', 'nom', 'sigle',
            'type', 'type_display',
            'statut', 'statut_display',
            'num_contribuable', 'num_rccm',
            'telephone', 'telephone2', 'email',
            'adresse', 'ville', 'pays',
            'contact_nom', 'contact_fonction',
            'contact_telephone', 'contact_email',
            'delai_livraison_jours', 'conditions_paiement', 'remise_habituelle',
            'banque', 'numero_compte', 'iban',
            'note_moyenne',
            'logo', 'notes',
            'nombre_devis', 'nombre_bons_commande', 'nombre_factures',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'updated_at', 'is_deleted',
            'note_moyenne',
        ]

    def get_nombre_devis(self, obj):
        return obj.devis.count()

    def get_nombre_bons_commande(self, obj):
        return obj.bons_commande.count()

    def get_nombre_factures(self, obj):
        return obj.factures.count()


class FournisseurListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Fournisseur
        fields = [
            'id', 'code', 'nom', 'sigle',
            'type', 'type_display',
            'statut', 'statut_display',
            'telephone', 'email', 'ville',
            'note_moyenne', 'logo',
        ]


# ============================================================
# ÉVALUATION FOURNISSEUR
# ============================================================

class EvaluationFournisseurSerializer(serializers.ModelSerializer):
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    evaluateur_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EvaluationFournisseur
        fields = [
            'id', 'fournisseur', 'fournisseur_nom',
            'date_evaluation', 'periode',
            'note_qualite', 'note_prix', 'note_delai', 'note_service',
            'note_globale',
            'commentaire',
            'evaluateur', 'evaluateur_nom',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'date_evaluation', 'note_globale', 'created_at', 'updated_at']

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_evaluateur_nom(self, obj):
        if not obj.evaluateur:
            return None
        return obj.evaluateur.get_full_name() or obj.evaluateur.email


# ============================================================
# DEMANDE D'ACHAT
# ============================================================

class LigneDemandeAchatSerializer(serializers.ModelSerializer):
    article_stock_code = serializers.SerializerMethodField(read_only=True)
    article_stock_designation = serializers.SerializerMethodField(read_only=True)
    montant_estime = serializers.ReadOnlyField()

    class Meta:
        model = LigneDemandeAchat
        fields = [
            'id', 'demande', 'ordre',
            'designation', 'description',
            'quantite', 'unite', 'prix_estime',
            'article_stock', 'article_stock_code', 'article_stock_designation',
            'montant_estime',
        ]
        read_only_fields = ['id', 'montant_estime']

    def get_article_stock_code(self, obj):
        return obj.article_stock.code if obj.article_stock else None

    def get_article_stock_designation(self, obj):
        return obj.article_stock.designation if obj.article_stock else None


class DemandeAchatSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    urgence_display = serializers.CharField(source='get_urgence_display', read_only=True)
    demandeur_nom = serializers.SerializerMethodField(read_only=True)
    validee_par_nom = serializers.SerializerMethodField(read_only=True)
    lignes = LigneDemandeAchatSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)
    montant_total_estime = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DemandeAchat
        fields = [
            'id', 'numero',
            'date_demande', 'date_souhaitee',
            'demandeur', 'demandeur_nom', 'service',
            'objet', 'motif',
            'urgence', 'urgence_display',
            'statut', 'statut_display',
            'validee_par', 'validee_par_nom',
            'date_validation', 'commentaire_validation',
            'notes',
            'lignes', 'nombre_lignes', 'montant_total_estime',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'date_demande',
            'validee_par', 'date_validation',
            'created_at', 'updated_at',
        ]

    def get_demandeur_nom(self, obj):
        return obj.demandeur.nom_complet if obj.demandeur else None

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()

    def get_montant_total_estime(self, obj):
        return sum(float(l.montant_estime) for l in obj.lignes.all())


class DemandeAchatListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    urgence_display = serializers.CharField(source='get_urgence_display', read_only=True)
    demandeur_nom = serializers.SerializerMethodField()

    class Meta:
        model = DemandeAchat
        fields = [
            'id', 'numero', 'date_demande',
            'objet', 'demandeur_nom', 'service',
            'urgence', 'urgence_display',
            'statut', 'statut_display',
        ]

    def get_demandeur_nom(self, obj):
        return obj.demandeur.nom_complet if obj.demandeur else None


# ============================================================
# DEVIS FOURNISSEUR
# ============================================================

class LigneDevisFournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneDevisFournisseur
        fields = [
            'id', 'devis', 'ordre',
            'designation', 'quantite', 'unite',
            'prix_unitaire', 'montant_ht',
        ]
        read_only_fields = ['id', 'montant_ht']


class DevisFournisseurSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    demande_achat_numero = serializers.SerializerMethodField(read_only=True)
    lignes = LigneDevisFournisseurSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DevisFournisseur
        fields = [
            'id', 'numero', 'numero_devis_fournisseur',
            'fournisseur', 'fournisseur_nom',
            'demande_achat', 'demande_achat_numero',
            'date_devis', 'date_validite',
            'objet', 'notes',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc',
            'delai_livraison_jours',
            'statut', 'statut_display',
            'fichier_devis',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'montant_tva', 'montant_ttc',
            'created_at', 'updated_at',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_demande_achat_numero(self, obj):
        return obj.demande_achat.numero if obj.demande_achat else None

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()


class DevisFournisseurListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField()

    class Meta:
        model = DevisFournisseur
        fields = [
            'id', 'numero', 'numero_devis_fournisseur',
            'fournisseur_nom',
            'date_devis', 'date_validite',
            'objet',
            'montant_ht', 'montant_ttc',
            'statut', 'statut_display',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None


# ============================================================
# BON DE COMMANDE
# ============================================================

class LigneBonCommandeSerializer(serializers.ModelSerializer):
    article_stock_code = serializers.SerializerMethodField(read_only=True)
    article_stock_designation = serializers.SerializerMethodField(read_only=True)
    quantite_restante = serializers.ReadOnlyField()
    est_completement_recu = serializers.ReadOnlyField()

    class Meta:
        model = LigneBonCommande
        fields = [
            'id', 'bon_commande', 'ordre',
            'designation', 'description',
            'quantite', 'unite', 'prix_unitaire', 'montant_ht',
            'article_stock', 'article_stock_code', 'article_stock_designation',
            'quantite_recue', 'quantite_restante', 'est_completement_recu',
        ]
        read_only_fields = ['id', 'montant_ht', 'quantite_restante', 'est_completement_recu']

    def get_article_stock_code(self, obj):
        return obj.article_stock.code if obj.article_stock else None

    def get_article_stock_designation(self, obj):
        return obj.article_stock.designation if obj.article_stock else None


class BonCommandeSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    demande_achat_numero = serializers.SerializerMethodField(read_only=True)
    devis_fournisseur_numero = serializers.SerializerMethodField(read_only=True)
    valide_par_nom = serializers.SerializerMethodField(read_only=True)
    lignes = LigneBonCommandeSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BonCommande
        fields = [
            'id', 'numero',
            'fournisseur', 'fournisseur_nom',
            'demande_achat', 'demande_achat_numero',
            'devis_fournisseur', 'devis_fournisseur_numero',
            'date_commande', 'date_livraison_prevue', 'date_livraison_reelle',
            'objet', 'conditions_particulieres',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc',
            'statut', 'statut_display',
            'valide_par', 'valide_par_nom', 'date_validation',
            'fichier_pdf', 'notes',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'montant_tva', 'montant_ttc',
            'valide_par', 'date_validation',
            'created_at', 'updated_at',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_demande_achat_numero(self, obj):
        return obj.demande_achat.numero if obj.demande_achat else None

    def get_devis_fournisseur_numero(self, obj):
        return obj.devis_fournisseur.numero if obj.devis_fournisseur else None

    def get_valide_par_nom(self, obj):
        if not obj.valide_par:
            return None
        return obj.valide_par.get_full_name() or obj.valide_par.email

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()


class BonCommandeListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField()

    class Meta:
        model = BonCommande
        fields = [
            'id', 'numero',
            'fournisseur_nom',
            'date_commande', 'date_livraison_prevue',
            'objet',
            'montant_ht', 'montant_ttc',
            'statut', 'statut_display',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None


# ============================================================
# RÉCEPTION
# ============================================================

class LigneReceptionSerializer(serializers.ModelSerializer):
    ligne_bon_commande_designation = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LigneReception
        fields = [
            'id', 'reception', 'ligne_bon_commande',
            'ligne_bon_commande_designation',
            'quantite_recue', 'quantite_acceptee', 'quantite_refusee',
            'motif_refus',
        ]
        read_only_fields = ['id', 'quantite_refusee']

    def get_ligne_bon_commande_designation(self, obj):
        return obj.ligne_bon_commande.designation if obj.ligne_bon_commande else None


class ReceptionSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    bon_commande_numero = serializers.SerializerMethodField(read_only=True)
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    magasin_destination_nom = serializers.SerializerMethodField(read_only=True)
    controle_par_nom = serializers.SerializerMethodField(read_only=True)
    lignes = LigneReceptionSerializer(many=True, read_only=True)
    nombre_lignes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reception
        fields = [
            'id', 'numero',
            'bon_commande', 'bon_commande_numero',
            'fournisseur', 'fournisseur_nom',
            'date_reception', 'numero_bon_livraison',
            'magasin_destination', 'magasin_destination_nom',
            'statut', 'statut_display',
            'controle_par', 'controle_par_nom', 'date_controle',
            'observations', 'fichier_bon_livraison',
            'lignes', 'nombre_lignes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'controle_par', 'date_controle',
            'created_at', 'updated_at',
        ]

    def get_bon_commande_numero(self, obj):
        return obj.bon_commande.numero if obj.bon_commande else None

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_magasin_destination_nom(self, obj):
        return obj.magasin_destination.nom if obj.magasin_destination else None

    def get_controle_par_nom(self, obj):
        if not obj.controle_par:
            return None
        return obj.controle_par.get_full_name() or obj.controle_par.email

    def get_nombre_lignes(self, obj):
        return obj.lignes.count()


class ReceptionListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    bon_commande_numero = serializers.SerializerMethodField()
    fournisseur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Reception
        fields = [
            'id', 'numero',
            'bon_commande_numero', 'fournisseur_nom',
            'date_reception', 'numero_bon_livraison',
            'statut', 'statut_display',
        ]

    def get_bon_commande_numero(self, obj):
        return obj.bon_commande.numero if obj.bon_commande else None

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None


# ============================================================
# FACTURE FOURNISSEUR
# ============================================================

class FactureFournisseurSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    bon_commande_numero = serializers.SerializerMethodField(read_only=True)
    reception_numero = serializers.SerializerMethodField(read_only=True)
    validee_par_nom = serializers.SerializerMethodField(read_only=True)
    solde_du = serializers.ReadOnlyField()
    est_payee = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = FactureFournisseur
        fields = [
            'id', 'numero_interne', 'numero_facture_fournisseur',
            'fournisseur', 'fournisseur_nom',
            'bon_commande', 'bon_commande_numero',
            'reception', 'reception_numero',
            'date_facture', 'date_echeance',
            'objet',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc', 'montant_paye',
            'solde_du', 'est_payee', 'est_en_retard',
            'statut', 'statut_display',
            'validee_par', 'validee_par_nom', 'date_validation',
            'fichier_pdf', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero_interne',
            'montant_tva', 'montant_ttc',
            'validee_par', 'date_validation',
            'solde_du', 'est_payee', 'est_en_retard',
            'created_at', 'updated_at',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_bon_commande_numero(self, obj):
        return obj.bon_commande.numero if obj.bon_commande else None

    def get_reception_numero(self, obj):
        return obj.reception.numero if obj.reception else None

    def get_validee_par_nom(self, obj):
        if not obj.validee_par:
            return None
        return obj.validee_par.get_full_name() or obj.validee_par.email


class FactureFournisseurListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField()
    solde_du = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()

    class Meta:
        model = FactureFournisseur
        fields = [
            'id', 'numero_interne', 'numero_facture_fournisseur',
            'fournisseur_nom',
            'date_facture', 'date_echeance',
            'objet',
            'montant_ttc', 'montant_paye', 'solde_du',
            'est_en_retard',
            'statut', 'statut_display',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None


# ============================================================
# PAIEMENT FOURNISSEUR
# ============================================================

class PaiementFournisseurSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField(read_only=True)
    facture_numero = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaiementFournisseur
        fields = [
            'id', 'numero',
            'facture', 'facture_numero',
            'fournisseur', 'fournisseur_nom',
            'montant', 'date_paiement',
            'mode', 'mode_display',
            'reference', 'notes',
            'statut', 'statut_display',
            'justificatif',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'created_at', 'updated_at']

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_facture_numero(self, obj):
        return obj.facture.numero_interne if obj.facture else None


class PaiementFournisseurListSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    fournisseur_nom = serializers.SerializerMethodField()

    class Meta:
        model = PaiementFournisseur
        fields = [
            'id', 'numero',
            'fournisseur_nom',
            'montant', 'date_paiement',
            'mode', 'mode_display',
            'statut', 'statut_display',
        ]

    def get_fournisseur_nom(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None