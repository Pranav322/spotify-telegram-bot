# spotify_utils.py
def play_song_on_spotify(spotify_client, song_name):
    try:
        # Search for the song to get its URI
        results = spotify_client.search(q=song_name, type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            raise Exception('Song not found.')

        song_uri = tracks[0]['uri']

        # Start playback
        spotify_client.start_playback(uris=[song_uri])
        return True  # Indicate success

    except Exception as e:
        error_message = str(e)
        if 'expired' in error_message.lower():
            # Handle expired token error
            return 'Authentication token expired. Please re-authenticate.'
        else:
            return f'Error playing song: {error_message}'
