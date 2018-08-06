import os, sys, yaml, json, logging
from jinja2 import Template, Environment, FileSystemLoader
from kubernetes import client, config
from kubernetes.stream import stream

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format = '[%(asctime)s %(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def readYaml(yamlPath):
    f = open(yamlPath, 'r')
    yamlContent = yaml.load(f)
    f.close()
    return yamlContent

def writeYaml(content, yamlFile):
    f = open(yamlFile, 'w')
    f.write(content)
    f.close()

def loadJson(path):
    jsonFile = open(path, "r")
    Json = json.load(jsonFile)
    jsonFile.close()
    return Json

def dataPath(fileName):
    # To seprate the config files and template files, all
    # inputs(data to render templates) and outputs(rendered templates)
    # must be stored in specific dir.

    #TODO move to transform
    currentDir=os.path.abspath(__file__)
    currentDir = os.path.dirname(currentDir)
    parentDir = os.path.join(currentDir, "../")
    return os.path.join(parentDir, fileName)

def jinjaEnv(templates_path):
    env = Environment(
        loader=FileSystemLoader(templates_path),
        trim_blocks=True,
        lstrip_blocks=True
    )
    return env

def execCmdInPod(pod_name, namespace, command):
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api() 
        bash_command = ['/bin/bash','-c']
        bash_command.append(command)
        resp = stream(v1.connect_get_namespaced_pod_exec,
                      pod_name, namespace, command=bash_command,
                      stderr=True, stdin=True, stdout=True,
                      tty=False)
        return resp
    except client.rest.ApiException as e:
        logger.error(e)

