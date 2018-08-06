class PeerOrganization:
   def __init__(self, name, domain, count, namespace, cluster):
       self.name = name
       self.domain = domain
       self.count = count
       self.namespace = namespace
       self.cluster = cluster 

class OrdererOrganization:
   def __init__(self, name, domain, count, orderer_type, namespace, cluster):
   # count represent the number of orderers under same orderer organization
   # orderer_type require solo or kafka, solo by default.
       self.name = name
       self.domain = domain
       self.count = count
       self.type = orderer_type
       self.namespace = namespace
       self.cluster = cluster 
