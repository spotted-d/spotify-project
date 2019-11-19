import my_settings
import datetime
import requests
import pandas as pd
from difflib import SequenceMatcher
from bs4 import BeautifulSoup


def get_lastfm(method, data=None):
    '''
    Generic function that builds request string and makes a LastFM api request
    :param method: specifies which LastFM api method to call
    :param data: data to send to api
    :return response: JSON-formatted api response
    '''

    request_string = (f'''http://ws.audioscrobbler.com/2.0/?method={method}'''
                      f'''&api_key={my_settings.LASTFM_TOKEN}''')

    if data is not None:
        request_string += data

    request_string += "&format=json"
    response = requests.get(request_string).json()

    return response


def get_genius(api_path, data, token):
    '''
    Generic function that makes a Genius api request based on a specified path
    :param api_path: path designating the type of api request
    :param data: data to feed to the request
    :param token: authorization token
    :return response: json response from api
    '''

    headers = {'Authorization': f'''Bearer {token}'''}
    response = requests.get(api_path, params=data, headers=headers).json()

    return response


def get_top_tags_list():
    '''
    Fetches top 50 tags from LastFM, by song count
    :return top_tags: list of top tags
    '''

    response = get_lastfm(method='tag.gettoptags')
    top_tags = []

    for tag in response['toptags']['tag']:
        top_tags.append(tag['name'].replace(' ', ''))

    return top_tags


def get_top_tracks_by_tag(tag, top_tracks, top_n=None):
    '''
    Fetches top 100 pages of tracks for a given tag (genre)
    :param tag: tag (genre) to fetch tracks for
    :param top_tracks: tracks list
    :return top_tracks: tracks list with appended tracks
    '''

    # Fetch the first 100 pages for each genre
    # for page in range(1, 100):
    for page in range(1, 2):   #two pages for now for testing purposes
        data = f'''&tag={tag}&page={page}'''
        response = get_lastfm(method='tag.gettoptracks', data=data)

        if top_n is None:
            for song in response['tracks']['track']:
                print(f'''Adding: {song['artist']['name']} - {song['name']}''')
                top_tracks.append(
                    {'artist_name': song['artist']['name'],
                     'song_title': song['name'],
                     'genre': tag})
        else:
            for song in response['tracks']['track'][:top_n]:
                print(f'''Adding: {song['artist']['name']} - {song['name']}''')
                top_tracks.append(
                    {'artist_name': song['artist']['name'],
                     'song_title': song['name'],
                     'genre': tag})

    return top_tracks


def get_artist_id(artist_name):
    '''
    Retrieves artist_id for a given artist_name
    :param artist_name: name of artist to retrieve
    :param base_url: api_path to call
    :return artist_id: id for specified artist
    '''

    data = {'q': artist_name}
    response = get_genius(f'''{my_settings.GENIUS_BASEURL}/search''',
                          data,
                          my_settings.GENIUS_TOKEN)

    if len(response['response']['hits']) == 0:
        print(f'''Artist name {artist_name} not found...''')
        exit(0)

    for hit in response['response']['hits']:
        if hit['result']['primary_artist']['name'].lower() == artist_name:
            artist_id = hit['result']['primary_artist']['id']
            break

    return artist_id


def get_song_lyrics(songs):
    '''
    Given a list of songs, append lyrics to each song dict
    :param songs: song list
    :return songs: song list with appended lyrics
    '''

    for song in songs:
        print(f'''Retrieving lyrics for: {song['artist_name']}'''
              f''' - {song['song_title']}''')
        page = requests.get(song['song_url'])
        html = BeautifulSoup(page.text, 'html.parser')
        song['lyrics'] = html.find('div', class_='lyrics').get_text()

    return songs


def find_genius_songs(songs):
    '''
    Builds song dictionary for each song in list fetched from LastFM. Adds
    attributes from Genius such as song_id, artist_id and song_url. Uses
    SequenceMatcher library to determine whether Genius match is "close enough"
    to LastFM song
    :param songs: song list
    :return final_songs: final list of songs with genius data
    '''

    for song in songs:
        print(f'''Fetching Genius data for: {song['artist_name']} '''
              f'''- {song['song_title']}''')
        data = {'q': f'''{song['song_title']} {song['artist_name']}'''}
        response = get_genius(
            f'''{my_settings.GENIUS_BASEURL}/search?''',
            data,
            my_settings.GENIUS_TOKEN)

        for hit in response['response']['hits']:
            artist_genius = hit['result']['primary_artist']['name']
            artist_lastfm = song['artist_name']
            song_genius = hit['result']['title']
            song_lastfm = song['song_title']

            # SequenceMatchter logic to handle "close enough" song matches
            if (SequenceMatcher(a=artist_genius, b=artist_lastfm).ratio() > 0.8
                    and SequenceMatcher(a=song_genius, b=song_lastfm).ratio() > 0.8):
                song['artist_id'] = hit['result']['primary_artist']['id']
                song['song_id'] = hit['result']['id']
                song['song_url'] = hit['result']['url']
                break

        # Only include songs with lyrics url in final result set
        final_songs = []
        for song in songs:
            if 'song_url' in song.keys():
                final_songs.append(song)

    return final_songs


def write_to_csv(songs):
    '''
    Converts song list to a dataframe and writes it to a csv
    :param songs: song list
    '''

    songs_df = pd.DataFrame(songs)
    songs_df.to_csv(my_settings.OUTPUT_PATH / 'test.csv')


def main():
    print(f'''START: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''')
    top_tags = get_top_tags_list()

    top_tracks = []
    for tag in top_tags:
        top_tracks = get_top_tracks_by_tag(tag, top_tracks)

    top_tracks = find_genius_songs(songs=top_tracks)
    top_tracks = get_song_lyrics(songs=top_tracks)
    write_to_csv(top_tracks)
    print(f'''END: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}''')


if __name__ == '__main__':
    main()
