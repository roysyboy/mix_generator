import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import urllib3

'''
scope = "playlist-read-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
'''

client_id = 'be603e31796549aea534a00d42658e1d'
client_secret = '02f6a628e90f41a0a444dfd238242ae4'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def print_playlists(playlists) -> None:
    for i, playlist in enumerate(playlists['items']):
        print('{}:'.format(i))
        print("    " + playlist['name'])
        print("    " + playlist['uri'])


def get_song_features(usr) -> tuple:
    # Get user id

    # Get a list of all playlists from usr
    playlists = sp.user_playlists(usr)

    # Get a single playlist
    cur_playlist_uris = playlists['items'][0]['uri']
    cur_playlist_raw = sp.playlist(cur_playlist_uris)

    cur_pl = cur_playlist_raw['tracks']['items']
    cur_pl_sz = len(cur_pl)

    song_uri_lst = [cur_pl[i]['track']['uri'] for i in range(cur_pl_sz)]
    song_name_lst = [cur_pl[i]['track']['name'] for i in range(cur_pl_sz)]

    # get features for each songs
    features = sp.audio_features(song_uri_lst)

    return features, song_name_lst


def main() -> None:
    usr = '217w3eazrgl6jhi6cofvyf7wi'
    features, names = get_song_features(usr)
    for i, feature in enumerate(features):
        print("{}: ".format(i))
        print("  {}".format(names[i]))
        print("  {}".format(feature))


def test() -> None:
    usr = '217w3eazrgl6jhi6cofvyf7wi'

    # Get a list of all playlists from usr
    playlists = sp.user_playlists(usr)

    # Get a single playlist
    cur_pl_uri = playlists['items'][0]['uri']
    cur_pl_name = playlists['items'][0]['name']

    cur_playlist = sp.playlist(cur_pl_uri)
    cur_song = cur_item = cur_playlist['tracks']['items'][0]['track']
    cur_song_artist = cur_song['artists'][0]['name']


if __name__ == "__main__":
    main()