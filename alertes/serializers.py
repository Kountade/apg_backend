# alertes/serializers.py
from rest_framework import serializers
from .models import ConfigAlerte, CanalNotification


class ConfigAlerteSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    gravite_display = serializers.CharField(source='get_gravite_display', read_only=True)

    class Meta:
        model = ConfigAlerte
        fields = [
            'id', 'type', 'type_display',
            'libelle', 'description',
            'gravite', 'gravite_display',
            'seuil_jours', 'seuil_valeur',
            'active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CanalNotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = CanalNotification
        fields = [
            'id', 'nom', 'type', 'type_display',
            'configuration', 'actif', 'ordre',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']