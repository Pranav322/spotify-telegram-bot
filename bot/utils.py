# spotify_utils.py
def play_song_on_spotify(spotify_client, song_name):
    # Search for the song to get its URI
    results = spotify_client.search(q=song_name, type='track', limit=1)
    tracks = results['tracks']['items']
    if not tracks:
        raise Exception('Song not found.')
    
    song_uri = tracks[0]['uri']
    
    # Start playback
    spotify_client.start_playback(uris=[song_uri])

    