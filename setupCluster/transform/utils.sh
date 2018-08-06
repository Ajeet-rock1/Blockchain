#!/bin/bash
# this is a function definition script.

#parseOpts
function parseOpts() {
    while getopts "c:ah" arg
    do
      case $arg in
        c)
          BOK_CONFIG=$OPTARG
          ;;
        a)
          SHOW_URLS=1
          ;;
        h)
          echo -e "Usage:\n    bash $0 [-c /path/to/bok.yaml] [-a]"
          exit 0
      exit 1
      ;;
      esac
    done
}

