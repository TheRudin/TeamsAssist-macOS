#!/bin/bash

# Script to easily generate a Home Assistant Long-Lived Access Token via CLI
# Author: Hassassistant (macOS Edition)

# Resolve directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "================================================================================"
echo "          Home Assistant Long-Lived Access Token Generator (macOS CLI)"
echo "================================================================================"

# Prompt user for HA URL if not provided
read -p "Enter your Home Assistant URL [http://homeassistant.local:8123]: " HA_URL
if [ -z "$HA_URL" ]; then
    HA_URL="http://homeassistant.local:8123"
fi

# Prompt for username
read -p "Enter your Home Assistant Username: " USERNAME
if [ -z "$USERNAME" ]; then
    echo "Error: Username cannot be empty."
    exit 1
fi

# Prompt for password (masked input)
unset PASSWORD
charcount=0
prompt="Enter your Home Assistant Password: "
while IFS= read -p "$prompt" -r -s -n 1 char; do
    if [[ $char == $'\0' ]]; then
        break
    fi
    if [[ $char == $'\177' ]]; then
        if [ $charcount -gt 0 ]; then
            charcount=$((charcount-1))
            prompt=$'\b \b'
            PASSWORD="${PASSWORD%?}"
        else
            prompt=""
        fi
    else
        charcount=$((charcount+1))
        prompt="*"
        PASSWORD+="$char"
    fi
done
echo "" # print new line after password submission

if [ -z "$PASSWORD" ]; then
    echo "Error: Password cannot be empty."
    exit 1
fi

echo "Connecting to $HA_URL..."
python3 "$DIR/create_token.py" "$HA_URL" "$USERNAME" "$PASSWORD"
