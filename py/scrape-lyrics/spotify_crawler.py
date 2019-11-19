import spotipy
import spotipy.util as util
import my_settings
import requests
import csv
import pprint



def initialize_spotify_connection():
    '''
    Instantiate spotify client object using authorization code flow:
    https://developer.spotify.com/documentation/general/guides/authorization-guide/#authorization-code-flow
    :return spotify: spotify api client object
    '''
    token = util.oauth2.SpotifyClientCredentials(
        client_id=my_settings.SPOTIPY_CLIENT_ID,
        client_secret=my_settings.SPOTIPY_CLIENT_SECRET
    )
    cache_token = token.get_access_token()
    spotify = spotipy.Spotify(cache_token)

    return spotify


def read_csv(path):
    with open(path) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            print(row[1])


def main():
    spotify = initialize_spotify_connection()
    read_csv(my_settings.DATA_PATH / "playlists_merged_sample.csv")

    urn = "spotify:track:69uxyAqqPIsUyTO8txoP2M"
    track = spotify.track(urn)
    pprint.pprint(spotify.audio_features(urn))


if __name__ == '__main__':
    main()
