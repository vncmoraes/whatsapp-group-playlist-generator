import time
import spotipy
import regex as re
from spotipy.oauth2 import SpotifyOAuth
import math

# Spotify Authentication
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope='playlist-modify-public user-read-private playlist-modify-private',
        client_id='client_id',
        client_secret='client_secret',
        redirect_uri='https://example.com/'
    )
)

# Existing playlists IDs (separated from years)
playlist_ids = {
    2024: 'playlist_id_1',
    2025: 'playlist_id_2',
}

def get_track_ids_from_file_by_year() -> dict::
    track_ids_by_year = {}

    with open("group_messages.txt", 'r', encoding="utf8") as file:
        for line in file:
            stripped_line = line.strip()
            message_year = int(re.sub('[^0-9]', '', stripped_line[:10][6:]) or 0)

            url_finder_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            line_track_urls = re.findall(url_finder_regex, stripped_line)

            line_track_ids = [
                track_url.split('track/')[1].split('?si')[0].split('?context')[0]
                for track_url in line_track_urls if ('spotify.com/track' in track_url)
            ]

            track_ids_by_year[message_year] = track_ids_by_year.get(message_year, []) + line_track_ids

    # Remove duplicate tracks without altering order
    for year in track_ids_by_year:
        track_ids_by_year[year] = list(dict.fromkeys(track_ids_by_year.get(year)))

    return track_ids_by_year


def get_all_track_ids_from_playlist(playlist_id: str) -> list:
    if not playlist_id:
        return []

    playlist_track_ids = []
    partial_playlist_tracks = sp.playlist_items(playlist_id, additional_types=('track',))

    while partial_playlist_tracks:
        partial_track_ids = [track['track']['id'] for track in partial_playlist_tracks['items']]
        playlist_track_ids.extend(partial_track_ids)

        if partial_playlist_tracks['next']:
            partial_playlist_tracks = sp.next(partial_playlist_tracks)
            print('Buscando músicas...')
            time.sleep(1)

        else:
            partial_playlist_tracks = None

    return playlist_track_ids


def add_tracks_to_playlists(track_ids_by_year: dict):
    current_playlist_track_ids = []

    for year, track_ids in track_ids_by_year.items():
        playlist_id = playlist_ids.get(year, None)

        if not playlist_id:
            continue

        current_playlist_track_ids.extend(get_all_track_ids_from_playlist(playlist_id))
        new_track_ids = [track_id for track_id in track_ids if track_id not in current_playlist_track_ids]
        n_of_iterations = math.ceil((len(new_track_ids) / 100))
        print(f'Encontradas {len(new_track_ids)} novas músicas')

        # Divides total tracks into groups of 100 because of API limit
        for i in range(n_of_iterations):
            range_end = ((i + 1) * 100)
            range_start = (range_end - 100)
            one_hundred_tracks = new_track_ids[range_start:range_end]

            print(f'Adicionando músicas {range_start}-{range_end}')
            sp.playlist_add_items(playlist_id, one_hundred_tracks, position=None)
            time.sleep(1)


if __name__ == '__main__':
    track_ids_dict = get_track_ids_from_file_by_year()
    add_tracks_to_playlists(track_ids_dict)
