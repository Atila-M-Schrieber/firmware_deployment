#!/bin/bash

usage() {
    echo "Usage: $0 (--board-id|-b) <board id> (--firmware|-f) <firmware name>\
		(--version|-v) <version x.x.x> (--gpg-user|-u) <gpg user/key id>\
		(--url|-U) <firmware server url>"
    exit 1
}

# Parsing:
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --board-id|-b) BOARD_ID="$2";;
        --firmware|-f) FIRMWARE="$2";;
        --version|-v) VERSION="$2";;
        --gpg-user|-u) USER="$2";;
        --url|-U) URL="$2";;
        *) echo "Bad argument: $1"; usage;;
    esac
    shift; shift
done

# Check args
if [[ -z "$BOARD_ID" || -z "$FIRMWARE" || -z "$VERSION" || -z "$USER" || -z "$URL" ]]; then
    echo "Missing required parameters."
    usage
fi

# Generate string to sign
STRING_TO_SIGN="$FIRMWARE-$VERSION-$BOARD_ID"

# Sign the string
echo -n "$STRING_TO_SIGN" | gpg -u "$USER" --output sig.pgp --detach-sig
if [[ $? -ne 0 ]]; then
    echo "Something went wrong with gpg!"
    exit 1
fi

# Send the update order
curl -X POST "$URL/update/$BOARD_ID" -F "firmware=$FIRMWARE" -F "version=$VERSION"\
	-F "sig.asc=@sig.pgp"

if [[ $? -ne 0 ]]; then
    echo "Ordering update failed :["
    rm sig.pgp
    exit 1
fi

echo
echo "Update order sent successfully"

rm sig.pgp
