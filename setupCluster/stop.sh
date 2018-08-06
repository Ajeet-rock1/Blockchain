#/bin/bash
set -e

#import utils.sh
. $PWD/transform/utils.sh

function stopFabricCluster(){
    BOK_CONFIG=${BOK_CONFIG:-config/bok.yaml}
    python3 transform/stop.py ${BOK_CONFIG}
}

#######start#########
parseOpts $@
stopFabricCluster
