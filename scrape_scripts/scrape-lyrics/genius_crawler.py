import requests
import my_settings
import pandas as pd
import argparse
from bs4 import BeautifulSoup


def parse_command_line_input():
    '''
    Establishes valid user arguments and parses them
    :return args: returns arguments object
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument("--artist",
                        nargs='+',
                        help="artist to pull discography for")
    args = parser.parse_args()

    # handle spaces and casing in artist name
    if args.artist is not None:
        args.artist = ' '.join(args.artist).lower()

    return args


def get(api_path, data, token):
    '''
    General function that makes api request based on a specified path
    :param api_path: path designating the type of api request
    :param data: data to feed to the request
    :param token: authorization token
    :return response: json response from api
    '''

    headers = {'Authorization': f'''Bearer {token}'''}
    response = requests.get(api_path, params=data, headers=headers).json()

    return response


def get_artist_id(artist_name, base_url):
    '''
    Retrieves artist_id for a given artist_name
    :param artist_name: name of artist to retrieve
    :param base_url: api_path to call
    :return artist_id: id for specified artist
    '''

    data = {'q': artist_name}
    response = get(f'''{base_url}/search''',
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


def get_artist_discography(artist_id, base_url):
    '''
    Retrieves list of all song_ids in entire artist discography
    :param artist_id:
    :param base_url:
    :return discography: list of all song_ids in artist discography
    '''

    # Logic for paging through all results inspired by:
    # https://www.jw.pe/blog/post/quantifying-sufjan-stevens-with-the-genius-api-and-nltk/
    current_page = 1
    next_page = True
    discography = []

    while next_page:
        data = {'page': current_page,
                'per_page': 50,
                'sort': 'title'}
        response = get(f'''{base_url}/artists/{artist_id}/songs''',
                       data,
                       my_settings.GENIUS_TOKEN)
        page_songs = response['response']['songs']

        if page_songs:
            for song in page_songs:
                discography.append(song['id'])
            print(f'''Retrieved results for page {current_page}''')
            # print(f'''Top song_id: {page_songs[0]['id']}''')
            current_page += 1
        else:
            next_page = False

    return discography


def get_song_data(song_id_list, artist_name, artist_id, base_url):
    '''
    Retrieves song data for a given list of song_ids
    :param song_id_list:
    :param base_url:
    :return all_songs:
    '''

    all_songs = []

    for song_id in song_id_list:
        print(f'''Retreiving song: {song_id}''')
        song_data = {}
        data = {
            'id': song_id,
            'text_format': 'plain'
        }
        response = get(f'''{base_url}/songs/{song_id}''',
                              data,
                              my_settings.GENIUS_TOKEN)
        song_data['artist_id'] = artist_id
        song_data['artist_name'] = artist_name
        song_data['song_id'] = song_id
        song_data['song_title'] = response['response']['song']['title']
        song_data['song_url'] = response['response']['song']['url']
        if response['response']['song']['album']:
            song_data['album_id'] = response['response']['song']['album']['id']
            song_data['album_name'] = response['response']['song']['album'][
                'name']
        else:
            song_data['album_id'] = None
            song_data['album_name'] = None
        all_songs.append(song_data)

    return all_songs


def retrieve_song_lyrics(songs):
    '''
    Given a list of songs, append lyrics to each song dict
    :param songs: song list
    :return songs: song list with appended lyrics
    '''

    for song in songs:
        print(f'''Retrieving lyrics for: {song['song_title']}''')
        url = song['song_url']
        page = requests.get(url)
        html = BeautifulSoup(page.text, 'html.parser')
        song['lyrics'] = html.find('div', class_='lyrics').get_text()

    return songs


def write_to_csv(songs):
    '''
    Converts song list to a dataframe and writes it to a csv
    :param songs: song list
    '''

    songs_df = pd.DataFrame(songs)
    songs_df.to_csv(my_settings.OUTPUT_PATH / 'test.csv')


def main():
    args = parse_command_line_input()

    print(f'''Retrieving results for artist: {args.artist}''')
    genius_base_url = 'https://api.genius.com'
    artist_id = get_artist_id(args.artist, genius_base_url)
    song_id_list = get_artist_discography(artist_id, genius_base_url)
    all_songs = get_song_data(song_id_list, args.artist, artist_id, genius_base_url)

    # retrieve full discography and genre
    all_songs = retrieve_song_lyrics(all_songs)

    # write to csv
    write_to_csv(all_songs)


if __name__ == '__main__':
    main()

