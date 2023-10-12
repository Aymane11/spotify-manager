from typing import List, Optional
from pydantic import BaseModel
from cherrypicker import CherryPicker

TRACK_FIELDS = {
    "name": "track.name",
    "artists": "track.artists",
    "album": "track.album.name",
    "added_by": "added_by.id",
    "preview_url": "track.preview_url",
    "link": "track.external_urls.spotify",
}

PLAYLIST_FIELDS = {
    "owner": "owner.id",
    "name": "name",
    "description": "description",
    "id": "id",
    "link": "external_urls.spotify",
}


class User(BaseModel):
    id: Optional[str]
    name: Optional[str]
    link: Optional[str]

    def __str__(self):
        return str(self.name)

    def from_dict(self, data: dict):
        self.id = data.get("id")
        self.name = data.get("name")
        self.link = data.get("link")
        return self

    def __eq__(self, other):
        return self.id == other.id


class Track(BaseModel):
    name: Optional[str]
    artists: Optional[List[str]]
    album: Optional[str]
    added_by: Optional[User]
    preview_url: Optional[str]
    link: Optional[str]

    def from_dict(self, data: dict):
        picker = CherryPicker(data)
        track = picker.flatten(delim=".").get()
        self.name = track[TRACK_FIELDS["name"]]
        self.album = track[TRACK_FIELDS["album"]]
        self.preview_url = track[TRACK_FIELDS["preview_url"]]
        self.link = track[TRACK_FIELDS["link"]]
        self.added_by = User().from_dict({"id": track[TRACK_FIELDS["added_by"]]})
        self.artists = [
            v
            for k, v in track.items()
            if k.startswith(TRACK_FIELDS["artists"]) and k.endswith("name")
        ]
        return self


class Playlist(BaseModel):
    owner: Optional[User]
    name: Optional[str]
    description: Optional[str]
    id: Optional[str]
    link: Optional[str]
    tracks: Optional[List[Track]]

    def from_dict(self, data: dict):
        picker = CherryPicker(data)
        playlist = picker.flatten(delim=".").get()
        self.owner = User().from_dict({"id": playlist[PLAYLIST_FIELDS["owner"]]})
        self.name = playlist[PLAYLIST_FIELDS["name"]]
        self.description = playlist[PLAYLIST_FIELDS["description"]]
        self.id = playlist[PLAYLIST_FIELDS["id"]]
        self.link = playlist[PLAYLIST_FIELDS["link"]]
        return self

    def add_tracks(self, tracks: List[Track]):
        if self.tracks:
            self.tracks.append(tracks)
        else:
            self.tracks = tracks

    def __str__(self):
        return (
            f'{self.name} - {(self.description[:40] + "..") if len(self.description) > 75 else self.description}'
            if len(self.description)
            else str(self.name)
        )

    def __iter__(self):
        yield from self.tracks

    def __getitem__(self, index):
        return self.tracks[index]

    def __len__(self):
        return len(self.tracks)
