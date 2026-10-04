# core/constants.py
"""
Constantes métier centralisées pour toute la plateforme APG.
Utilisables dans les modèles, serializers, vues, formulaires.
"""

# ============================================================
# RÔLES UTILISATEURS
# ============================================================
ROLE_PDG = 'pdg'
ROLE_ADMIN = 'admin'  # Alias historique de pdg
ROLE_RH = 'rh'
ROLE_COMPTABLE = 'comptable'
ROLE_LOGISTIQUE = 'logistique'
ROLE_SUPERVISEUR = 'superviseur'
ROLE_EMPLOYE = 'employe'

ROLE_CHOICES = [
    (ROLE_PDG, 'PDG / Administrateur Général'),
    (ROLE_RH, 'Responsable RH'),
    (ROLE_COMPTABLE, 'Responsable Comptabilité'),
    (ROLE_LOGISTIQUE, 'Responsable Logistique'),
    (ROLE_SUPERVISEUR, 'Responsable Exploitation / Superviseur'),
    (ROLE_EMPLOYE, 'Employé'),
]

STAFF_ROLES = [ROLE_PDG, ROLE_ADMIN, ROLE_RH,
               ROLE_COMPTABLE, ROLE_LOGISTIQUE, ROLE_SUPERVISEUR]
ADMIN_ROLES = [ROLE_PDG, ROLE_ADMIN]


# ============================================================
# DEVISES & MONNAIES
# ============================================================
DEVISE_DEFAUT = 'GNF'
DEVISES = [
    ('GNF', 'Franc Guinéen'),
    ('USD', 'Dollar US'),
    ('EUR', 'Euro'),
]


# ============================================================
# STATUTS COMMUNS
# ============================================================
STATUT_ACTIF = 'actif'
STATUT_INACTIF = 'inactif'
STATUT_ARCHIVE = 'archive'

STATUT_CHOICES_COMMUN = [
    (STATUT_ACTIF, 'Actif'),
    (STATUT_INACTIF, 'Inactif'),
    (STATUT_ARCHIVE, 'Archivé'),
]

# Workflow générique
STATUT_BROUILLON = 'brouillon'
STATUT_EN_ATTENTE = 'en_attente'
STATUT_VALIDE = 'valide'
STATUT_REFUSE = 'refuse'
STATUT_ANNULE = 'annule'
STATUT_TERMINE = 'termine'

STATUT_WORKFLOW_CHOICES = [
    (STATUT_BROUILLON, 'Brouillon'),
    (STATUT_EN_ATTENTE, 'En attente'),
    (STATUT_VALIDE, 'Validé'),
    (STATUT_REFUSE, 'Refusé'),
    (STATUT_ANNULE, 'Annulé'),
    (STATUT_TERMINE, 'Terminé'),
]


# ============================================================
# TYPES DE CONTRAT
# ============================================================
TYPE_CONTRAT_CDI = 'CDI'
TYPE_CONTRAT_CDD = 'CDD'
TYPE_CONTRAT_STAGE = 'STAGE'
TYPE_CONTRAT_TEMPORAIRE = 'TEMPORAIRE'

TYPE_CONTRAT_CHOICES = [
    (TYPE_CONTRAT_CDI, 'CDI'),
    (TYPE_CONTRAT_CDD, 'CDD'),
    (TYPE_CONTRAT_STAGE, 'Stage'),
    (TYPE_CONTRAT_TEMPORAIRE, 'Temporaire'),
]


# ============================================================
# STATUTS PRÉSENCE
# ============================================================
PRESENCE_PRESENT = 'present'
PRESENCE_ABSENT = 'absent'
PRESENCE_RETARD = 'retard'
PRESENCE_MISSION = 'mission'
PRESENCE_CONGE = 'conge'
PRESENCE_REPOS = 'repos'
PRESENCE_DEPART_ANTICIPE = 'depart_anticipe'

PRESENCE_STATUT_CHOICES = [
    (PRESENCE_PRESENT, 'Présent'),
    (PRESENCE_ABSENT, 'Absent'),
    (PRESENCE_RETARD, 'Retard'),
    (PRESENCE_MISSION, 'Mission'),
    (PRESENCE_CONGE, 'Congé'),
    (PRESENCE_REPOS, 'Repos'),
    (PRESENCE_DEPART_ANTICIPE, 'Départ anticipé'),
]


