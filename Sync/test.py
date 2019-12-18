#'href': 'https://api.spotify.com/v1/playlists/0vvXsWCC9xrXsKd4FyS8kM',

import re

#.*\/(\w+(?:\.\w+)?)[?\.]?
txt = "https://api.spotify.com/v1/playlists/0vvXsWCC9xrXsKd4FyS8kM"
reg=re.search(".*\/(\w+(?:\.\w+)?)[?\.]?", txt)

list(txt.split('/'))
print(txt)