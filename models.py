class Playlist:
    name = ''
    description = ''
    _id = ''
    link = ''

    def __init__(self, name, description, _id, link):
        self.name = name
        self.description = description
        self._id = _id
        self.link = link

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getUri(self):
        return self._id
    
    def getLink(self):
        return self.link

    def __str__(self):
        if len(self.description):
            return f'{self.name} - {self.description}'
        else:
            return self.name

    def __repr__(self):
        return f'Playlist(name={self.name}, description={self.description}, uri={self._id}, link={self.link})'

class Track:
    name = ''
    artists = []
    album = ''
    added_by = ''
    preview_url = ''
    url = ''

    def __init__(self, name, artists, album, added_by, preview_url, url):
        self.name = name
        self.artists = artists
        self.album = album
        self.added_by = added_by
        self.preview_url = preview_url
        self.url = url
