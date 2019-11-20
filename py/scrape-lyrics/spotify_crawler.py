import spotipy
import spotipy.util as util
import my_settings
import requests
import csv
import pandas as pd
import datetime


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


def write_to_csv(songs, index=0):
    '''
    Converts song list to a dataframe and writes it to a csv. Includes handling
    for first batch (open in write mode) or subsequent (open in append mode)
    :param songs: song list
    '''
    csv_fullpath = my_settings.OUTPUT_PATH / 'song_attribs_test.csv'
    songs_df = pd.DataFrame(songs)
    songs_df.set_index("trackid")
    # songs_df.dropna(how="all")

    if index == 0:
        songs_df.to_csv(csv_fullpath, header=True)
    else:
        with open(csv_fullpath, 'a') as f:
            songs_df.to_csv(f, header=False)


def extract_song_features_in_chunks(songs, spotify):
    '''
    Calls spotify API to retrieve song audio features either individually or in
    batches up to 100 tracks at a time
    :param songs: either individual trackid or batch (up to 100)
    :param spotify: spotify client object
    :return: dictionary of features for track/tracks
    '''

    features = spotify.audio_features(songs)
    return features


def read_csv_in_chunks(path, spotify):
    '''
    For a given input csv, fetches song features in batches of 100 tracks at a
    time, then writes to csv by batch to handle memory pressure
    :param path: full filepath of csv location
    :param spotify: spotify client object
    '''
    # Reading by chunk
    # https://stackoverflow.com/questions/42900757/sequentially-read-huge-csv-file-in-python
    chunksize = 100
    rows = 2262300
    num_chunks = int(rows / chunksize)
    starting_now = False

    for chunk_index, chunk in enumerate(pd.read_csv(path, chunksize=chunksize)):
        print(f"""Extracting features for chunk {chunk_index + 1} / {num_chunks}""")
        try:
            features = extract_song_features_in_chunks(list(chunk["trackid"]),
                                                       spotify)
            for feature in features:
                if len(feature) < 10:
                    print("STOP")
        except:
            spotify = initialize_spotify_connection()
            features = extract_song_features_in_chunks(list(chunk["trackid"]),
                                                       spotify)

        for feature_index, (trackid, song_feature) in enumerate(zip(list(chunk["trackid"]), features)):
            if song_feature is None:
                features[feature_index] = {"trackid": trackid}
            else:
                song_feature["trackid"] = trackid

        write_to_csv(features, chunk_index)


def main():
    print(f'''START: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''')

    # Instantiate spotify client
    spotify = initialize_spotify_connection()

    # Read csv in chunks, write to output
    read_csv_in_chunks(my_settings.DATA_PATH / "unique_tracks.csv",
                       spotify)

    print(f'''END: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''')


if __name__ == '__main__':
    main()
