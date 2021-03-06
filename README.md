###----------How to Deploy Hyperledger Fabric on Kubernetes----------###

Let’s assume there is an instance of Kubernetes ready for running Fabric. There are a few scripts we use for the following steps. Download them here:

https://github.com/Ajeet-rock1/Blockchain.git
The downloaded scripts in Blockchain/ folder are as follows:

Configuration files of Fabric:-

We need to edit two configuration files in the Blockchain/ folder to define the Fabric cluster to be deployed:

A. cluster-config.yaml

The cryptogen tool generates certificates for Fabric members based on cluster-config.yaml. An example is as follows:

OrdererOrgs:
 - Name: Orderer
Domain: orgorderer1
     Template:
       Count: 1
  
 PeerOrgs:
 - Name: Org1
     Domain: org1
     Template:­
       Count: 2­­
  
 - Name: Org2
     Domain: org2
     Template:
       Count: 2

Two keywords OrdererOrgs and PeerOrgs specify the type of organization:

1) OrdererOrgs defines an organization with the name Orderer and the domain name orgorderer1. The value of Count under Template is 1. It means only one orderer is under the organization. Its id is orderer0.

2) PeerOrgs defines two organizations: Org1 and Org2. The corresponding domain names are org1 and org2, respectively. As specified by the value of Count, each organization has two peers, namely peer0 and peer1. Peer0 of org1 and peer0 of org2 have the same ID, but they could be distinguished easily by domain name, e.g. peer0.org1 and peer0.org2.

Note: Since the namespace of Kubernetes does not support ‘.’ and uppercase letters, the domain names of each organization should follow the same rule.

For more information on how to customize cluster-config.yaml, please refer to the source code of cryptogen (fabric/common/tools/cryptogen/main.go) .

From the file cluster-config.yaml, cryptogen will generate crypto-config/ directory as follows:
crypto-config
|--- ordererOrganizations
|     |--- orgorderer1
|           |--- msp
|           |--- ca
|           |--- tlsca
|           |--- users
|           |--- orderers
|           |--- orderer0.orgorderer1
|                 |--- msp
|                 |--- tls
|
|--- peerOrganizations
      |--- org1
      |     |--- msp
      |     |--- ca
      |     |--- tlsca
      |     |--- users
      |     |--- peers
      |           |--- peer0.org1
      |           |     |--- msp
      |           |     |--- tls
      |           |--- peer1.org1
      |                 |--- msp
      |                 |--- tls
      |--- org2
            |--- msp
            |--- ca
            |--- tlsca
            |--- users
            |--- peers
                   |--- peer0.org2
                   |     |--- msp
                   |     |--- tls
                   |--- peer1.org2
                         |--- msp
                         |--- tls
B. configtx.yaml

The tool configtxgen will generate genesis block according to configtx.yaml. The genesis block is used to boot up orderer and restrict permission of channel creation. We need to modify configtx.yaml to generate the appropriate genesis block according to the definition of organizations in cluster-config.yaml.

For example, if we add an Org3 to cluster-config.yaml and prepare to create a channel that contains Org1, Org2, Org3, we should modify configtx.yaml by the following two steps:









