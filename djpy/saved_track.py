import dataclasses
import typing as T


@dataclasses.dataclass
class SavedTrack:
    name: str
    artists: [str]
    album: str
    youtube_link: T.Optional[str]
    spotify_uri: str
