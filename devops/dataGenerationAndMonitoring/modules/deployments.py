import os,json
import copy
import yaml
import zipfile
import shutil
def generate_docker_yaml_files(tag,EXPOSE,dockerDeploymentPath,configuration,yamlFilePath):
    print("EXPOSE ",EXPOSE)
    EXPOSE_PORT = 3000
    container_counter = 1
    services_counter = 1
    for content in configuration:
        for container in content['pod']['containers']:
            deployment_name = "nodeapp-{}-{}".format(str(tag), str(container_counter))
            services = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": deployment_name},
                "spec": {
                    "selector": {"app": deployment_name},
                    "ports": [],
                    "type": "LoadBalancer"
                },

            }
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": deployment_name,
                    "labels": {
                        "app": deployment_name
                    }},
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {
                            "app": deployment_name
                        }},
                    "template": {
                        "metadata":
                            {"labels":
                                 {"app": deployment_name}
                             },
                        "spec": {
                            "containers": []
                        }
                    }  # end template
                }  # end selector

            }  # end spec
            container_template = {
                "container": "",
                "image": "",
                "ports": {
                    "-containerPort": 3000
                }
            }

            data = '''FROM node:alpine
              WORKDIR /usr/src/app
              COPY package*.json ./

              RUN npm install
              # If you are building your code for production
              # RUN npm ci --only=production

              # Bundle app source
              COPY . .

              EXPOSE {}
              CMD [ "node", "server.js" ]'''.format(EXPOSE_PORT)

            services_template = {"-protocol": "TCP", "name": "service1", "port": 666, "targetport": 666}
            for service in container['services']:
                services_template['name'] = "service{}".format(services_counter)
                services_template['port'] = int(service['port'])
                services_template['targetport'] = EXPOSE_PORT
                services['spec']['ports'].append(copy.deepcopy(services_template))
                services_counter = services_counter + 1

            container_template["container"] = "container-{}".format(container_counter)
            container_template["image"] = "image-{}".format(container_counter)
            container_template["ports"]["-containerPort"] = EXPOSE_PORT
            deployment['spec']['template']['spec']['containers'].append(copy.deepcopy(container_template))

            dockerFileName = str(tag) + '-' + str(container_counter) + '.Dockerfile'

            dockerFilePath = os.path.join(dockerDeploymentPath, dockerFileName)
            with open(dockerFilePath, 'w') as dockerFile:
                dockerFile.write(data)
            with open(os.path.join(yamlFilePath, str(tag) + "-" + str(container_counter) + "services.yaml"),
                      "w") as file:
                yaml.dump(services, file)
            with open(os.path.join(yamlFilePath, str(tag) + "-" + str(container_counter) + "deployment.yaml"),
                      "w") as file:
                yaml.dump(deployment, file)
            container_counter = container_counter + 1

def generate_helm_deployments(tag,configuration,dockerImage,EXPOSE_PORT,helmDeploymentPath):
    for content in configuration:
        container_counter = 1
        for container in content['pod']['containers']:
            file_tags='{}-{}'.format(tag,container_counter)
            deployment_name='nodeapp-{}'.format(file_tags)
            helm_chart_path=os.path.join(helmDeploymentPath,file_tags+"-chart")
            container_counter=container_counter+1
            template_dir=os.path.join(helm_chart_path,'templates')
            os.makedirs(template_dir)

            # writing values.yaml file
            with open(os.path.join(helm_chart_path, 'values.yaml'), "w") as file:
                file.write(
                    f"""
image:
  repository: """ + dockerImage + """
    tag: latest
replicaCount: 1
service:
  type: LoadBalancer
  targetPort: """ + EXPOSE_PORT[1] + """
name: """ + deployment_name)

            # writing chart.yaml file
            with open(os.path.join(helm_chart_path, 'Chart.yaml'), "w") as file:
                file.write(
                    f"""
apiVersion: v2
name: {deployment_name}
type: application
version: 1"""
                )
            servicespath = os.path.join(template_dir, 'service.yaml')
            deploymentpath = os.path.join(template_dir, 'deployment.yaml')
            # writing deployment.yaml file
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
      - name: container-""" + deployment_name + """
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}"""
                )

            #write services.yaml file
            services = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "{{ .Values.name }}"
                },
                "spec": {
                    "selector": {
                        "app": "{{ .Values.name }}"
                    },
                    "ports": [],
                    "type": "{{ .Values.service.type }}"

                }#close spec

            }#close services
            services_port_template={
            "protocol": "TCP",
            "name": 0,
            "port": 0000,
            "targetPort": "{{ .Values.service.targetPort }}"}
            services_counter=1
            for service in container["services"]:
                services_port_template['port']=int(service['port'])
                services_port_template['name']="service-"+str(services_counter)
                services['spec']['ports'].append(copy.deepcopy(services_port_template))
                services_counter=services_counter+1
            with open(servicespath,"w") as file:
                yaml.dump(services,file)

            zip_path = os.path.join(helmDeploymentPath, file_tags + '-chart.zip')
            zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(helm_chart_path):
                for file in files:
                    zipf.write(os.path.join(root, file))
            zipf.close()
            shutil.rmtree(helm_chart_path)



def generate_deployment_files(**kwargs):
    if kwargs:
       required_fields=[
           'tag','dockerImage','defaultDockerFilePath','dockerDeploymentPath','configDataPath','yamlFilePath','helmDeploymentPath'
       ]
       for field in required_fields:
           if not kwargs[field]:
               print("Error all fields are required, {}".format(required_fields))
               exit(1)
       tag=kwargs['tag']
       dockerImage=kwargs['dockerImage']
       defaultDockerFilePath=kwargs['defaultDockerFilePath']
       dockerDeploymentPath=kwargs['dockerDeploymentPath']
       configDataPath=kwargs['configDataPath']
       yamlFilePath=kwargs['yamlFilePath']
       helmDeploymentPath=kwargs['helmDeploymentPath']



    print("generating files for tag: ",tag)
    filename = str(tag) + 'config.json'
    filepath = os.path.join(configDataPath, filename)
    # reading the configuration file
    with open(filepath) as f:
        data = f.read()
        configuration = json.loads(data)

    #ceating the expose port from  default clone project's dockerfile
    EXPOSE_PORT = 3000  # default port
    # open docker file to get expose port
    with open(defaultDockerFilePath, "r") as dockerfile:
        for content in dockerfile:
            if "EXPOSE" in content:
                EXPOSE_PORT = content.split()

    generate_docker_yaml_files(tag,EXPOSE_PORT,dockerDeploymentPath,configuration,yamlFilePath)
    generate_helm_deployments(tag,configuration,dockerImage,EXPOSE_PORT,helmDeploymentPath)

