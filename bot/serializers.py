from rest_framework import serializers
from .models import SpotifyUser

class SpotifyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotifyUser
        fields = '__all__' 

