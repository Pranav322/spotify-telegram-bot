from django.urls import path
from .views import spotify_callback , check_user_id , get_user_playlists , merge_playlists , current_playing_song , play_song , play_together

urlpatterns = [
  
    path('callback/' , spotify_callback , name = "callback"),
    path('check/' , check_user_id , name = "check_user"),
    path('playlist/' , get_user_playlists , name = "user_playlists"),
    path('mergeplaylists/' , merge_playlists , name = "merge_playlist"),
    path('current_playing_song/' ,current_playing_song , name = "current_playing_song"),
    path('play_song/' , play_song , name = "play_song"),
    path('play_together/' , play_together , name = "play_together")
]
