#!/bin/bash
#
# Name.com DNS update script
#
# 2022 Chris Markiewicz
#
# Released into the public domain
#
# This is a template of a script I run on my router. Mostly intended to prevent having to
# figure it out again when I get a new router.
# The API docs can be found here: https://www.name.com/api-docs

USER=          # name.com login
TOKEN=         # Generate token at https://www.name.com/account/settings/api
DOMAIN=        # Domain name managed by name.com
HOST=          # Host under $DOMAIN (FQDN=$HOST.$DOMAIN)
RECORD=        # Retrieve all records with `curl -u $USER:$TOKEN $API/domains/$DOMAIN/records`
               # Find the object matching "host" and use the "id" field
DEV=pppoe-wan  # Device connecting to ISP, which should have the public IP

API=https://api.name.com/v4

URL=$API/domains/$DOMAIN/records/$RECORD
IP=$( ip address show dev $DEV | awk '/inet / {print $2}' )

curl -u $USER:$TOKEN $URL -X PUT -H 'Content-Type: application/json' \
    --data '{"host": "'$HOST'", "type": "A", "answer": "'$IP'","ttl":300}'
