import json,copy,time,os
from devops.dataGenerationAndMonitoring.Iterations import iterator
from devops.dataGenerationAndMonitoring.Iterations.iterator import get_new_filetag,get_prev_filetag,get_total_files_length,get_new_filetag1,get_prev_filetag1
from devops.dataGenerationAndMonitoring.modules import algo1
from devops.dataGenerationAndMonitoring.modules.deployments import generate_deployment_files
#initial configuration template

# DIR = os.path.join(os.getcwd(), 'docker\dataGenerationAndMonitoring\Iterations')
DIR=None
def get_initial_files(DIR,initial_template):
    #generate the name for new configuration file
    configfile=str(get_new_filetag1(DIR))+'config.json'
    #generate the name for new data file
    datafile=str(get_new_filetag1(DIR))+'data.json'
    #populate new configuration file
    iterator.generate_config_file(template=initial_template,DIR=DIR,filename=configfile)
    #populate new data file
    iterator.generate_data(DIR,configfile,datafile)


def getLastDataObject(DIR,config_file,data_file):
    #get the latest min and max ranges for cpu , container and services
    #need this method , because we have to generate new data for the same file if monitoring
    #algorithm didnot found any exceeding threshold in the specific data.json file
    #new data deopend on the previous data last object because in real time there is very small
    #variation in resource usage
    with open(os.path.join(DIR,data_file),'r') as data:
        content=json.loads(data.read())
    content=content[len(content)-1]
    pod=content['pod']
    pod_cpu=pod['metrices']['CPU']
    pod_ram=pod['metrices']['RAM']

    container=pod['containers']
    container=container[len(container)-1]
    container_load=container['metrices']['load']

    services=container['services']
    service=services[len(services)-1]
    service_load=service['metrices'][0]['load']
    iterator.generate_data(DIR,config_file,data_file,pod_cpu=pod_cpu,pod_ram=pod_ram,container_load=container_load,service_load=service_load)

def data_monitor(defaultDockerFilePath,dockerImage,dockerDeploymentPath,configDataPath,yamlFilePath,servicesPort,helmDeploymentPath):
    global DIR
    DIR=configDataPath
    initial_template = [
        {
            "pod": {
                "name": "pod1",
                "metrices": {
                    "CPU": "",
                    "RAM": ""
                },
                "containers": [
                    {
                        "id": "c1",
                        "metrices": {
                            "load": "",

                        },
                        "services": [
                            {
                                "port": str(servicesPort[0]),
                                "metrices": [
                                    {
                                        "load": ""
                                    }]},
                            {
                                "port": str(servicesPort[1]),
                                "metrices": [
                                    {
                                        "load": ""
                                    }]},
                            {
                                "port": str(servicesPort[2]),
                                "metrices": [
                                    {
                                        "load": ""
                                    }]},
                            {
                                "port": str(servicesPort[3]),
                                "metrices": [
                                    {
                                        "load": ""
                                    }]},
                            {
                                "port": str(servicesPort[4]),
                                "metrices": [
                                    {
                                        "load": ""
                                    }]}
                        ]  # services array close
                    }  # container 1 close

                ]
            }
        }
    ]
    if get_total_files_length(DIR)==0:
        # print('get initial files')
        get_initial_files(DIR,initial_template)

    counter=0
    for run in range(50):
        # print('loop',run)
        #pausing loop for 3 seconds
        #get the latest name for data file
        data_read_file=str(get_prev_filetag1(DIR))+'data.json'
        data_read_path=os.path.join(DIR,data_read_file)
        # print('prev file tag is ',data_read_path)
        #read the lates data.json file
        #read the lates data.json file
        with open(data_read_path) as f:
            data=f.read()
            dataset=json.loads(data)

        #get the latest config file name to monitor
        config_read_file=str(get_prev_filetag1(DIR))+'config.json'

        #creating the path to access the latest config file
        config_read_path=os.path.join(DIR,config_read_file)

        #call monitoring function to check wether data.json file have any object that exceeds
        #thrshold, if yes then we need to update the template (cofig.json file)
        new_template=algo1.monitorData(dataset,config_read_path)
        #if false then no change in template occur after monitoring , need to add more objects to the latest data.json file

        if new_template==False:
            #no need to update the template just overwrite the new data to latest data.json file
            #add more objects to the lates data.json file
            data_file=str(get_prev_filetag1(DIR))+'data.json'
            config_file = str(get_prev_filetag1(DIR)) + 'config.json'
            getLastDataObject(DIR,config_file,data_file)
            print('No changing in template no need to update the config file')
            continue
        else:
            print('--------------------------')
            print('we are generating data')
            #how much containers we need for new temlate (config.json file)
            print('total containers {}'.format(len(new_template[0]['pod']['containers'])))
            for container in new_template[0]['pod']['containers']:
                   print('Id: {} services: {}'.format(container['id'],len(container['services'])))

            print('--------------------------')
            #generate stuff for new files

            #creating name for new configuration file
            new_config_file=str(get_new_filetag1(DIR))+'config.json'

            # creating name for new data file
            new_data_file=str(get_new_filetag1(DIR))+'data.json'
            # print(new_config_file,new_data_file)

            #creating config.json file with new template
            iterator.generate_config_file(template=new_template,DIR=DIR,filename=new_config_file)

            #creating the data.json file populate data according to new template
            iterator.generate_data(DIR,new_config_file,new_data_file)

            #create docker files according to how many containers we need in new config
            #we are passing prev_filestags here becaause at last 2 function that we call above
            #already created new files
            required_fields = [
                'tag', 'dockerImage', 'defaultDockerFilePath', 'dockerDeploymentPath', 'configDataPath', 'yamlFilePath',
                'helmDeploymentPath'
            ]
            generate_deployment_files(
                tag=iterator.get_prev_filetag1(DIR),
                dockerImage=dockerImage,
                defaultDockerFilePath=defaultDockerFilePath,
                dockerDeploymentPath=dockerDeploymentPath,
                configDataPath=configDataPath,
                yamlFilePath=yamlFilePath,
                helmDeploymentPath=helmDeploymentPath)
