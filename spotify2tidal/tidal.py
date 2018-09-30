import logging
import requests
import tidalapi


class Tidal:
    def __init__(self, username, password):
        self.tidal_session = self._connect(username, password)

    @property
    def own_playlists(self):
        """All playlists of the current user.
        """
        return self.tidal_session.get_user_playlists(
            self.tidal_session.user.id
        )

    def add_track_to_playlist(self, playlist_id, name, artist):
        """Search tidal for a track and add it to a playlist.

        Keyword arguments:
        playlist_id: Playlist to add track to
        name: Name of the track
        artist: Artist of the track
        """
        track_id = self._search_track(name, artist)

        if track_id:
            tidal_add_track_url = (
                "https://listen.tidal.com/v1/playlists/"
                + str(playlist_id)
                + "/items"
            )
            r = requests.post(
                tidal_add_track_url,
                headers={
                    "x-tidal-sessionid": self.tidal_session.session_id,
                    "if-none-match": "*",
                },
                data={"trackIds": track_id, "toIndex": 1},
            )
            r.raise_for_status()
            logging.getLogger(__name__).info("Added: %s - %s", artist, name)

        else:
            logging.getLogger(__name__).warning(
                "Could not find track: %s - %s", artist, name
            )

    def delete_existing_playlist(self, playlist_name):
        """Delete any existing playlist with a given name.

        Keyword arguments:
        playlist_name: Playlist name to delete
        """
        for playlist in self.own_playlists:
            if playlist.name == playlist_name:
                self._delete_playlist(playlist.id)

    def _create_playlist(self, playlist_name, delete_existing=False):
        """Create a tidal playlist and return its ID.

        Keyword arguments:
        playlist_name: Name of the playlist to create
        delete_existing: Delete any existing playlist with the same name
        """
        if delete_existing is True:
            self.delete_existing_playlist(playlist_name)

        tidal_create_playlist_url = (
            "https://listen.tidal.com/v1/users/"
            + str(self.tidal_session.user.id)
            + "/playlists"
        )

        r = requests.post(
            tidal_create_playlist_url,
            data={"title": playlist_name, "description": ""},
            headers={"x-tidal-sessionid": self.tidal_session.session_id},
        )
        r.raise_for_status()

        logging.getLogger(__name__).debug(
            "Created playlist: %s", playlist_name
        )

        return r.json()["uuid"]

    def _connect(self, username, password):
        """Connect to tidal and return a session object.

        Keyword arguments:
        username: Tidal username
        password: Tidal password
        """
        tidal_session = tidalapi.Session()
        tidal_session.login(username, password)
        return tidal_session

    def _delete_playlist(self, playlist_id):
        """Delete a playlist.

        Keyword arguments:
        playlist_id: Playlist ID to delete
        """
        playlist_url = "https://listen.tidal.com/v1/playlists/" + playlist_id

        r = requests.delete(
            playlist_url,
            headers={"x-tidal-sessionid": self.tidal_session.session_id},
        )
        r.raise_for_status()

    def _search_track(self, name, artist):
        """Search tidal and return the track ID.

        Keyword arguments:
        name: Name of the track
        artist: Artist of the track
        """
        tracks = self.tidal_session.search(field="track", value=name).tracks

        for t in tracks:
            if t.artist.name.lower() == artist.lower():
                return t.id
