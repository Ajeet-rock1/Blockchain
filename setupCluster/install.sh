#!/bin/bash
set -e

#import utils.sh
. $PWD/transform/utils.sh

#check Prerequisites
function checkPrerequisites(){
    export PATH=/usr/local/bin:$PATH
    #check Python3 
    if ! which python3 >/dev/null ; then
        echo "Python 3 is required. Please install Python3 and try again."
        exit 1
    fi
    #check python3-jinja2
    if ! pip3 show Jinja2 >/dev/null ; then
       echo "Jinja2 is required. Please install Jinja2 and try again."
       exit 1
    fi
    #check python3-yaml
    if ! pip3 show PyYAML >/dev/null ; then
       echo "PyYaml is required. Please install PyYaml and try again."
       exit 1
    fi
}

#install hyperledger facric
function installFabricCluster() {
  python3 transform/install.py $BOK_CONFIG
}

###########start install##########
checkPrerequisites
parseOpts $@

BOK_CONFIG=${BOK_CONFIG:-config/bok.yaml}

if [ -n "$SHOW_URLS" ]; then
  # Assume the cluster is already created. Show the URLs of K8s and Fabric.
  python3 transform/get_urls.py $BOK_CONFIG
else
  installFabricCluster
fi
