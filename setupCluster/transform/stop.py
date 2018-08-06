import os, sys
from fabric import stopFabricCluster, stopFabricExplorer
from tools import readYaml

if __name__ == "__main__" :
    configFile=sys.argv[1]
    yamlContent=readYaml(configFile)
    stopFabricExplorer(yamlContent)
    stopFabricCluster(yamlContent)
