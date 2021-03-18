from django.db import models
from django.contrib.auth.models import User
import os
from git import Repo
import shutil
import subprocess
import shutil

import tempfile
from django.http import HttpResponse
# Create your models here.
class Github(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url=models.URLField(primary_key=True,blank=False,null=False)
    cloned_directory=models.CharField(max_length=200,blank=False,null=False)
    def cloning(self):
        try:
            print("start clonoing")
            cloned_repo=Repo.clone_from(self.url, self.cloned_directory)
            print("cloning complete")
            cloned_repo.close()
            return True
        except Exception as e:
            print("Error",e)
            return False
    def __str__(self):
        return self.url


class Docker(models.Model):
    github=models.OneToOneField(Github,on_delete=models.CASCADE)
    dockerImage=models.CharField(max_length=200,blank=False,null=False)
    defaultDockerFilePath=models.CharField(max_length=200,blank=False,null=False)
    deploymentPath=models.CharField(max_length=200,blank=False,null=False)

    def create_image(self):
        if self.dockerImage =="":
            print("image is none")
            exit(1)
        else:
            subprocess.call(['docker','build','-t',self.dockerImage,'.'],cwd=self.github.cloned_directory)
    def push_image(self):
        if self.dockerImage =="":
            exit(1)
            print("image is none")
        else:
            subprocess.call(['docker', 'push', self.dockerImage])

    def remove_image(self):
        if self.dockerImage=="":
            print("docker image name is required")
            exit(1)
        subprocess.call(['docker', 'rmi', self.dockerImage])



    def __str__(self):
        return self.dockerImage

class Kubernetes(models.Model):
    docker=models.OneToOneField(Docker,on_delete=models.CASCADE)
    deploymentName=models.CharField(max_length=100,blank=False,null=False)
    configDataPath=models.CharField(max_length=200,blank=False,null=False)
    yamlDeployments=models.CharField(max_length=200,blank=False,null=False)
    defhelmChartPath=models.CharField(max_length=200,null=False,blank=False)
    helmDeployments=models.CharField(max_length=200,null=False,blank=False)

    def __str__(self):
        return  self.deploymentName

    def createChart(self,services_ports):
        if len(services_ports)==0 or self.docker=="" or self.deploymentName=="" or self.defhelmChartPath=="":
            print("all fields are required")
            exit(1)
        dockerImage=str(self.docker.dockerImage)
        DOCKERFILE_PATH = self.docker.defaultDockerFilePath
        EXPOSE_PORT = 3000  # default port
        # open docker file to get expose port
        with open(DOCKERFILE_PATH, "r") as dockerfile:
            for content in dockerfile:
                if "EXPOSE" in content:
                    EXPOSE_PORT = content.split()
        #writing values.yaml file
        with open(os.path.join(self.defhelmChartPath, 'values.yaml'), "w") as file:
            file.write(
                f"""
image:
  repository: """+dockerImage+"""
  tag: latest
replicaCount: 1
service:
  type: LoadBalancer
  targetPort: """+EXPOSE_PORT[1]+"""
name: """+self.deploymentName)

        #writing chart.yaml file
        with open(os.path.join(self.defhelmChartPath, 'Chart.yaml'), "w") as file:
            file.write(
                f"""
apiVersion: v2
name: {self.deploymentName}
type: application
version: 1"""
            )
        template_dir=os.path.join(self.defhelmChartPath,'templates')
        servicespath = os.path.join(template_dir, 'service.yaml')
        deploymentpath = os.path.join(template_dir, 'deployment.yaml')

        #writing deployment.yaml file
        with open(deploymentpath, "w") as file:
            file.write(
                """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name }}
  labels:
    app: {{ .Values.name }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{ .Values.name }}
  template:
    metadata:
      labels:
        app: {{ .Values.name }}
    spec:
      containers:
      - name: container-""" + self.deploymentName + """
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}"""
            )

        #writing service.yaml file
        with open(servicespath, 'w')as file:
            file.write(
                """apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.name }}
spec:
  selector:
    app: {{ .Values.name }}
  ports:
    - protocol: TCP
      name: service1
      port: """+str(services_ports[0])+"""
      targetPort: {{ .Values.service.targetPort }}
    - protocol: TCP
      name: service2
      port: """+str(services_ports[1])+"""
      targetPort: {{ .Values.service.targetPort }}
    - protocol: TCP
      name: service3
      port: """+str(services_ports[2])+"""
      targetPort: {{ .Values.service.targetPort }}
    - protocol: TCP
      name: service4
      port: """+str(services_ports[3])+"""
      targetPort: {{ .Values.service.targetPort }}
    - protocol: TCP
      name: service5
      port: """+str(services_ports[4])+"""
      targetPort: {{ .Values.service.targetPort }}
  type: {{ .Values.service.type }}"""
            )
    def deployChart(self):
        if self.docker.defaultDockerFilePath=="" or self.defhelmChartPath=="" or self.deploymentName=="":
            print("3 fields are required dockerfilepath, deploymentname, defhelmchart")
            exit(1)
        clone_dir=os.path.dirname(self.docker.defaultDockerFilePath)
        helmChartName=os.path.basename(self.defhelmChartPath)
        print(clone_dir)
        subprocess.call(['helm','install',self.deploymentName,helmChartName],cwd=clone_dir)
    def remove_helm_deployment(self):
        if self.deploymentName=="":
            print("deploymentName is required")
            exit(1)
        subprocess.call(['helm', 'uninstall', str(self.deploymentName)])



#this can be get_deploymentfile
    def get_deployment_file(self,type,filename):
        helm_template_dir=os.path.join(self.defhelmChartPath,'templates')
        if type=="defDocker":
            filepath=self.docker.defaultDockerFilePath
        if filename=="service.yaml":
            filepath=os.path.join(helm_template_dir,filename)
        if filename=="deployment.yaml":
            filepath=os.path.join(helm_template_dir,filename)
        if filename=="values.yaml":
            filepath=os.path.join(self.defhelmChartPath,filename)
        if filename=="Chart.yaml":
            filepath=os.path.join(self.defhelmChartPath,filename)

        if type=="newConfig":
            filepath=os.path.join(self.configDataPath,filename)
        if type=="newyaml":
            filepath = os.path.join(self.yamlDeployments, filename)
        if type=="newDocker":
            filepath = os.path.join(self.docker.deploymentPath, filename)

        file_content = []
        with open(filepath, "r") as file:
            for data in file:
                file_content.append(data)
        return file_content
class Endpoints(models.Model):
    kubernetes=models.ForeignKey(Kubernetes,on_delete=models.CASCADE)
    ports=models.PositiveIntegerField(primary_key=True)

    def __str__(self):
        return str(self.ports)

    def generate_port_numbers(self,endpoints):
        port_low_range = 4000
        port_up_range = 4005
        services_ports=[]
        if len(endpoints)!=0:
            port_low_range = endpoints[len(endpoints) - 1].ports + 1
            port_up_range = port_low_range + 5
        for ports in range(port_low_range, port_up_range):
            services_ports.append(ports)
        return services_ports