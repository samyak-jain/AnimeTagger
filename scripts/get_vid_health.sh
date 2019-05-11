curl \
  'https://www.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics&id='$1'&key='$2 \
  --header 'Accept: application/json' \
  --compressed -s
