from django.urls import path
from .views import spotify_callback , check_user_id , get_user_playlists

urlpatterns = [
  
    path('callback/' , spotify_callback , name = "callback"),
    path('check/' , check_user_id , name = "check_user"),
    path('playlist/' , get_user_playlists , name = "user_playlists")
    # Add other URL patterns as needed
]