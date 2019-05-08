youtube-dl --cookies $1 $2 --flat-playlist -j | jq -r '.id' | sed 's_^_https://youtu.be/_'
