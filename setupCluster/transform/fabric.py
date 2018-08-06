import yaml, sys, os, time, shutil
from control import runOrderers, runPeers, deleteOrderers, deletePeers, \
     checkAndRun, checkAndDelete
from kubernetes import client, config 
from kubernetes.stream import stream
from tools import readYaml, logger, dataPath, execCmdInPod

TIMEOUT=1200
INTERVAL=5

def relocateFileForFabric(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    ordererDomainName = yamlContent["crypto-config.yaml"]["OrdererOrgs"][0]["Domain"]
    clusterPath = mountPoint + "/" + clusterName
    resourcesPath = clusterPath + "/resources"
    channelArtifacts = resourcesPath + "/channel-artifacts"
    #copy genesis.block to crypto-config
    srcfile = channelArtifacts + "/genesis.block"
    dstfile = resourcesPath + "/crypto-config/ordererOrganizations/" + ordererDomainName + "/genesis.block"
    shutil.copyfile(srcfile, dstfile)
    #copy configtx.yaml to channel-artifacts
    srcfile =  resourcesPath + "/configtx.yaml"
    dstfile =  channelArtifacts + "/configtx.yaml"
    shutil.copyfile(srcfile, dstfile)
    os.remove(srcfile)
    #move ingress.yaml into deployment
    srcfile = os.path.join(os.path.dirname(__file__), "../ingress_peer.yaml_" + clusterName)
    dstfile = resourcesPath + "/deployment/ingress_peer.yaml"
    shutil.copyfile(srcfile, dstfile)
    os.remove(srcfile)
    srcfile = os.path.join(os.path.dirname(__file__), "../ingress_orderer.yaml_" + clusterName)
    dstfile = resourcesPath + "/deployment/ingress_orderer.yaml"
    shutil.copyfile(srcfile, dstfile)
    os.remove(srcfile)
    #delete crypto-config.yaml
    deleteFile = resourcesPath + "/crypto-config.yaml"
    os.remove(deleteFile)
    time.sleep(5)

def startFabricCluster(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    location = mountPoint + "/" + clusterName + "/resources/deployment"
    ordererOrgPath = location + "/ordererOrganizations"
    runOrderers(ordererOrgPath)
    peerOrgPath = location + "/peerOrganizations"
    runPeers(peerOrgPath)
    # Create ingress
    checkAndRun(location + "/ingress_peer.yaml")
    checkAndRun(location + "/ingress_orderer.yaml")

def stopFabricCluster(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    location = mountPoint + "/" + clusterName + "/resources/deployment"
    ordererOrgPath = location + "/ordererOrganizations"
    deleteOrderers(ordererOrgPath)
    peerOrgPath = location + "/peerOrganizations"
    deletePeers(peerOrgPath)
    # Delete ingress
    checkAndDelete(location + "/ingress_peer.yaml")
    checkAndDelete(location + "/ingress_orderer.yaml")

def checkFabricServiceStatus(yamlContent):
    logger.info("Waiting for BoK to start up ...")
    clusterName = yamlContent["clusterName"]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    ifReady=0
    timeCount=0
    config.load_kube_config()
    v1 = client.CoreV1Api()
    while True:
        ret = v1.list_pod_for_all_namespaces(watch=False)
        for peerOrg in peerOrgs:
            peerOrgName=peerOrg["Name"]
            namespace=peerOrgName.lower() + "-" + clusterName.lower()
            for i in ret.items:
                if namespace == i.metadata.namespace:
                    if i.status.phase != "Running":
                        ifReady=0
                        break
                    else:
                        ifReady=1
            if ifReady == 0:
                break
        if ifReady == 1:
            logger.info("BoK is up and running.")
            break
        else:
            timeCount = timeCount + INTERVAL
            time.sleep(INTERVAL)
       
        if timeCount > TIMEOUT:
            logger.error("Error: Failed to start BoK service.")
            sys.exit(1)

def checkFabricServiceIfExist(yamlContent):
    clusterName = yamlContent["clusterName"]
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for peerOrg in peerOrgs:
        peerOrgName=peerOrg["Name"]
        namespace=peerOrgName.lower() + "-" + clusterName.lower()
        for i in ret.items:
            if namespace == i.metadata.namespace:
                if i.status.phase != "Running":
                    logger.info("The cluster " + clusterName + " is being deployed, please wait for running.")
                else:
                    logger.info("The cluster " + clusterName + " is aleady running.")
                sys.exit(0)
        logger.info("The cluster " + clusterName + " was already created, please run start.sh to start the cluster.")
        sys.exit(0)  
           
def checkConsensusServiceStatus(yamlContent):
    logger.info("Checking consensus service status.")            
    clusterName = yamlContent["clusterName"]
    ordererOrgName=yamlContent["crypto-config.yaml"]["OrdererOrgs"][0]["Name"]
    ORDERMSPID="OrdererMSP"
    ordererDomain = yamlContent["crypto-config.yaml"]["OrdererOrgs"][0]["Domain"]
    MSPCONFIGPATH = "/etc/hyperledger/ordererOrganizations/" + ordererDomain + "/orderers/orderer0." + ordererDomain + "/msp"
    ordererNamespace=ordererOrgName.lower() + "-" + clusterName.lower()
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    checkCommand="env CORE_PEER_LOCALMSPID=" + ORDERMSPID + " " + "CORE_PEER_MSPCONFIGPATH=" + MSPCONFIGPATH + " " + \
        "peer channel fetch 0 -o " + "orderer0." + ordererNamespace + ":7050 -c testchainid"
    re = 0
    timeCount = 0
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    while True:
        for peerOrg in peerOrgs:
            peerOrgName=peerOrg["Name"]
            namespace=peerOrgName.lower() + "-" + clusterName.lower()
            for i in ret.items:
                if (i.metadata.namespace == namespace and i.metadata.name.startswith("cli")):
                    cliPodName = i.metadata.name
                    resp = execCmdInPod(cliPodName, namespace, checkCommand)
                    logger.debug(resp)
                    re = resp.find("Error")
        if re == -1:
            break
        else:
            timeCount = timeCount + INTERVAL
            time.sleep(INTERVAL)
        if timeCount > TIMEOUT:
           errMsg="Error: Consensus service is not healthy"
           logger.error(errMsg)
           sys.exit(1)
    logger.info("Consensus service is OK.")            

def joinChannelAndUpdate(yamlContent):
    clusterName = yamlContent["clusterName"]
    ordererOrgName = yamlContent["crypto-config.yaml"]["OrdererOrgs"][0]["Name"]
    channelName = yamlContent["channelName"]
    logger.info("Joining " + channelName + " and updating.")            
    ordererNamespace=ordererOrgName.lower() + "-" + clusterName.lower()
    OrdererUrl = "orderer0." + ordererNamespace + ":7050"
    peerOrgs = yamlContent["crypto-config.yaml"]["PeerOrgs"]
    createChannel = "peer channel create -c " + channelName +  " -o " + OrdererUrl + \
                    " " + "-t 15 -f resources/channel-artifacts/channel.tx"
    copyBlock = "cp ./" + channelName + ".block ./resources/channel-artifacts -rf"
    channelCreateFlag = 0
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    re = 0
    for peerOrg in peerOrgs:
        peerOrgName=peerOrg["Name"]
        peersNum=peerOrg["Template"]["Count"]
        namespace=peerOrgName.lower() + "-" + clusterName.lower()
        ret = v1.list_namespaced_pod(namespace, watch=False)
        for i in ret.items:
            if i.metadata.name.startswith("cli"):
                cliPodName = i.metadata.name
        if channelCreateFlag == 0:
            resp = execCmdInPod(cliPodName, namespace, createChannel)
            logger.debug(resp)
            re = resp.find("Error")
            if re != -1:
                logger.error("Failed to create channel " + channelName + ".")
                sys.exit(1)
            resp = execCmdInPod(cliPodName, namespace, copyBlock)
            re = resp.find("cannot")
            if re != -1:
                logger.error("Failed to config channel " + channelName + ".")
                sys.exit(1)
            for n in range(peersNum):
                peerUrl = "peer" + str(n) + "." + namespace + ":7051"
                joinChannel="env CORE_PEER_ADDRESS=" + peerUrl + " peer channel join -b resources/channel-artifacts/" + channelName + ".block"
                resp = execCmdInPod(cliPodName, namespace, joinChannel)
                logger.debug(resp)
                re = resp.find("Error")
                if re != -1:
                    errMsg = "peer" + str(n) + " fail to join channel " + channelName + " on " + namespace
                    logger.error(errMsg)
                    sys.exit(1)
            updateChannel="peer channel update -o " + OrdererUrl + " -c " + channelName + " -f resources/channel-artifacts/" + peerOrgName + "MSPanchors.tx"
            resp = execCmdInPod(cliPodName, namespace, updateChannel)
            logger.debug(resp)
            re = resp.find("Error")
            if re != -1:
                errMsg = "Fail to update channel " + channelName + " on " + namespace
                logger.error(errMsg)
                sys.exit(1)
            channelCreateFlag = 1
        else:
            for n in range(peersNum):
                peerUrl = "peer" + str(n) + "." + namespace + ":7051"
                joinChannel="env CORE_PEER_ADDRESS=" + peerUrl + " " + "peer channel join -b resources/channel-artifacts/" + channelName + ".block"
                resp = execCmdInPod(cliPodName, namespace, joinChannel)
                logger.debug(resp)
                re = resp.find("Error")
                if re != -1:
                    errMsg = "peer" + str(n) + " fail to join " + channelName + " on " + namespace
                    logger.error(errMsg)
                    sys.exit(1)
            updateChannel="peer channel update -o " + OrdererUrl + " -c " + channelName + " -f resources/channel-artifacts/" + peerOrgName + "MSPanchors.tx"
            resp = execCmdInPod(cliPodName, namespace, updateChannel)
            logger.debug(resp)
            re = resp.find("Error")
            if re != -1:
                errMsg = "Failed to update channel " + channelName + " on " + namespace
                logger.error(errMsg)
                sys.exit(1)
    logger.info("Joining " + channelName + " and updating is over.")            

def startFabricExplorer(yamlContent):
    logger.info("Start to run fabric explorer.")
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    namespace = "explorer-" + clusterName
    timeCount = 0
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if(i.metadata.namespace == namespace and i.metadata.name.startswith("fabric-explorer")):
            explorerRunFlag = 1
            logger.info("Fabric explorer is already installed")
            return
        else:
            explorerRunFlag = 0

    if explorerRunFlag == 0:
       explorerYaml = mountPoint + "/" + clusterName + "/resources/explorer-artifacts/fabric_1_0_explorer.yaml"
       command = "kubectl apply -f " + explorerYaml
       re=os.system(command)
       if re != 0:
          logger.info("Command execution failed: " + command)

    time.sleep(INTERVAL)

    while True:
       ret = v1.list_namespaced_pod(namespace, watch=False)
       for i in ret.items:
           logger.info("Fabric explorer pod status: " + i.status.phase)
           if i.status.phase != "Running":
               ifReady = 0
           else:
               ifReady = 1

       if ifReady == 0:
           timeCount = timeCount + INTERVAL
           time.sleep(INTERVAL)
       else:
           logger.info("Fabric explorer is ready.")
           return

def stopFabricExplorer(yamlContent):
    clusterName = yamlContent["clusterName"]
    mountPoint = yamlContent["nfsServer"]["mountPoint"]
    explorerYaml = mountPoint + "/" + clusterName + "/resources/explorer-artifacts/fabric_1_0_explorer.yaml"
    command = "kubectl delete  --grace-period=0 --force -f " + explorerYaml
    re=os.system(command)
    if re != 0:
        logger.info(command + " exec failed")

def showAddress(yamlContent):
    urls = getUrls(yamlContent)

    dashboard ="You can view Kubernetes dashboard at: " + urls["k8sDashboardUrl"]
    logger.info(dashboard)

    if urls["fabricExplorerUrl"]:
        explorerMsg = "You can view Fabric Explorer at: " + urls["fabricExplorerUrl"]
    else:
        explorerMsg = "Can not get Ingress Controller IP. Please check your Ingress controller settings."
    logger.info(explorerMsg)

def getUrls(yamlContent):
    k8sDashboardUrl = ""
    fabricExplorerUrl = ""

    clusterName = yamlContent["clusterName"].lower()
    kubeNamespace="kube-system"
    explorerNamespace="explorer-" + clusterName
    config.load_kube_config()
    v1 = client.CoreV1Api()
    v1beta = client.ExtensionsV1beta1Api()
    
    # Get Kubernetes Dashboard Url
    ret = v1.list_namespaced_pod(kubeNamespace, watch=False)
    for i in ret.items:
        if i.metadata.name.startswith("kubernetes-dashboard"):
            dashboardIp = i.status.host_ip
    ret = v1.list_namespaced_service(kubeNamespace, watch=False)
    for i in ret.items:
        if i.metadata.name.startswith("kubernetes-dashboard"): 
            dashboardNodePort = i.spec.ports[0].node_port
    k8sDashboardUrl = "https://" + dashboardIp + ":" + str(dashboardNodePort)


    # Get Fabric Explorer Url
    ingressHostname = None
    ingressPort = 80
    ingressSslPort = 443
    ret = v1beta.list_namespaced_ingress(explorerNamespace, watch=False)
    for i in ret.items:
        if i.metadata.name == "explorer-ingress":
            hosts = i.status.load_balancer.ingress
            if hosts is not None and len(hosts) != 0:
               ingressHostname = hosts[0].ip
               break
    if not ingressHostname:
        # The 'Address' column in 'kubectl get ing -n $explorerNamespace' is empty.
        # Get the Node IP for ingress-nginx pod which is the ingress controller IP.
        # This applies to PKS 1.1.0.
        ret = v1.list_namespaced_pod("ingress-nginx")
        for i in ret.items:
            if i.metadata.name.startswith("nginx-ingress-controller"):
                ingressHostname = i.status.host_ip
                break;
        ret = v1.list_namespaced_service("ingress-nginx")
        for i in ret.items:
            if i.metadata.name.startswith("ingress-nginx"):
                for port in i.spec.ports:
                    if port.name == "http":
                        ingressPort = port.node_port
                    elif port.name == "https":
                        ingressSslPort = port.node_port
                break;

    if ingressHostname:
        if ingressSslPort != 443:
            ingressHostname += ":" + str(ingressSslPort)
        fabricExplorerUrl = "https://" + ingressHostname + "/fabric/" + clusterName + "/explorer"

    return {"k8sDashboardUrl": k8sDashboardUrl, "fabricExplorerUrl": fabricExplorerUrl}
