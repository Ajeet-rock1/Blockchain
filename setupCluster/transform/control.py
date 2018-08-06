import os, time
from tools import logger


#### orderer
##### namespace(org)
###### single orderer

#### peer
##### namespace(org)
###### ca
####### single peer

def runOrderers(path):
    orgs = os.listdir(path)
    for org in orgs:
        orgPath = os.path.join(path, org)
        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml" ) #orgYaml namespace.yaml
        checkAndRun(namespaceYaml)
        # wait for pv/pvc creation
        time.sleep(20)
        for orderer in os.listdir(orgPath + "/orderers"):
            ordererPath = os.path.join(orgPath + "/orderers", orderer)
            ordererYaml = os.path.join(ordererPath, orderer + ".yaml")
            checkAndRun(ordererYaml)
            time.sleep(10)
    

def deleteOrderers(path):
    orgs = os.listdir(path)
    for org in orgs:
        orgPath = os.path.join(path, org)
        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml" ) #orgYaml namespace.yaml
        for orderer in os.listdir(orgPath + "/orderers"):
            ordererPath = os.path.join(orgPath + "/orderers", orderer)
            ordererYaml = os.path.join(ordererPath, orderer + ".yaml")
            checkAndDelete(ordererYaml)
            time.sleep(10)
        checkAndDelete(namespaceYaml)

def runPeers(path):
    orgs = os.listdir(path)
    for org in orgs:
        orgPath = os.path.join(path, org)

        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml" ) # namespace.yaml
        checkAndRun(namespaceYaml)
        # wait for pv/pvc creation
        time.sleep(20)

        caYaml = os.path.join(orgPath, org + "-ca.yaml" ) # namespace.yaml
        checkAndRun(caYaml)

        cliYaml = os.path.join(orgPath, org + "-cli.yaml" ) # namespace.yaml
        checkAndRun(cliYaml)		

        for peer in os.listdir(orgPath + "/peers"):
            peerPath = os.path.join(orgPath + "/peers", peer)
            peerYaml = os.path.join(peerPath, peer + ".yaml")
            checkAndRun(peerYaml)
            time.sleep(10)

def deletePeers(path):
    orgs = os.listdir(path)
    for org in orgs:
        orgPath = os.path.join(path, org)

        namespaceYaml = os.path.join(orgPath, org + "-namespace.yaml" ) # namespace.yaml
        caYaml = os.path.join(orgPath, org + "-ca.yaml" ) # ca.yaml
        cliYaml = os.path.join(orgPath, org + "-cli.yaml" ) # cli.yaml

        for peer in os.listdir(orgPath + "/peers"):
            peerPath = os.path.join(orgPath + "/peers", peer)
            peerYaml = os.path.join(peerPath, peer + ".yaml")
            checkAndDelete(peerYaml)

        checkAndDelete(cliYaml)
        checkAndDelete(caYaml)

        time.sleep(10)  # keep namespace alive until every resources have been destroyed
        checkAndDelete(namespaceYaml)

def checkAndRun(f):
    if os.path.isfile(f):
        # sleep 5 seconds before deployment creation,
        # in case the PV hasn't initialized completely.
        os.system("kubectl apply -f " + f)
    else:
        logger.error("The file %s does not exist." % (f))

def checkAndDelete(f):
   if os.path.isfile(f):
       os.system("kubectl delete --force --grace-period=0 -f " + f)

