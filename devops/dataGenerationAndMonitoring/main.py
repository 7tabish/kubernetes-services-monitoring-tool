from devops.dataGenerationAndMonitoring import app
#from docker.dataGenerationAndMonitoring.Iterations import  iterator
import os


def run(docker,kubernetes,servicesPort):
    defaultDockerFilePath=docker.defaultDockerFilePath
    dockerDeploymentPath=docker.deploymentPath
    dockerImage=docker.dockerImage
    configDataPath=kubernetes.configDataPath
    yamlFilePath=kubernetes.yamlDeployments
    helmDeploymentPath=kubernetes.helmDeployments
    app.data_monitor(defaultDockerFilePath,dockerImage,dockerDeploymentPath,configDataPath,yamlFilePath,servicesPort,helmDeploymentPath)
