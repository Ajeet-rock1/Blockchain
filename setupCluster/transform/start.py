import os, sys
from fabric import startFabricCluster, checkFabricServiceStatus, \
checkConsensusServiceStatus, startFabricExplorer, showAddress 
from tools import readYaml

if __name__ == "__main__" :
    configFile=sys.argv[1]
    yamlContent=readYaml(configFile)
    startFabricCluster(yamlContent)
    checkFabricServiceStatus(yamlContent)
    checkConsensusServiceStatus(yamlContent)
    startFabricExplorer(yamlContent)
    showAddress(yamlContent)
