import logging
import spotipy
import spotipy.util as util


class Spotify:
    def __init__(
        self,
        username,
        client_id,
        client_secret,
        client_redirect_uri,
        discover_weekly_id=None,
    ):
        self.username = username
        self._client_id = client_id
        self._client_secret = client_secret
        self._client_redirect_uri = client_redirect_uri
        self._discover_weekly_id = discover_weekly_id

        self.spotify_session = self._connect()

    @property
    def own_playlists(self):
        """All playlists of the user.

        This does not include things like 'Discover Weekly', since these are
        technically owned by Spotify, not the user.
        """
        try:
            result = self.spotify_session.current_user_playlists()
            playlists = result["items"]

            while result["next"]:
                result = self.spotify_sesion.next(result)
                playlists.extend(result["items"])
        except spotipy.client.SpotifyException:
            self._refresh_expired_token()
            return self.own_playlists

        return playlists

    @property
    def discover_weekly_playlist(self):
        """Playlist object of the 'Discover Weekly" playlist.

        Since the discover weekly is special in the sense that it isn't actually
        owned by the user, its ID has to be manually provided beforehand.
        """
        if not self._discover_weekly_id:
            raise ValueError("No discover weekly ID set")

        try:
            return self.spotify_session.user_playlist(
                self.username, self._discover_weekly_id
            )
        except spotipy.client.SpotifyException:
            self._refresh_expired_token()
            return self.discover_weekly_playlist()

    def tracks_from_playlist(self, playlist):
        """Return a list with all tracks from a given playlist.

        Keyword arguments:
        playlist: spotipy playlist to get tracks from
        """
        try:
            result = self.spotify_session.user_playlist(
                user=playlist["owner"]["id"],
                playlist_id=playlist["id"],
                fields="tracks,next",
            )["tracks"]

            tracks = result["items"]

            while result["next"]:
                result = self.spotify_session.next(result)
                tracks.extend(result["items"])
        except spotipy.client.SpotifyException:
            self._refresh_expired_token()
            return self.tracks_from_playlist(playlist)

        return tracks

    def _connect(self):
        """Connect to Spotify and return a session object.

        Use spotify's Authorization Code Flow.
        This requires a registered client at spotify with a valid client-id,
        client-secret and some redirection-url
        More information on authorization:
        https://developer.spotify.com/documentation/general/guides/authorization-guide/
        https://spotipy.readthedocs.io/en/latest/#authorized-requests
        """
        scope = "user-library-read playlist-read-private playlist-modify-private playlist-modify-public"
        token = util.prompt_for_user_token(
            self.username,
            scope=scope,
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._client_redirect_uri,
        )

        if not token:
            raise ValueError("Could not connect to Spotify")

        return spotipy.Spotify(auth=token)

    def _refresh_expired_token(self):
        """When the token expires after 1h, refresh it.

        When the token expires, spotipy throws spotipy.client.SpotifyException.
        To refresh the expired token, simply reauthenticate. Spotipy refreshes
        the token automatically in case it is expired.
        """
        logging.getLogger(__name__).debug("Refreshing token")
        self.spotify_session = self._connect()
