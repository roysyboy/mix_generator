import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import urllib3

# global variables
global sp, token
sp = None
token = None


# return a single string of each artist in artists separated by comma
def get_artists(artists) -> str:
    sz = len(artists)
    if sz < 1:
        return None
    result = artists[0]['name']
    for i in range(1, sz):
        result += ", " + artists[i]['name']

    return result


# print out each track from given spotify playlist
def print_playlists(playlists) -> None:
    for i, playlist in enumerate(playlists['items']):
        print('{}: {}'.format(i + 1, playlist['name']))
        # print("    " + playlist['name'])
        # print("    " + playlist['uri'])


# get a list of all playlist of user profile
def get_playlist(usr, client_id, client_secret):
    global sp
    sp = auth_spotify(usr, client_id, client_secret)
    if sp is None:
        return None
    
    playlists = sp.user_playlists(usr)
    print_playlists(playlists)

    return playlists


# authenticate spotify's web api
def auth_spotify(usr, client_id, client_secret) -> spotipy.Spotify:
    global sp, token
    # client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    # sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    scope = 'playlist-modify-public'
    token = spotipy.util.prompt_for_user_token(usr, scope, client_id, client_secret, redirect_uri='http://localhost')
    sp = spotipy.Spotify(auth=token)
    return sp


# get features for each song in a playlist
def get_song_features(usr, playlists, playlist_no, client_id, client_secret) -> tuple:
    global sp
    # sp = auth_spotify(usr, client_id, client_secret)
    if sp is None:
        return None

    # Get a list of all playlists from usr
    playlist_no -= 1

    # Get a single playlist
    cur_playlist_uris = playlists['items'][playlist_no]['uri']
    playlist_name = playlists['items'][playlist_no]['name']
    cur_playlist_raw = sp.playlist(cur_playlist_uris)

    cur_pl = cur_playlist_raw['tracks']['items']
    cur_pl_sz = len(cur_pl)

    song_uri_lst = [cur_pl[i]['track']['uri'] for i in range(cur_pl_sz)]
    song_name_lst = [(cur_pl[i]['track']['name'], get_artists(cur_pl[i]['track']['artists'])) for i in range(cur_pl_sz)]

    # get features for each songs
    features = sp.audio_features(song_uri_lst)

    return features, song_name_lst, playlist_name


# convert given list of uri's into a spotify playlist with given playlist name
def uri_to_playlist(uri_list, usr, playlist_name) -> None:
    global sp
    if sp is not None:
        playlist_name += " - roy's mix"
        new_playlist = sp.user_playlist_create(usr, playlist_name)
        sp.playlist_add_items(new_playlist['id'], uri_list)
    else:
        print("sp failure")


##### main #####
def main() -> None:
    usr = input('Enter Spotify user id: ')
    client_id = input('Enter client id: ')
    client_secret = input('Enter client secret passcode: ')
    
    playlists = get_playlist(usr, client_id, client_secret)
    playlist_no = input('Enter the playlist number: ')
    features, names = get_song_features(usr, playlists, client_id, client_secret)
    for i, feature in enumerate(features):
        print("{}: ".format(i))
        print("  {}".format(names[i]))
        print("  {}".format(feature))


if __name__ == "__main__":
    main()