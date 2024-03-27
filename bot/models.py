from django.db import models
import datetime
from django.utils import timezone
# Create your models here.
class SpotifyUser(models.Model):

    telegram_user_id = models.IntegerField(unique=True)
    spotify_access_token = models.CharField(max_length=255)
    spotify_refresh_token = models.CharField(max_length=255)
    token_expiry = models.DateTimeField(null=True, blank=True)

    @property
    def is_token_expired(self):
        """
        Check if the access token is expired.
        """
        return self.token_expiry <= timezone.now()