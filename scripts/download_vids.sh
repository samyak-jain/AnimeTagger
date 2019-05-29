youtube-dl -x --audio-format mp3 --batch-file $1 -o $2 --add-metadata --print-json | jq -r .title
