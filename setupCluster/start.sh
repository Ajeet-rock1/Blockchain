#/bin/bash
set -e

#import utils.sh
. $PWD/transform/utils.sh

function startFabricCluster(){
    BOK_CONFIG=${BOK_CONFIG:-config/bok.yaml}
    python3 transform/start.py ${BOK_CONFIG}
}

#######start#########
parseOpts $@
startFabricCluster
