import string
import config as tc
from explorer import renderFabricExplorer 
import os

def generateNamespacePod(DIR, yamlContent):
# GenerateNamespacePod generate the yaml file to create the namespace for k8s, and return a set of paths which indicate the location of org files 
    orgs = []
    for org in os.listdir(DIR):
        orgDIR = os.path.join(DIR, org)
        ## generate namespace first.
        orgs.append(orgDIR)
        offset = orgs.index(orgDIR)
        tc.configORGS(org, orgDIR, offset, yamlContent)
    return orgs

def generateDeploymentPod(orgs, yamlContent):
    for org in orgs:
        if org.find("peer") != -1: #whether it create orderer pod or peer pod 
            suffix = "/peers"
        else:
            suffix = "/orderers"
        members = os.listdir(org + suffix)
        offset = orgs.index(org)
        for member in members:
            memberDIR = os.path.join(org + suffix, member)
            tc.generateYaml(member,memberDIR, suffix, offset, yamlContent)

def generateFabricExplorer(yamlContent):
    renderFabricExplorer(yamlContent)
    
def createInstallLock(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    clusterPath = mountPoint + "/" + clusterName
    lockfile = clusterPath + "/" + "install.lock"
    f = open(lockfile, 'w')
    f.write(clusterName)
    f.close()

# TODO kafa nodes and zookeeper nodes don't have dir to store their certificate, must use anotherway to create pod yaml.

def generateDeploymentYaml(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    clusterPath = mountPoint + "/" + clusterName
    resourcesPath = clusterPath + "/resources"
    cryptoConfigPath = resourcesPath + "/crypto-config"
    ordererPath = cryptoConfigPath + "/ordererOrganizations"
    peerPath = cryptoConfigPath + "/peerOrganizations"
    
    peerOrgs = generateNamespacePod(peerPath, yamlContent)
    generateDeploymentPod(peerOrgs, yamlContent)
    ordererOrgs = generateNamespacePod(ordererPath, yamlContent)
    generateDeploymentPod(ordererOrgs, yamlContent)
   
    generateFabricExplorer(yamlContent)
