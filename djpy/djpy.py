import dataclasses
import io
import json
import typing as T
import urllib.request

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from saved_track import SavedTrack
from downloader import download_tracks


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


SHEET_KEY = "1HYYg0COPorG3-3LvJx6MeT38jpyDylppJDJnhB08Ino"
SHEET_NAME = "Songs"
SHEET_URL = "".join(
    [
        "https://docs.google.com/spreadsheets/d/",
        SHEET_KEY,
        "/gviz/tq?tqx=out:csv&sheet=",
        SHEET_NAME,
    ]
)

# Lindy Favorites
# PLAYLIST_URI = "spotify:playlist:637KMeDDmU7MWmCjS567zW"

# All Lindy
PLAYLIST_URI = "spotify:playlist:4hgB4Tk5x5ll6YCy5s1SHR"
USERNAME = "thaunatos"


def get_songs_in_playlist() -> [SavedTrack]:
    client_credentials_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    playlist_id = PLAYLIST_URI.split(":")[-1]

    results = sp.user_playlist(USERNAME, playlist_id)
    raw_tracks = results["tracks"]["items"]
    saved_tracks = []

    for raw_track in raw_tracks:

        track = raw_track["track"]
        artists = list(map(lambda a: a["name"], track["artists"]))

        saved_tracks.append(
            SavedTrack(
                name=track["name"],
                spotify_uri=track["uri"],
                album=track["album"]["name"],
                artists=artists,
                youtube_link=None,
            )
        )

    return saved_tracks


def download_sheet():
    import ssl

    context = ssl._create_unverified_context()
    response = urllib.request.urlopen(SHEET_URL, context=context)
    return response.read().decode("utf-8")


def parse_sheet(raw_sheet) -> [SavedTrack]:
    import csv
    import io

    csvfile = io.StringIO(raw_sheet)
    reader = csv.DictReader(csvfile)
    rows = [row for row in reader]
    saved_tracks = []

    saved_track_fields = set(SavedTrack.__annotations__.keys())

    for row in rows:
        assert set(row.keys()) == saved_track_fields
        row["artists"] = row["artists"].split("\n")
        saved_tracks.append(SavedTrack(**row))

    return saved_tracks


def write_tracks_to_csv(tracks: [SavedTrack]) -> str:
    import csv, io

    dict_tracks = list(map(dataclasses.asdict, tracks))
    for dict_track in dict_tracks:
        dict_track["artists"] = "\n".join(dict_track["artists"])

    csvfile = io.StringIO()
    writer = csv.DictWriter(csvfile, list(dict_tracks[0].keys()))
    writer.writeheader()
    writer.writerows(dict_tracks)

    return csvfile.getvalue()


def merge_tracks(sheet_tracks, playlist_tracks) -> [SavedTrack]:
    seen_uris = set()
    merged_tracks = []

    for track in sheet_tracks + playlist_tracks:
        if not track.spotify_uri in seen_uris:
            seen_uris.add(track.spotify_uri)
            merged_tracks.append(track)

    return merged_tracks


def sync_sheet_playlist_data():
    playlist_tracks = get_songs_in_playlist()
    sheet_tracks = parse_sheet(download_sheet())

    merged = merge_tracks(sheet_tracks, playlist_tracks)

    csv = write_tracks_to_csv(merged)
    print(csv)


def main():
    tracks = parse_sheet(download_sheet())
    downloadable_tracks = [track for track in tracks if track.youtube_link]
    download_tracks(downloadable_tracks)
    # sync_sheet_playlist_data()


if __name__ == "__main__":
    main()
