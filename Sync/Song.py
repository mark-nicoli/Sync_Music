import string, re
sigTimeDifference = 10000 # ms

# words that are found in songs titles to differentiate versions of the same song
DIFFERENT_VERSION_KEY_WORDS = ["version", "live", "studio", "rerecorded",
                                "edit", "radio", "mix", "extended", "acoustic",
                                "edition", "remix"]

SAME_VERSION_KEY_WORDS = ["remaster", "remastered", "mono", "stereo"]

def lazy_property(fn):
    '''Decorator that makes a property lazy-evaluated.
        so it be fast
    '''
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property

""" return a lower case string with punctuation removed.

    """
def simple_string(s):
    return s.lower().translate({string.punctuation: None})

""" remove keywords with excess information form the song name.

    """
def get_simplified_song_name(name, keywords):
    song_name = name

    # seach for word as a whole, not just if it appears in the string
        # i.e. edit will not match if song title contains credits
    words_in_song_name = re.split(" |\(|\)|\[|\]", song_name)
    for word in keywords:

        if word in words_in_song_name:
            pattern = ' - .*' + word + '.*$' # ex. "song - 2011 Remaster, song - single version"
            song_name = re.sub(pattern, '', song_name)

            pattern = ' \[.*' + word + '.*\]' # ex. [2001 Remaster]
            song_name = re.sub(pattern, '', song_name)
            pattern = ' \(.*' + word + '.*\)' # ex. (2001 Remaster)
            song_name = re.sub(pattern, '', song_name)

    return song_name

def take_artists_from_song_name(name, artist_set):
    song_name = name
    feat_index = song_name.index(" (feat. ")

    start_artist_index = feat_index + 8
    end_artist_index = song_name.rfind(')')

    featured_artists = song_name[start_artist_index:end_artist_index]

    featured_artists_list = re.split(" & | and |, ", featured_artists)
    featured_artists_set = set(list(map(simple_string, featured_artists_list)))
    artist_set |= featured_artists_set

    # remove the features from the title since they're not always there
    song_name = song_name[:feat_index]
    return song_name, artist_set

    """
    Create a Song Object in a useful format using the raw track information
    returned by the Spotify API.

    """

def create_song_obj_from_track_dict(sp, track, local=False):
    return Song(sp, track["uri"], track["name"], track["artists"][0]["name"], map(lambda x: x["name"], track["artists"][1:]),
            track["album"]["name"], track["duration_ms"], local)

class Song(object):
    def __init__(self, sp, uri, name, artist, features, album, duration, local=False):
        self.sp = sp
        self.uri = uri
        self.name = name
        self.artist = artist
        self.featured_artists = features
        self.album = album
        self.duration = duration
        self.local = local

        self.artist_set = set(list(map(simple_string, [artist])))
        self.set_identifier_and_match_name()

        # save some attributes in a dictionary for access with [] notation
        self.attributes = { "name": self.name, "uri": self.uri, "artist":
              self.artist, "album": self.album, "duration": self.duration,
              "featured_artists": self.featured_artists, "local": self.local,
              "identifier": self.identifier
        }

    ''' Set the strings that are used for song matching.

        '''
    def set_identifier_and_match_name(self):
        song_name = self.name.lower()

        if " (feat. " in song_name:
            song_name, artist_set = take_artists_from_song_name(song_name,
                                                              self.artist_set)
            # if the features were not already recorded as artists for the track
            if len(list(self.featured_artists)) == 0:
                self.artist_set |= set(artist_set)

        # remove details about the song that are considered to not significantly
        # make the song a different version
        song_name = get_simplified_song_name(song_name, SAME_VERSION_KEY_WORDS)
        self.match_name = simple_string(song_name)

        # remove any version specific details from the song title
        song_name = get_simplified_song_name(song_name, DIFFERENT_VERSION_KEY_WORDS)

        # include all artists in identifier in case they are listed in a different order
        identifier = simple_string(song_name) + " - " + \
                     " - ".join(self.artist_set)
        self.identifier = identifier


    @lazy_property
    def audio_features(self):
        # Get Audio features info
        return self.sp.audio_features([self.uri])

    def __eq__(self, other):
        if isinstance(other, Song):
            if self.uri == other.uri:
                return True

            elif self.match_name == other.match_name and \
                self.artist_set == other.artist_set and \
                (abs(self.duration - other.duration) < sigTimeDifference):

                return True

            return False
        return False
    # not equal to go with equality definition
    def __ne__(self, other):
        return (not self.__eq__(other))

    # allows accessing fields of the song with [] notation
    def __getitem__(self, key):
        return self.attributes[key]

    # formats the output when printing the song as a string
    def __str__(self):
        name = self.name.encode('utf-8').strip()
        artist = self.artist.encode('utf-8').strip()
        album = self.album.encode('utf-8').strip()
        uri = self.uri.encode('utf-8').strip()
        return (
            "-" * 50 + "\n"
            "Title: %s \n" \
            "Artist: %s \n" \
            "Album: %s\n" \
            "Uri: %s \n"  % (name, artist, album, uri) +
            "-" * 50 + "\n"
            )
        return
