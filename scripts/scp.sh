#!/usr/bin/env bash
set -e;
{ # try
    # sshpass -p "$password" scp -rqC $dir_origin $username@$Ip:$dir_destination
    scp -rC $1 breath4sale:$2 &&
    echo '{"success": true, "message": "Success."}';

} || { # catch
    echo '{"success": false, "message": "Failed to scp"}';
}