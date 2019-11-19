import spotipy
import my_settings
import requests
import spotipy.util as util


def clean_artist_and_track(request_string):

    return request_string.replace("#", "")


def get_potential_genres(base_url, artist, track):

    request_string = clean_artist_and_track(
        f'''{base_url}&artist={artist}&track={track}&format=json''')
    print(request_string)
    response = requests.get(request_string).json()
    try:
        toptags = response['track']['toptags']['tag']
    except:
        toptags = ''

    tags_list = [value['name'] for value in toptags]
    return tags_list


def fetch_playlist_tracks():

    token = util.oauth2.SpotifyClientCredentials(
        client_id=my_settings.SPOTIPY_CLIENT_ID,
        client_secret=my_settings.SPOTIPY_CLIENT_SECRET
    )

    cache_token = token.get_access_token()
    spotify = spotipy.Spotify(cache_token)

    # playlists = [{'name': 'All Out 70s'},
    #              {'name': 'All Out 80s'},
    #              {'name': 'All Out 90s'},
    #              {'name': 'All Out 00s'},
    #              {'name': 'All Out 10s'},
    #              {'name': 'BIGGEST PLAYLIST WITH ALL THE BEST SONGS'}]
    playlists = [{'name': 'BIGGEST PLAYLIST WITH ALL THE BEST SONGS'}]

    all_tracks = []

    for playlist in playlists:
        playlist_data = spotify.search(q=playlist['name'], type='playlist')

        for matched_playlist in playlist_data['playlists']['items']:

            if matched_playlist['name'] == playlist['name']:
                playlist['id'] = matched_playlist['id']
                playlist['owner'] = matched_playlist['owner']['id']

                tracks = spotify.user_playlist_tracks(
                    user=playlist['owner'],
                    playlist_id=playlist['id'])

                while tracks['next']:
                    print(tracks['next'])

                    for item in tracks['items']:
                        try:
                            all_tracks.append(
                                {'artist_name': item['track']['artists'][0]['name'],
                                 'track_name': item['track']['name']})
                        except:
                            print(item)
                    tracks = spotify.next(tracks)

                break

    return all_tracks


def main():
    lastfm_base_url = f'''http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={my_settings.LASTFM_TOKEN}'''
    tracks = fetch_playlist_tracks()

    for track in tracks:
        track['genre'] = get_potential_genres(
            lastfm_base_url,
            track['artist_name'].replace(' ', '').replace("'", '').lower(),
            track['track_name'].replace(' ', '').replace("'", '').lower())

    tracks_with_genres = [track for track in tracks if track['genre'] != []]

    print(tracks_with_genres)


if __name__ == '__main__':
    main()