# ============================================================
# TYPES DE CONGÉ
# ============================================================
CONGE_ANNUEL = 'annuel'
CONGE_MALADIE = 'maladie'
CONGE_MATERNITE = 'maternite'
CONGE_EXCEPTIONNEL = 'exceptionnel'

CONGE_TYPE_CHOICES = [
    (CONGE_ANNUEL, 'Congé annuel'),
    (CONGE_MALADIE, 'Congé maladie'),
    (CONGE_MATERNITE, 'Congé maternité'),
    (CONGE_EXCEPTIONNEL, 'Congé exceptionnel'),
]


# ============================================================
# STATUTS FACTURE
# ============================================================
FACTURE_NON_PAYEE = 'non_payee'
FACTURE_PARTIELLE = 'partielle'
FACTURE_PAYEE = 'payee'
FACTURE_EN_RETARD = 'en_retard'
FACTURE_LITIGE = 'litige'
FACTURE_ANNULEE = 'annulee'

FACTURE_STATUT_CHOICES = [
    (FACTURE_NON_PAYEE, 'Non payée'),
    (FACTURE_PARTIELLE, 'Partiellement payée'),
    (FACTURE_PAYEE, 'Payée'),
    (FACTURE_EN_RETARD, 'En retard'),
    (FACTURE_LITIGE, 'Litige'),
    (FACTURE_ANNULEE, 'Annulée'),
]


# ============================================================
# TYPES DE FACTURE
# ============================================================
FACTURE_TYPE_DEFINITIVE = 'definitive'
FACTURE_TYPE_PROFORMA = 'proforma'

FACTURE_TYPE_CHOICES = [
    (FACTURE_TYPE_DEFINITIVE, 'Définitive'),
    (FACTURE_TYPE_PROFORMA, 'Pro-forma'),
]


# ============================================================
# STATUTS DEVIS
# ============================================================
DEVIS_BROUILLON = 'brouillon'
DEVIS_ENVOYE = 'envoye'
DEVIS_ACCEPTE = 'accepte'
DEVIS_REFUSE = 'refuse'
DEVIS_EXPIRE = 'expire'

DEVIS_STATUT_CHOICES = [
    (DEVIS_BROUILLON, 'Brouillon'),
    (DEVIS_ENVOYE, 'Envoyé'),
    (DEVIS_ACCEPTE, 'Accepté'),
    (DEVIS_REFUSE, 'Refusé'),
    (DEVIS_EXPIRE, 'Expiré'),
]


# ============================================================
# MODES DE PAIEMENT
# ============================================================
PAIEMENT_ESPECES = 'especes'
PAIEMENT_VIREMENT = 'virement'
PAIEMENT_CHEQUE = 'cheque'
PAIEMENT_MOBILE_MONEY = 'mobile_money'
PAIEMENT_CARTE = 'carte'

PAIEMENT_MODE_CHOICES = [
    (PAIEMENT_ESPECES, 'Espèces'),
    (PAIEMENT_VIREMENT, 'Virement bancaire'),
    (PAIEMENT_CHEQUE, 'Chèque'),
    (PAIEMENT_MOBILE_MONEY, 'Mobile Money'),
    (PAIEMENT_CARTE, 'Carte bancaire'),
]


# ============================================================
# TYPES DE COMPTE DE TRÉSORERIE
# ============================================================
COMPTE_CAISSE = 'caisse'
COMPTE_BANQUE = 'banque'
COMPTE_MOBILE_MONEY = 'mobile_money'

COMPTE_TYPE_CHOICES = [
    (COMPTE_CAISSE, 'Caisse'),
    (COMPTE_BANQUE, 'Banque'),
    (COMPTE_MOBILE_MONEY, 'Mobile Money'),
]


# ============================================================
# STATUTS DE PAIE
# ============================================================
PAIE_BROUILLON = 'brouillon'
PAIE_CALCULEE = 'calculee'
PAIE_CONTROLEE = 'controlee'
PAIE_VALIDEE = 'validee'
PAIE_EN_ATTENTE_PAIEMENT = 'en_attente_paiement'
PAIE_PAYEE = 'payee'
PAIE_ANNULEE = 'annulee'

PAIE_STATUT_CHOICES = [
    (PAIE_BROUILLON, 'Brouillon'),
    (PAIE_CALCULEE, 'Calculée'),
    (PAIE_CONTROLEE, 'Contrôlée'),
    (PAIE_VALIDEE, 'Validée'),
    (PAIE_EN_ATTENTE_PAIEMENT, 'En attente de paiement'),
    (PAIE_PAYEE, 'Payée'),
    (PAIE_ANNULEE, 'Annulée'),
]


