import sys
from generateCluster import checkIfClusterExists, generateFabricClusterConfig
from generateDeployment import generateDeploymentYaml, createInstallLock
from fabric import relocateFileForFabric, startFabricCluster, checkFabricServiceStatus, \
checkConsensusServiceStatus, joinChannelAndUpdate, startFabricExplorer, showAddress
from tools import readYaml, logger

if __name__ == "__main__" :
    configFile=sys.argv[1]
    yamlContent=readYaml(configFile)
    if not checkIfClusterExists(yamlContent):
        # generate fabric Config
        generateFabricClusterConfig(yamlContent)
        # generate deployment
        generateDeploymentYaml(yamlContent)
        # relocate some file
        relocateFileForFabric(yamlContent)
        # create install.lock
        createInstallLock(yamlContent)

    # start fabric clsuter
    startFabricCluster(yamlContent)
    # check fabic service if run
    checkFabricServiceStatus(yamlContent)
    # check fabric consensus service
    checkConsensusServiceStatus(yamlContent)
    # join defaultchannel
    joinChannelAndUpdate(yamlContent)
    # start fabric explorer
    startFabricExplorer(yamlContent)
    # show kubernetes dashboard and explorer url
    showAddress(yamlContent)
