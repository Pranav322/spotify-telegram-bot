from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from .models import SpotifyUser  # Make sure this import matches your project structure
from django.http import JsonResponse
from spotipy import Spotify

@csrf_exempt
def spotify_callback(request):
    if request.method == 'GET':
        code = request.GET.get('code')
        state = request.GET.get('state')

        if state is None or code is None:
            return HttpResponse("Missing state or code parameter.", status=400)

        try:
            user_id = int(state)
        except ValueError:
            return HttpResponse("Invalid state parameter.", status=400)

        sp_oauth = SpotifyOAuth(
            client_id="089524721b034aedb34a7914e4b96144",
            client_secret="721c4e2992a84b3787dd9e72f71db1cc",
            redirect_uri="https://pranawww.pythonanywhere.com/api/callback",
            scope="playlist-read-private user-library-read user-read-playback-state",
            state=state,
            
        )

    #     token_info = sp_oauth.get_access_token(code, as_dict=False)

   

        token_info = sp_oauth.get_access_token(code, as_dict=True)

        if token_info:
            access_token = token_info['access_token']
            refresh_token = token_info['refresh_token']
            expires_in = token_info['expires_in']
    
    # Update or create the SpotifyUser instance with the new token information
            spotify_user, _ = SpotifyUser.objects.update_or_create(
            telegram_user_id=user_id,
            defaults={
                'spotify_access_token': access_token,
                'spotify_refresh_token': refresh_token,
                # Ensure that the expiration time is correctly calculated based on the current time
                'token_expiry': timezone.now() + timezone.timedelta(seconds=expires_in)
                }
        )
            return HttpResponse("Authentication successful! You can close this window.")
        else:
            return HttpResponse("Failed to retrieve access token from Spotify.", status=400)

# checking if users authentication token is expired or not 
def get_authenticated_spotify_client(user_id):
    try:
        spotify_user = SpotifyUser.objects.get(telegram_user_id=user_id)
    except SpotifyUser.DoesNotExist:
        return None  # User not found

    if spotify_user.is_token_expired:
        # Refresh the token
        sp_oauth = SpotifyOAuth(
            client_id="089524721b034aedb34a7914e4b96144",
            client_secret="721c4e2992a84b3787dd9e72f71db1cc",
            redirect_uri="https://pranawww.pythonanywhere.com/api/callback",
            scope="playlist-read-private user-library-read user-read-playback-state",
        
        )
        token_info = sp_oauth.refresh_access_token(spotify_user.spotify_refresh_token)

        # Update and save the new access token and expiry in the database
        spotify_user.spotify_access_token = token_info['access_token']
        spotify_user.token_expiry = timezone.now() + timezone.timedelta(seconds=token_info['expires_in'])
        spotify_user.save()

    # Return a Spotipy client using the refreshed or valid access token
    return Spotify(auth=spotify_user.spotify_access_token)



def check_user_id(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')

        if user_id is None:
            return JsonResponse({"error": "User ID parameter is missing."}, status=400)

        try:
            user_id = int(user_id)
        except ValueError:
            return JsonResponse({"error": "Invalid user ID parameter."}, status=400)

        # Check if the user ID exists in the SpotifyUser model
        if SpotifyUser.objects.filter(telegram_user_id=user_id).exists():
            return JsonResponse({"exists": True})
        else:
            return JsonResponse({"exists": False})

    return JsonResponse({"error": "Method not allowed."}, status=405)


def get_user_playlists(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')

        if user_id is None:
            return JsonResponse({"error": "User ID parameter is missing."}, status=400)

        try:
            user_id = int(user_id)
        except ValueError:
            return JsonResponse({"error": "Invalid user ID parameter."}, status=400)

        # Use the utility function to get an authenticated Spotipy client
        sp = get_authenticated_spotify_client(user_id)

        if not sp:
            # If sp is None, it means the user wasn't found or the token couldn't be refreshed
            return JsonResponse({"error": "Failed to authenticate with Spotify or user not found."}, status=404)

        # Fetch user's playlists from Spotify
        playlists = sp.current_user_playlists()

        # Extract playlist names
        playlist_data = [{
            "name": playlist['name'],
            "id": playlist['id']
        } for playlist in playlists['items']]

        return JsonResponse({"playlists": playlist_data})

    return JsonResponse({"error": "Method not allowed."}, status=405)