# ============================================================
# TYPES DE CLIENT
# ============================================================
CLIENT_PARTICULIER = 'particulier'
CLIENT_ENTREPRISE = 'entreprise'
CLIENT_ADMINISTRATION = 'administration'
CLIENT_ONG = 'ong'
CLIENT_COLLECTIVITE = 'collectivite'
CLIENT_COMMERCE = 'commerce'
CLIENT_HOTEL = 'hotel'
CLIENT_ECOLE = 'ecole'

CLIENT_TYPE_CHOICES = [
    (CLIENT_PARTICULIER, 'Particulier'),
    (CLIENT_ENTREPRISE, 'Entreprise'),
    (CLIENT_ADMINISTRATION, 'Administration'),
    (CLIENT_ONG, 'ONG'),
    (CLIENT_COLLECTIVITE, 'Collectivité'),
    (CLIENT_COMMERCE, 'Commerce'),
    (CLIENT_HOTEL, 'Hôtel'),
    (CLIENT_ECOLE, 'Établissement scolaire'),
]


# ============================================================
# TYPES DE MOUVEMENT DE STOCK
# ============================================================
MOUVEMENT_ENTREE = 'entree'
MOUVEMENT_SORTIE = 'sortie'
MOUVEMENT_TRANSFERT = 'transfert'
MOUVEMENT_AJUSTEMENT = 'ajustement'

MOUVEMENT_TYPE_CHOICES = [
    (MOUVEMENT_ENTREE, 'Entrée'),
    (MOUVEMENT_SORTIE, 'Sortie'),
    (MOUVEMENT_TRANSFERT, 'Transfert'),
    (MOUVEMENT_AJUSTEMENT, 'Ajustement'),
]

MOTIF_ENTREE_CHOICES = [
    ('achat', 'Achat'),
    ('retour', 'Retour'),
    ('transfert', 'Transfert'),
    ('don', 'Don'),
    ('correction', 'Correction'),
]

MOTIF_SORTIE_CHOICES = [
    ('affectation', 'Affectation'),
    ('consommation', 'Consommation'),
    ('transfert', 'Transfert'),
    ('perte', 'Perte'),
    ('deterioration', 'Détérioration'),
    ('retour_fournisseur', 'Retour fournisseur'),
]


# ============================================================
# TYPES DE VÉHICULE
# ============================================================
VEHICULE_TRICYCLE = 'tricycle'
VEHICULE_CAMION = 'camion'
VEHICULE_VOITURE = 'voiture'
VEHICULE_MOTO = 'moto'

VEHICULE_TYPE_CHOICES = [
    (VEHICULE_TRICYCLE, 'Tricycle'),
    (VEHICULE_CAMION, 'Camion'),
    (VEHICULE_VOITURE, 'Voiture'),
    (VEHICULE_MOTO, 'Moto'),
]

VEHICULE_ETAT_CHOICES = [
    ('disponible', 'Disponible'),
    ('en_service', 'En service'),
    ('panne', 'En panne'),
    ('entretien', 'En entretien'),
    ('hors_service', 'Hors service'),
]


# ============================================================
# TYPES DE MAINTENANCE
# ============================================================
MAINTENANCE_PREVENTIVE = 'preventive'
MAINTENANCE_CORRECTIVE = 'corrective'
MAINTENANCE_VIDANGE = 'vidange'

MAINTENANCE_TYPE_CHOICES = [
    (MAINTENANCE_PREVENTIVE, 'Préventive'),
    (MAINTENANCE_CORRECTIVE, 'Corrective'),
    (MAINTENANCE_VIDANGE, 'Vidange'),
]


# ============================================================
# TYPES DE CARBURANT
# ============================================================
CARBURANT_ESSENCE = 'essence'
CARBURANT_GASOIL = 'gasoil'
CARBURANT_HUILE = 'huile'

CARBURANT_TYPE_CHOICES = [
    (CARBURANT_ESSENCE, 'Essence'),
    (CARBURANT_GASOIL, 'Gasoil'),
    (CARBURANT_HUILE, 'Huile'),
]


# ============================================================
# STATUTS MISSION
# ============================================================
MISSION_PLANIFIEE = 'planifiee'
MISSION_EN_COURS = 'en_cours'
MISSION_TERMINEE = 'terminee'
MISSION_ANNULEE = 'annulee'

