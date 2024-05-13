# serializers.py
from rest_framework import serializers
from .models import ScrapeResult

class ScrapeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeResult
        fields = ['url']