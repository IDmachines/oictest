#!/bin/bash

startme() {
    oprp.py adfs &
    oprp.py azure_ad &
    oprp.py google &
    oprp.py ping &
    oprp.py salesforce &
    oprp.py telekom &
    oprp.py thinktecture_code &
}

stopme() {
    pkill -f "adfs"
    pkill -f "azure_ad"
    pkill -f "google"
    pkill -f "ping"
    pkill -f "salesforce"
    pkill -f "telekom"
    pkill -f "thinktecture_code"
}

case "$1" in
    start)   startme ;;
    stop)    stopme ;;
    restart) stopme; startme ;;
    *) echo "usage: $0 start|stop|restart" >&2
       exit 1
       ;;
esac