MISSION_STATUT_CHOICES = [
    (MISSION_PLANIFIEE, 'Planifiée'),
    (MISSION_EN_COURS, 'En cours'),
    (MISSION_TERMINEE, 'Terminée'),
    (MISSION_ANNULEE, 'Annulée'),
]


# ============================================================
# TYPES DE NOTIFICATION
# ============================================================
NOTIF_INFO = 'info'
NOTIF_ALERTE = 'alerte'
NOTIF_VALIDATION = 'validation'
NOTIF_SYSTEME = 'systeme'

NOTIF_TYPE_CHOICES = [
    (NOTIF_INFO, 'Information'),
    (NOTIF_ALERTE, 'Alerte'),
    (NOTIF_VALIDATION, 'Validation'),
    (NOTIF_SYSTEME, 'Système'),
]


# ============================================================
# TYPES DE DOCUMENT
# ============================================================
DOC_CONTRAT = 'contrat'
DOC_FACTURE = 'facture'
DOC_RECU = 'recu'
DOC_BON_COMMANDE = 'bon_commande'
DOC_BON_LIVRAISON = 'bon_livraison'
DOC_JUSTIFICATIF = 'justificatif'
DOC_CONTRAT_TRAVAIL = 'contrat_travail'
DOC_PIECE_ADMIN = 'piece_admin'
DOC_VEHICULE = 'document_vehicule'
DOC_FOURNISSEUR = 'document_fournisseur'

DOC_TYPE_CHOICES = [
    (DOC_CONTRAT, 'Contrat'),
    (DOC_FACTURE, 'Facture'),
    (DOC_RECU, 'Reçu'),
    (DOC_BON_COMMANDE, 'Bon de commande'),
    (DOC_BON_LIVRAISON, 'Bon de livraison'),
    (DOC_JUSTIFICATIF, 'Justificatif'),
    (DOC_CONTRAT_TRAVAIL, 'Contrat de travail'),
    (DOC_PIECE_ADMIN, 'Pièce administrative'),
    (DOC_VEHICULE, 'Document véhicule'),
    (DOC_FOURNISSEUR, 'Document fournisseur'),
]


# ============================================================
# PRÉFIXES DE NUMÉROTATION (conformes au cahier des charges)
# ============================================================
PREFIX_FACTURE = 'FACT'
PREFIX_DEVIS = 'DEV'
PREFIX_PROFORMA = 'PRO'
PREFIX_BON_COMMANDE = 'BC'
PREFIX_DEPENSE = 'DEP'
PREFIX_ENCAISSEMENT = 'ENC'
PREFIX_DECAISSEMENT = 'DEC'
PREFIX_EMPLOYE = 'RH-EMP'
PREFIX_CONTRAT = 'CTR'
PREFIX_CONGE = 'CGE'
PREFIX_TRICYCLE = 'TR'
PREFIX_VEHICULE = 'VEH'
PREFIX_MISSION = 'MIS'
PREFIX_MAINTENANCE = 'MNT'
PREFIX_CARBURANT = 'CBT'
PREFIX_DEMANDE_ACHAT = 'DA'
PREFIX_RECEPTION = 'REC'
PREFIX_PAIEMENT = 'PAY'


# ============================================================
# SEUILS & ALERTES
# ============================================================
SEUIL_STOCK_CRITIQUE = 10
SEUIL_CAISSE_BASSE = 100000  # 100 000 GNF
JOURS_ALERTE_CONTRAT_EXPIRATION = 30  # 30 jours avant expiration
JOURS_ALERTE_FACTURE_ECHEANCE = 7     # 7 jours avant échéance


# ============================================================
# TAUX (à ajuster selon la réglementation guinéenne)
# ============================================================
TAUX_TVA = 18  # 18% en Guinée
TAUX_CNSS_EMPLOYE = 5    # 5% (part employé)
TAUX_CNSS_EMPLOYEUR = 18  # 18% (part employeur)


# ============================================================
# MESSAGES DE VALIDATION
# ============================================================
MSG_ACCES_REFUSE = "Vous n'avez pas la permission d'effectuer cette action."
MSG_OBJET_INTROUVABLE = "L'objet demandé n'existe pas."
MSG_VALIDATION_REQUISE = "Cette opération nécessite une validation."
MSG_MONTANT_INVALIDE = "Le montant spécifié est invalide."
MSG_STOCK_INSUFFISANT = "Le stock disponible est insuffisant."
MSG_FACTURE_VERROUILLEE = "Cette facture ne peut plus être modifiée."
