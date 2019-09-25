import dataclasses
import glob
import json
import sys
import os
from pathlib import Path

from saved_track import SavedTrack


def add_metadata(song_path, track_list: [SavedTrack]):
    import eyed3

    _, extension = os.path.splitext(song_path)
    song_path = song_path.replace(extension, ".mp3")

    youtube_id = os.path.basename(song_path).split(" ")[0]
    corresponding_tracks = [
        track for track in track_list if youtube_id in track.youtube_link
    ]
    if not corresponding_tracks:
        return

    track = corresponding_tracks[0]

    audiofile = eyed3.load(song_path)

    audiofile.tag.title = track.name
    audiofile.tag.album = track.album
    audiofile.tag.artist = "\n".join(track.artists)

    audiofile.tag.save()


def unseen_tracks(download_dir, track_list: [SavedTrack]) -> [SavedTrack]:
    unseen = []

    mp3_search_pattern = str(download_dir) + "/*.mp3"
    mp3_paths = glob.glob(mp3_search_pattern)
    filenames = [os.path.basename(path) for path in mp3_paths]

    for track in track_list:
        has_short_url = "youtu.be/" in track.youtube_link
        if not has_short_url:
            unseen.append(track)
            continue

        youtube_id = track.youtube_link.split("/")[-1]
        is_existing_id = any(youtube_id in filename for filename in filenames)

        if not is_existing_id:
            unseen.append(track)

    return unseen


def download_tracks(track_list: [SavedTrack], skip_seen=True):
    import youtube_dl

    all_tracks = track_list

    out_dir = Path.cwd() / "downloads"
    if skip_seen:
        track_list = unseen_tracks(out_dir, track_list)
    if track_list:
        plural = "s" if len(track_list) != 1 else ""
        print(f"{len(track_list)} unseen track{plural}")
    else:
        print("No unseen tracks")
        sys.exit(0)

    output_template = f"{out_dir}/%(id)s %(title)s.%(ext)s"

    ydl_opts = {
        "download_archive": out_dir / "archive.txt",
        "format": "bestaudio/best",
        "nocheckcertificate": True,
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    urls = [track.youtube_link for track in track_list]
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

    for song_path in glob.glob("downloads/*.mp3"):
        add_metadata(song_path, all_tracks)
