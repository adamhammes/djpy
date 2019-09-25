import dataclasses
import glob
import json
import os
from pathlib import Path

from saved_track import SavedTrack


def add_metadata(song_path, track_list: [SavedTrack]):
    import eyed3

    _, extension = os.path.splitext(song_path)
    song_path = song_path.replace(extension, ".mp3")

    youtube_id = os.path.basename(song_path).split(" ")[0]
    track = [track for track in track_list if youtube_id in track.youtube_link][0]

    audiofile = eyed3.load(song_path)

    audiofile.tag.title = track.name
    audiofile.tag.album = track.album
    audiofile.tag.artist = "\n".join(track.artists)

    audiofile.tag.save()


def download_tracks(track_list: [SavedTrack]):
    import youtube_dl

    out_dir = Path.cwd() / "downloads"
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
        add_metadata(song_path, track_list)
