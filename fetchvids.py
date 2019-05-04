import subprocess


def get_vid_list():
    command = "youtube-dl --cookies cookie_secret.txt " \
              "'https://www.youtube.com/watch?v=Q9WcG0OMElo&list=RDGMEMhCgTQvcskbGUxqI4Sn2QYw&start_radio=1' " \
              "--flat-playlist -j | jq -r '.id' | sed 's_^_https://youtu.be/_' "

