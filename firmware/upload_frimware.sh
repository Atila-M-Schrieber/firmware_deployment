#!/bin/bash

usage() {
	echo "Usage: $0 [ (--firmware|-f) <firmware name> (--version|-v) <version x.x.x> ||\
		(--directory|-d) <firmware directory> ] (--gpg-user|-u) <gpg user/key id>\
		(--url|-U) <firmware server url>" 
	exit 1
}

# Parsing:
while [[ "$#" -gt 0 ]]; do # as long as there are args left..
	case $1 in # done with a sick vim macro
		--firmware|-f) FIRMWARE="$2";;
		--version|-v) VERSION="$2";;
		--directory|-d) DIRECTORY="$2";;
		--gpg-user|-u) USER="$2";;
		--url|-U) URL="$2";;
		*) echo "Bad argument: $1"; usage;;
	esac
	shift; shift
done

# check arguments
if [[ -z "$USER" || -z "URL" ]]; then
	echo "Missing required parameters."
	usage
fi

# if firmware & version given, construct directory
if [[ -n "$FIRMWARE" && -n "$VERSION" ]]; then
    DIRECTORY="${FIRMWARE}-${VERSION}"
elif [[ -z "$DIRECTORY" ]]; then
	echo "Either give firmware name + version, or the directory. Firmware name + version take priority."
	usage
elif [[ -z "$FIRMWARE" || -z "$VERSION" ]]; then # construct name & version from dir
	FIRMWARE=$(echo "$DIRECTORY" | sed -E 's/-[0-9.]+$//')
    VERSION=$(echo "$DIRECTORY" | sed -E 's/^[^-]+-//')
fi

if [[ ! -d "$DIRECTORY" ]]; then
    echo "Firmware directory '$DIRECTORY' does not exist!"
    exit 1
fi

# Sign the firmware files
cat "$DIRECTORY"/* | gpg -u "$USER" --output sig.pgp --detach-sig
if [[ $? -ne 0 ]]; then
    echo "Something went wrong with gpg!"
    exit 1
fi

# Send the files
curl -X PUT "$URL/upload" -F "firmware=$FIRMWARE" -F "version=$VERSION"\
	$(for file in "$DIRECTORY"/*; do echo "-F file=@$file"; done | tr '\n' ' ')\
	-F "file=@sig.pgp"

echo

if [[ $? -ne 0 ]]; then
    echo "Uploading failed :["
	rm sig.pgp
    exit 1
fi

rm sig.pgp

echo "Uploaded successfully"
