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
            scope="playlist-read-private user-library-read user-read-playback-state playlist-modify-public playlist-modify-private user-read-currently-playing user-modify-playback-state user-read-private",
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

from django.views.decorators.http import require_http_methods

import json
# Ensure the get_authenticated_spotify_client and any other imports are correctly added

@csrf_exempt
@require_http_methods(["POST"])
def merge_playlists(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id1 = data['user_id1']
        user_id2 = data['user_id2']
    except KeyError:
        return JsonResponse({'error': 'Missing data.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    try:
        client1 = get_authenticated_spotify_client(user_id1)

        client2 = get_authenticated_spotify_client(user_id2)
        if not client1 or not client2:
            raise Exception('Authentication failed for one or both users.')

        user1_track_uris = [item['track']['uri'] for item in client1.current_user_saved_tracks(limit=50)['items']]
        user2_track_uris = [item['track']['uri'] for item in client2.current_user_saved_tracks(limit=50)['items']]

        merged_track_uris = list(set(user1_track_uris + user2_track_uris))

        playlist_name = "Merged Playlist"
        user_profile = client1.me()
        new_playlist = client1.user_playlist_create(user_profile['id'], playlist_name, public=True)

        for i in range(0, len(merged_track_uris), 100):
            batch = merged_track_uris[i:i+100]
            client1.playlist_add_items(new_playlist['id'], batch)

        playlist_url = new_playlist['external_urls']['spotify']
        return JsonResponse({'playlist_link': playlist_url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)






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

@require_http_methods(["GET"])
def current_playing_song(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'error': 'Missing user ID.'}, status=400)

    try:
        spotify_client = get_authenticated_spotify_client(user_id)
        if spotify_client:
            current_track = spotify_client.current_user_playing_track()
            if current_track and current_track.get('is_playing'):
                track_name = current_track['item']['name']
                artist_names = [artist['name'] for artist in current_track['item']['artists']]
                return JsonResponse({
                    'track_name': track_name,
                    'artists': artist_names,
                    'is_playing': current_track.get('is_playing'),
                })
            else:
                return JsonResponse({'message': 'No track is currently playing.'})
        else:
            return JsonResponse({'error': 'Failed to authenticate Spotify client.'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



# spotify_utils.py

def play_song_on_spotify(clients, song_name):
    """
    Search for a song by name and start playback on Spotify client(s) active devices.

    Parameters:
    - clients: A single authenticated Spotipy client object or a list of client objects.
    - song_name: The name of the song to search for and play.

    Returns:
    - success: A boolean indicating if the song was successfully played.
    """
    if not isinstance(clients, list):
        clients = [clients]  # Convert single client to a list for consistency

    # Search for the song to get its URI
    search_result = clients[0].search(q=song_name, type='track', limit=1)
    tracks = search_result['tracks']['items']
    
    if not tracks:
        print("Song not found.")
        return False
    
    track_uri = tracks[0]['uri']
    
    # Attempt to start playback on each user's active device
    for client in clients:
        try:
            client.start_playback(uris=[track_uri])
        except Exception as e:
            print(f"Failed to start playback for one of the users: {e}")
            return False
    
    return True



# views.py

# from .utils import play_song_on_spotify

@csrf_exempt
@require_http_methods(["POST"])
def play_song(request):
    try:
        # Check content type
        if not request.content_type == 'application/json':
            return JsonResponse({'error': 'Content-Type must be application/json.'}, status=400)
        
        # Parse JSON data
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        song_name = data.get('song_name')
        if not user_id or not song_name:
            return JsonResponse({'error': 'Missing user ID or song name.'}, status=400)

        # Attempt to authenticate Spotify client
        spotify_client = get_authenticated_spotify_client(user_id)
        if not spotify_client:
            return JsonResponse({'error': 'Failed to authenticate Spotify client.'}, status=401)

        # Call function to play song
        play_song_on_spotify(spotify_client, song_name)
        return JsonResponse({'message': 'Playback started.'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def play_together(request):
    try:
        # Parse JSON data
        data = json.loads(request.body.decode('utf-8'))
        requester_user_id = data.get('requester_user_id')
        target_user_id = data.get('target_user_id')
        song_name = data.get('song_name')
        if not requester_user_id or not target_user_id or not song_name:
            return JsonResponse({'error': 'Missing requester_user_id, target_user_id, or song_name.'}, status=400)

        # Authenticate Spotify clients for both users
        requester_client = get_authenticated_spotify_client(requester_user_id)
        target_client = get_authenticated_spotify_client(target_user_id)

        if not requester_client or not target_client:
            return JsonResponse({'error': 'Authentication failed for one or both users.'}, status=401)
        
        # Example function to search and play a song on Spotify
        success = play_song_on_spotify([requester_client, target_client], song_name)

        if success:
            message = "Song is now playing on both devices."
        else:
            message = "Failed to play the song."

        return JsonResponse({'message': message})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
