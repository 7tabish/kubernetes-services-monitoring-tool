import json,os,copy,random

def get_initial_config(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read()
        dataset = json.loads(data)
    return dataset

def generate_config_file(**kwargs):
    #kwargs are key vbalue pairs when we pass more
    if kwargs:
        if not kwargs['template'] or not kwargs['filename'] or not kwargs['DIR']:
            print("tempalte,filename and DIR are required")
            exit(1)
        filename=kwargs['filename']
        template=kwargs['template']
        DIR=kwargs['DIR']

    print('filename is ',filename)
    path=os.path.join(DIR,filename)
    print('writing config file../.')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
#(int) return total number of files.

DIR=os.getcwd()
DIR=os.path.join(DIR,'docker\dataGenerationAndMonitoring\Iterations')

#this method will return integer that is the number for new next file in that directory
def get_new_filetag():
    #get the total number of files in the directory of iterations
    DIR_SIZE = (len(os.listdir(DIR)))
    #minus 2 due to 2 default are always show when we try to get the length of directory
    DIR_SIZE = DIR_SIZE - 2
    #incremet of 1 so we can assign that number to new incoming file in that directory
    new_file_tag = int((DIR_SIZE / 2) + 1)
    if new_file_tag <10:
        new_file_tag=str("0"+str(new_file_tag))
    # print('new file is',new_file_tag)
    return new_file_tag

#(int) return the number of latest configuration file
def get_prev_filetag():
    DIR_SIZE = (len(os.listdir(DIR)))
    DIR_SIZE = DIR_SIZE - 2
    prev_file_tag = int(DIR_SIZE / 2)
    if prev_file_tag<10:
        prev_file_tag=str("0"+str(prev_file_tag))
    return prev_file_tag

def get_total_files_length(DIR):
    DIR_SIZE = (len(os.listdir(DIR)))
    total_files=int(DIR_SIZE/2)
    # print("total existing files are ",total_files)
    return total_files

#this method will return integer that is the number for new next file in that directory
def get_new_filetag1(DIR):
    #get the total number of files in the directory of iterations
    DIR_SIZE = (len(os.listdir(DIR)))
    DIR_SIZE = int(DIR_SIZE / 2)
    new_file_tag=DIR_SIZE+1
    if new_file_tag<10:
        new_file_tag=str("0"+str(new_file_tag))
    return new_file_tag

#(int) return the number of latest configuration file
def get_prev_filetag1(DIR):
    DIR_SIZE = (len(os.listdir(DIR)))
    prev_file_tag=int(DIR_SIZE/2)
    if prev_file_tag<10:
        prev_file_tag=str("0"+str(prev_file_tag))
    return prev_file_tag




import time
def get_pod_load(min_range,max_range):
    return random.randrange(min_range,max_range)


def get_load(min_range, max_range):
    return random.randrange(min_range, max_range)


def generate_data(DIR, config_file, data_file,**kwargs):
    # min and max load range for pod metrices
    pod_min_cpu = 1
    pod_max_cpu = 100
    pod_min_ram = 1
    pod_max_ram = 100

    # min and max range for container metrices (load)
    container_min_range = 1
    container_max_range = 95

    # min and max range for container's services
    service_max_range = 95
    service_min_range = 1
    if kwargs:
        if kwargs['pod_cpu']>10 and kwargs['pod_cpu']<85:
            pod_min_cpu=kwargs['pod_cpu']-10
            pod_max_cpu=kwargs['pod_cpu']+10
        if kwargs['pod_ram']>10 and kwargs['pod_ram']<85:
            pod_min_ram=kwargs['pod_ram']-10
            pod_max_ram=kwargs['pod_ram']+10
        if kwargs['container_load'] > 10 and kwargs['container_load'] < 85:
            container_min_range = kwargs['container_load'] - 10
            container_max_range = kwargs['container_load'] + 10
        if kwargs['service_load'] > 10 and kwargs['service_load'] < 85:
            service_min_range = kwargs['service_load'] - 10
            service_max_range = kwargs['service_load'] + 10



    # getting the path of the latest config file
    path_config = os.path.join(DIR, config_file)

    # reading the latest config file
    with open(path_config, 'r', encoding='utf-8') as f:
        data = f.read()
        dataset = json.loads(data)
    new_data = []
    pod_counter = 0
    container_counter = 0
    #set the default load value that can use only for first object in any dataset


    # iterate loop 10 times to generate 10 objects of dataset
    for load in range(0, 10):
        config = copy.deepcopy(dataset)
        pod_counter = 0
        for pod in config:
            #make container_counter to 0 on every new pod so we can calculate the total no of container on each pod
            container_counter = 0

            #get the random value for pod_cpu load
            pod_cpu_laod=get_pod_load(pod_min_cpu,pod_max_cpu)
            # get the random value for pod_ram load
            pod_ram_laod=get_pod_load(pod_min_ram,pod_max_ram)

            #setting the pod metrices(cpu and ram)
            pod['pod']['metrices']['CPU'] = pod_cpu_laod
            pod['pod']['metrices']['RAM'] = pod_ram_laod



            for container in pod['pod']['containers']:

                # generating the new container name
                container_counter = container_counter + 1
                #getting the load of container
                container_load = get_load(container_min_range, container_max_range)
                container['metrices']['load'] = container_load

                for service in container['services']:
                    #get the service load for each service in the container
                    service_load = get_load(service_min_range, service_max_range)
                    for metrices in service['metrices']:
                        metrices['load'] = service_load
            new_data.append(pod)
    # updating the min and max range of pod(cpu and ram) for next iteration
        if pod_cpu_laod < 90 and pod_cpu_laod > 10:
            pod_min_cpu = pod_cpu_laod - 10
            pod_max_cpu = pod_cpu_laod + 10
        if pod_ram_laod < 90 and pod_ram_laod > 10:
            pod_min_ram = pod_ram_laod - 10
            pod_max_ram = pod_ram_laod + 10
    #************************************************
    #update the container load (min and max range)
        if container_load<85 and container_load>10:
            container_min_range=container_load-10
            container_max_range=container_load+10


        if service_load>10 and service_load<85:
            service_min_range=service_load-10
            service_max_range=service_load+10

    path_data = os.path.join(DIR, data_file)
    with open(path_data, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)


