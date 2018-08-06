import os, sys, yaml, shutil
from tools import logger, dataPath, jinjaEnv, writeYaml
from fabric import checkFabricServiceIfExist
from components import PeerOrganization, OrdererOrganization

# **** Define json ****
# should be moved to component in the furture

# ==== orderer relative ====
ORDERER = {
    "url": "grpc://orderer{}.{}:7050",
    "server-host": "orderer{}.{}",
}

# ==== peer relative =====
PEERORG = {
    "name": "peer{}",
    "mspid": "{}MSP",
    "ca": "http://ca.{}:7054"
}

ADMIN = {
    "key": "/first-network/crypto-config/peerOrganizations/{0}/users/Admin@{0}/msp/keystore",
    "cert": "/first-network/crypto-config/peerOrganizations/{0}/users/Admin@{0}/msp/signcerts",
#    "tls_cacerts": ""
}
PEER = {
    "requests": "grpc://peer{}.{}:7051",
    "events": "grpc://peer{}.{}:7053",
    "server-hostname": "peer{}.{}",
    "tls_cacerts": "/first-network/crypto-config/peerOrganizations/{1}/peers/peer{0}.{1}/tls/ca.crt"
}
# **** End of define ****

def checkIfClusterExists(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    clusterPath = mountPoint + "/" + clusterName
    lockfile = clusterPath + "/" + "install.lock"
    if not os.path.exists(clusterPath):
        re = os.makedirs(clusterPath)
        if re != None:
            errMsg = "Create dir " + clusterPath + "failed."
            logger.error(errMsg)
            sys.exit(1)
        dstDir = clusterPath + "/" + "resources"
        shutil.copytree("resources", dstDir)
        return False
    else:
        return os.path.exists(lockfile)

def renderCryptoConfigYaml(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    #ordererOrgs
    ordererOrgs = yamlContent["crypto-config.yaml"]["OrdererOrgs"]
    for ordererOrg in ordererOrgs:
        ordererOrg["Type"] = yamlContent["consensusType"]
    #peerOrgs
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    #write to crypto-config.yaml
    cryptoConfigYaml = mountPoint + "/" + clusterName + "/resources/" + "crypto-config.yaml"
    with open(cryptoConfigYaml, "w") as f:
        f.write("clusterName: ")
        f.write(clusterName) 
        f.write("\nOrdererOrgs:\n")
        f.write(yaml.dump(ordererOrgs))
        f.write("PeerOrgs:\n")
        f.write(yaml.dump(peerOrgs))
        f.close()

def renderConfigTxYaml(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    clusterPath = mountPoint + "/" + clusterName

    ordererOrg = yamlContent["crypto-config.yaml"]["OrdererOrgs"][0]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
   
    templatesDir = dataPath("templates")
    env = jinjaEnv(templatesDir)
    template = env.get_template("configtx_template.yaml")
    configTx = clusterPath + "/" + "resources" + "/" + "configtx.yaml"
    
    peerORGS = []
    # peerOrgs
    for peerOrg in peerOrgs:
        namespace = peerOrg["Name"] + "-" + clusterName
        peerOrg["Namespace"] = namespace.lower()
        org = PeerOrganization(peerOrg["Name"], peerOrg["Domain"], peerOrg["Template"]["Count"], peerOrg["Namespace"], clusterName)
        peerORGS.append(org)
    # ordererOrg
    namespace = ordererOrg["Name"] + "-" + clusterName
    ordererOrg["Namespace"] = namespace.lower()
    ordererORG = OrdererOrganization(ordererOrg["Name"], ordererOrg["Domain"],
                                     ordererOrg["Template"]["Count"], ordererOrg["Type"], ordererOrg["Namespace"], clusterName)

    content = template.render(peerOrgs=peerORGS, ordererOrg=ordererORG)
    writeYaml(content, configTx)

#TODO Place the output ingress.yaml to deployment folder.
def renderIngressYaml(yamlContent):
    clusterName = yamlContent["clusterName"]
    ordererOrgs = yamlContent["crypto-config.yaml"]["OrdererOrgs"]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
   
    templatesDir = dataPath("templates")
    env = jinjaEnv(templatesDir)
    template = env.get_template("ingress_template.yaml")
    ingress = os.path.join(os.path.dirname(__file__), "../ingress_{}.yaml_" + clusterName)
   
    peerORGS = [] 
    # peerOrgs
    for peerOrg in peerOrgs:
        namespace = peerOrg["Name"] + "-" + clusterName
        peerOrg["Namespace"] = namespace.lower()
        org = PeerOrganization(peerOrg["Name"], peerOrg["Domain"], peerOrg["Template"]["Count"], peerOrg["Namespace"], clusterName)
        peerORGS.append(org)

    ordererORGS = []
    # ordererOrgs
    for ordererOrg in ordererOrgs:
        namespace = ordererOrg["Name"] + "-" + clusterName
        ordererOrg["Namespace"] = namespace.lower()
        ordererORG = OrdererOrganization(ordererOrg["Name"], ordererOrg["Domain"],
                                         ordererOrg["Template"]["Count"], ordererOrg["Type"], ordererOrg["Namespace"], clusterName)
        ordererORGS.append(ordererORG)

    content = template.render(Orgs=peerORGS, isPeer=True)
    writeYaml(content, ingress.format("peer"))

    content = template.render(Orgs=ordererORGS, isPeer=False)
    writeYaml(content, ingress.format("orderer"))

def generateFabricCerts(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    clusterPath = mountPoint + "/" + clusterName
    resourcesPath = clusterPath + "/resources"
    command = "env CONFIG_PATH=" + resourcesPath + " FABRIC_CFG_PATH=" + resourcesPath + " cryptogen generate \
    --config=" + resourcesPath + "/crypto-config.yaml --output=" + resourcesPath +"/crypto-config"
    re = os.system(command)
    if re != 0:
        logger.error(command + " exec failed.")
        sys.exit(1)

def generateChannelArtifacts(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    channelName = yamlContent["channelName"]
    clusterPath = mountPoint + "/" + clusterName
    resourcesPath = clusterPath + "/resources"
    channelArtifacts = resourcesPath + "/channel-artifacts"
    re = os.makedirs(channelArtifacts, exist_ok=True)
    if re != None:
        errMsg = "Create " + channelArtifacts + " Dir failed."
        logger.error(errMsg)
        sys.exit(1)
    command = "env CONFIG_PATH=" + resourcesPath + " FABRIC_CFG_PATH=" + resourcesPath + " configtxgen \
    -profile OrdererGenesis -outputBlock " + channelArtifacts + "/genesis.block"
    re = os.system(command)
    if re != 0:
        logger.error(command + " exec failed.")
        sys.exit(1)

    #configtxgen -profile DefaultChannel -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID $CHANNEL_NAME
    command = "env CONFIG_PATH=" + resourcesPath + " FABRIC_CFG_PATH=" + resourcesPath + " configtxgen \
    -profile DefaultChannel -outputCreateChannelTx " + channelArtifacts + "/channel.tx -channelID " + channelName
    re = os.system(command)
    if re != 0:
        logger.error(command + " exec failed.")
        sys.exit(1)
    for peerOrg in peerOrgs:
        peerOrgName = peerOrg["Name"]
        command = "env CONFIG_PATH=" + resourcesPath + " FABRIC_CFG_PATH=" + resourcesPath + " configtxgen -profile \
        DefaultChannel -outputAnchorPeersUpdate " + channelArtifacts + "/" + peerOrgName + "MSPanchors.tx -channelID " \
        + channelName + " -asOrg " + peerOrgName + "MSP"
        re = os.system(command)
        if re != 0:
            logger.error(command + " exec failed.")
            sys.exit(1)

def generateFabricClusterConfig(yamlContent):
    renderCryptoConfigYaml(yamlContent)
    renderConfigTxYaml(yamlContent)
    renderIngressYaml(yamlContent)
    generateFabricCerts(yamlContent)
    generateChannelArtifacts(yamlContent)
