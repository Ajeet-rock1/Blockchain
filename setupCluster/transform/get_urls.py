import json
import sys
from fabric import getUrls
from tools import readYaml

if __name__ == "__main__" :
    configFile=sys.argv[1]
    yamlContent=readYaml(configFile)
    print(json.dumps(getUrls(yamlContent)))
