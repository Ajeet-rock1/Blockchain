from string import Template
import yaml, string, os
from tools import logger

TestDir = './dest/'
GAP = 100  #interval for organization port
BASEDIR = os.path.dirname(__file__)

def render(src, dest, **kw):
    t = Template(open(src, 'r').read())
    # may refactor later
    with open(dest, 'w') as f:
        f.write(t.substitute(**kw))

def getTemplate(templateName):
    configTemplate = os.path.join(BASEDIR, "../templates/" + templateName)
    return configTemplate

def locateDeploymentFile(path):
    detial = path.rsplit("crypto-config")
    resourcesPath = detial[0]
    storedPath = resourcesPath + "deployment" + detial[1]
    # create stroedPath while path is not exist.
    if not os.path.exists(storedPath):
        os.makedirs(storedPath)
    return storedPath

def notifyDFgeneration(deploymentYaml, template):
    # Notification of deployment file generation
    deploymentYaml = deploymentYaml.rsplit("deployment/")[-1]
    # Only show the path under deployment/
    template = template.rsplit("templates/")[-1]
    # Only show the path under template/
    raw = "Generating {} from template: {}".format(deploymentYaml, template)
    # should replace by logger in the furture
    logger.info(raw)

# create org/namespace 
def configORGS(name, path, offset, yamlContent):
    # param name: name of org;
    # param  path: describe where is the namespace yaml to be placed.
    namespaceTemplate = getTemplate("fabric_1_0_template_namespace.yaml")
    storedPath = locateDeploymentFile(path)
    deploymentOfNamespace = storedPath + "/" + name + "-namespace.yaml"
    deploymentOfCli = storedPath + "/" + name + "-cli.yaml" 
    deploymentOfCA = storedPath + "/" + name + "-ca.yaml"
    clusterName = yamlContent["clusterName"]
    PORTSTARTFROM = yamlContent["fabricPortStartFrom"]
    nfsIp = yamlContent["nfsServer"]["hostname"]
    nfsExportDir = yamlContent["nfsServer"]["exportDir"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    fabricTag = yamlContent["hyperledgerFabricImage"]["fabricTag"]
    ordererOrgs = yamlContent["crypto-config.yaml"]["OrdererOrgs"]
    for ordererOrg in ordererOrgs:
       if name == ordererOrg["Domain"]:
           ordererOrgName = ordererOrg["Name"] 
           namespace = ordererOrg["Name"].lower() + "-" + clusterName.lower()
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    for peerOrg in peerOrgs:
       if name == peerOrg["Domain"]:
           peerOrgName = peerOrg["Name"]
           namespace = peerOrg["Name"].lower() + "-" + clusterName.lower()
    notifyDFgeneration(deploymentOfNamespace, namespaceTemplate)
    render(namespaceTemplate, deploymentOfNamespace, namespace = namespace,
    pvName = namespace + "-pv",
    pvcName = namespace + "-pvc",
    # resources dir of NFS
    path = path.replace(mountPoint, nfsExportDir),
    nfsIp = nfsIp
    )
	
    if path.find("peer") != -1 :
        ####### pod config yaml for org cli
        cliTemplate = getTemplate("fabric_1_0_template_cli.yaml")
        mspPathTemplate = 'users/Admin@{}/msp'
        tlsPathTemplate = 'users/Admin@{}/tls'

        notifyDFgeneration(deploymentOfCli, cliTemplate)
        render(cliTemplate, deploymentOfCli, name = "cli",
        namespace = namespace,
        mspPath = mspPathTemplate.format(name),
        tlsPath = tlsPathTemplate.format(name),
        pvName = namespace + "-pv",
        pvcName = namespace + "-pvc",
        resourcesName = namespace + "-resources-pv",
        resourcesNamePvc = namespace + "-resources-pvc",
        peerAddress = "peer0." + namespace + ":7051",
        mspid = peerOrgName + "MSP",
        nfsExportDir = nfsExportDir,   
        nfsIp = nfsIp,
        clusterName = clusterName,
        fabricTag = fabricTag
        )
        #######

        ####### pod config yaml for org ca
        ###Need to expose pod's port to worker ! ####
        ##org format like this org1-f-1##
        addressSegment = offset * GAP
        exposedPort = PORTSTARTFROM + addressSegment
        caTemplate = getTemplate("fabric_1_0_template_ca.yaml")
        tlsCertTemplate = '/etc/hyperledger/fabric-ca-server-config/{}-cert.pem'
        tlsKeyTemplate = '/etc/hyperledger/fabric-ca-server-config/{}'
        caPathTemplate = 'ca/'
        cmdTemplate =  ' fabric-ca-server start --ca.certfile /etc/hyperledger/fabric-ca-server-config/{}-cert.pem --ca.keyfile /etc/hyperledger/fabric-ca-server-config/{} -b admin:adminpw -d '

        skFile = ""
        for f in os.listdir(path+"/ca"):  # find out sk!
            if f.endswith("_sk"):
                skFile = f
	
        notifyDFgeneration(deploymentOfCA, cliTemplate)
        render(caTemplate, deploymentOfCA, namespace = namespace,
        command = '"' + cmdTemplate.format("ca."+name, skFile) + '"',
        caPath = caPathTemplate,
        tlsKey = tlsKeyTemplate.format(skFile),	
        tlsCert = tlsCertTemplate.format("ca."+name),
        nodePort = exposedPort,
        pvName = namespace + "-pv",
        pvcName = namespace + "-pvc",
        fabricTag = fabricTag
        )
        #######

# create peer/pod
def configPEERS(name, path, offset, yamlContent): # name means peerid.
    configTemplate = getTemplate("fabric_1_0_template_peer.yaml")
    storedPath = locateDeploymentFile(path)
    deploymentOfPeer = storedPath + "/" + name + ".yaml"

    mspPathTemplate = 'peers/{}/msp'
    tlsPathTemplate = 'peers/{}/tls'
    proPathTemplate = 'peers/{}/production'
    nameSplit = name.split(".", 1)
    peerName = nameSplit[0]
    domainName = nameSplit[1]

    # readConfigFile
    clusterName = yamlContent["clusterName"]
    PORTSTARTFROM = yamlContent["fabricPortStartFrom"]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    for peerOrg in peerOrgs:
       if domainName == peerOrg["Domain"]:
           peerOrgName = peerOrg["Name"]
           namespace = peerOrg["Name"].lower() + "-" + clusterName.lower()

    addressSegment = offset * GAP
    peerOffset = int((peerName.split("peer")[-1])) * 4
    exposedPort1 = PORTSTARTFROM + addressSegment + peerOffset + 1
    exposedPort2 = PORTSTARTFROM + addressSegment + peerOffset + 2
    exposedPort3 = PORTSTARTFROM + addressSegment + peerOffset + 3

    networkMode = yamlContent["networkMode"]
    dockerdSockDir = yamlContent["dockerdSockDir"]
    fabricTag = yamlContent["hyperledgerFabricImage"]["fabricTag"]
    fabricKafkaTag = yamlContent["hyperledgerFabricImage"]["fabricKafkaTag"]
    peerDomain = peerName + "." + namespace   
 
    notifyDFgeneration(deploymentOfPeer, configTemplate)
    render(configTemplate, deploymentOfPeer,
    networkMode = networkMode,
    dockerdSockDir = dockerdSockDir,
    namespace = namespace,
    podName = peerName + "-" + namespace,
    peerID  = peerName,
    corePeerID = peerDomain,
    peerAddress = peerDomain + ":7051",
    peerCCAddress = peerDomain + ":7052",
    peerGossip = peerDomain  + ":7051",
    localMSPID = peerOrgName + "MSP",
    mspPath = mspPathTemplate.format(name),
    tlsPath = tlsPathTemplate.format(name),
    proPath = proPathTemplate.format(name),
    nodePort1 = exposedPort1,
    nodePort2 = exposedPort2,
    nodePort3 = exposedPort3,
    pvcName = namespace + "-pvc",
    fabricTag = fabricTag,
    fabricKafkaTag = fabricKafkaTag
    )

# create orderer/pod
def configORDERERS(name, path, offset, yamlContent): # name means ordererid
    # TODO put these methods to a utils.
    currentDir = os.path.dirname(__file__)

    clusterName = yamlContent["clusterName"]
    PORTSTARTFROM = yamlContent["fabricPortStartFrom"]
    fabricTag = yamlContent["hyperledgerFabricImage"]["fabricTag"]
    fabricKafkaTag = yamlContent["hyperledgerFabricImage"]["fabricKafkaTag"]
    consensusType = yamlContent["consensusType"]
    if consensusType == "kafka":
        ordererTemplate = "fabric_1_0_template_orderer_kafka.yaml" 
    elif consensusType == "solo":
        ordererTemplate = "fabric_1_0_template_orderer.yaml"
    else:
        ordererTemplate = "fabric_1_0_template_orderer.yaml"
        logger.warning("WARNING: Unknown orderer type %s. Use solo instead.",ordererYaml["Type"])

    configTemplate = getTemplate(ordererTemplate)
    storedPath = locateDeploymentFile(path)
    deploymentOfOrderer = storedPath + "/" + name + ".yaml"

    mspPathTemplate = 'orderers/{}/msp'
    tlsPathTemplate = 'orderers/{}/tls'
    proPathTemplate = 'orderers/{}/production'

    nameSplit = name.split(".", 1)
    ordererName = nameSplit[0]
    domainName = nameSplit[1]
    ordererOrgs = yamlContent["crypto-config.yaml"]["OrdererOrgs"]
    for ordererOrg in ordererOrgs:
       if domainName == ordererOrg["Domain"]:
           namespace = ordererOrg["Name"].lower() + "-" + clusterName.lower()

    ordererOffset = offset
    exposedPort = PORTSTARTFROM + 2000 + ordererOffset

    notifyDFgeneration(deploymentOfOrderer, configTemplate)
    render(configTemplate, deploymentOfOrderer,
    namespace = namespace,
    ordererID = ordererName,
    podName =  ordererName + "-" + namespace,
    localMSPID = "OrdererMSP",
    mspPath= mspPathTemplate.format(name),
    tlsPath= tlsPathTemplate.format(name),
    proPath = proPathTemplate.format(name),
    nodePort = exposedPort,
    pvcName = namespace + "-pvc",
    fabricTag = fabricTag,
    fabricKafkaTag = fabricKafkaTag
    )

def generateYaml(member, memberPath, flag, offset, yamlContent):
    if flag == "/peers":
        configPEERS(member, memberPath, offset, yamlContent)
    else:
        configORDERERS(member, memberPath, offset, yamlContent) 

