#!/bin/zsh
# File:    autoMake.zsh 
# Date:    13.10.2014 22:01
# Author:  Marek Nožka, marek <@t> tlapicka <d.t> net
# Licence: GNU/GPL 
# Task:    Automatic lunch sass procesing when file change.
############################################################
setopt extendedglob # **/*.txt
setopt re_match_pcre 

interface="webface/"

# načtu XID okna jako parametr z příkazové řádky
if [ $1 ] && [ $1 != 'x' ]; then 
    if [[ $1 =~ '^[\da-fA-F]+$' ]]; then
        winID="0x$1"
    elif [[ $1 =~ '^0x[\da-fA-F]+$' ]]; then
        winID="$1"
    else 
        echo "Toto nevypadá jako window XID" >/dev/stderr
        exit 1
    fi
else
    winID=$(xwininfo | egrep -i 'window id:' | awk '{print $4}')
    echo $winID
fi


radek=0
while true; do
    radek=$[ $radek + 1 ]
    notify=$(inotifywait -r -e modify . --exclude '^\..+\.swp$|^\..+\.log$|\.idea|\.sqlite')
    echo $notify
    if echo $notify | grep styles.scss ; then
        echo "-->" scss --compass styles.scss $interface/static/styles.css
        scss --compass styles.scss $interface/static/styles.css
        echo
    fi

    if [[ $notify =~ 'nejaky vzor' ]]; then
        echo -ne " ~ "
    fi

    sleep 0.1 

    if [ $winID ]; then
        aktivni=$(xdotool getactivewindow)
        xdotool windowactivate --sync $winID
        xdotool key --clearmodifiers ctrl+F5 
        xdotool windowactivate --sync $aktivni
    fi
    printf "%03d: " ${radek}; 
    date
    
done

