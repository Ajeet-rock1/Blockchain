import os, sys, yaml, copy, json
from tools import logger, jinjaEnv, dataPath, readYaml, loadJson

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

# explorer relative
def handlerPeerNetwork(peerOrg, clusterName):
    # return dict which will be dumped to json later. 
    name = peerOrg["Name"]
    domain = peerOrg["Domain"]
    count = peerOrg["Template"]["Count"]
    namespace = peerOrg["Name"] + "-" + clusterName
    namespace = namespace.lower()

    # ----- peer org instance ------
    org = copy.copy(PEERORG)
    org["name"] = org["name"].format(domain)
    org["mspid"] = org["mspid"].format(name)
    org["ca"] = org["ca"].format(namespace)

    # ----- peer instances -----
    for j in range(count):
        peer = copy.copy(PEER)
        peer["requests"] = peer["requests"].format(j, namespace)
        peer["events"] = peer["events"].format(j, namespace)
        peer["server-hostname"] = peer["server-hostname"].format(j, namespace)
        peer["tls_cacerts"] = peer["tls_cacerts"].format(j, domain)
        org.update({"peer" + str(j): peer})
 
    # ----- admin instance ----
    admin = copy.copy(ADMIN)
    admin["key"] = admin["key"].format(domain)
    admin["cert"] = admin["cert"].format(domain)
    org.update({"admin": admin})

    return org

def handlerOrdererNetwork(ordererOrg, clusterName):
    # again, we are using ordererOrg rather than ordererOrgs,
    # bacause only one ordererOrg is supporeted so far.

    # ----------------- orderer organization ---------
    orderersList = []

    for i in range(ordererOrg["Template"]["Count"]):
       #name = ordererOrg["Name"]
       name = "orderer"
       domain = ordererOrg["Domain"]
       namespace= name + "-" + clusterName 
       namespace= namespace.lower()
       # ---------- orderer org instance -------
       orderer = copy.copy(ORDERER)
       orderer["url"] = orderer["url"].format(i, namespace)
       orderer["server-host"] = orderer["server-host"].format(i, namespace)
       orderersList.append(orderer)

    return orderersList 
 
def renderNetwork(Yaml, output, template):
    # The template file is a normal json file, not a jinja template.
    ordererOrg = Yaml['OrdererOrgs'][0]
    peerOrgs = Yaml['PeerOrgs']
    clusterName = Yaml['clusterName']
    config = template
    network = {}
   
    # handle peers
    _count = 1
    for peerOrg in peerOrgs:
        org = handlerPeerNetwork(peerOrg, clusterName)
        #nickName = peerOrg["Name"]
        nickName = "org" + str(_count)
        _count += 1

        network.update({nickName: org})
        config["org"].append(nickName)

    # update template
    config.update({"network-config": network})

    # write to file config.json
    content = json.dumps(config, indent=4, sort_keys=True)
    networkConfig = open(output, 'w')
    networkConfig.write(content)
    networkConfig.close()

def renderFabricExplorer(yamlContent):
    clusterName = yamlContent["clusterName"]
    PORTSTARTFROM = yamlContent["fabricPortStartFrom"]
    nfsExportDir = yamlContent["nfsServer"]["exportDir"]
    nfsIp = yamlContent["nfsServer"]["hostname"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"] 
    templatesDir = dataPath("templates")
    env = jinjaEnv(templatesDir)
    template = env.get_template("fabric_1_0_explorer.yaml")
    hostNodePort = PORTSTARTFROM + 2067
    content = template.render(clusterName = clusterName,
                              nfsExportDir = nfsExportDir,
                              nfsIp = nfsIp,
                              hostNodePort = hostNodePort
                              )
    explorerYaml = mountPoint + "/"+ clusterName +"/resources/explorer-artifacts/fabric_1_0_explorer.yaml"  
    with open(explorerYaml, "w") as f:
        f.write(content)
        f.close()
    
    #render config.json
    channelName = yamlContent["channelName"]
    cryptoConfig = mountPoint + "/"+ clusterName + "/resources/crypto-config.yaml"
    cryptoYaml = readYaml(cryptoConfig)
    networkConfig = mountPoint + "/"+ clusterName + "/resources/explorer-artifacts/config.json"
    networkTemplatePath = dataPath("resources/explorer-artifacts/config.json")
    networkTemplate = loadJson(networkTemplatePath)
    networkTemplate["channel"] = channelName
    renderNetwork(cryptoYaml, networkConfig, networkTemplate)
