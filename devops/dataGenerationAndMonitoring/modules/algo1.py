from devops.dataGenerationAndMonitoring.Iterations import iterator
import copy,time,json,os,csv


#return (json) object of new services
def get_new_services(t_services,ports):
    print("In method")
    print("T-services ",t_services," Ports ",ports)
    service_template={'port':'','metrices':[{'load':''}]}
    new_services=[]
    for port in ports:
        service_template['port']=port
        new_services.append(copy.deepcopy(service_template))

    return new_services

#return (json) object of new containers
def get_new_container(services):
    container_template={
            'id': 'new Container',
            'metrices': {'CPU': '', 'RAM': ''},
            'services':[]
    }
    container_template['services']=services
    return container_template

#monitor the metrices of pods , container and services
def monitorData(dataset,config_path):
    #iterate loop to all dataset
    for data in dataset:
        counter_container=0
        scalingup_services_counter = 0
        scalingdown_services_counter = 0
        scalingdown_counter_container=0
        down_prev_port = []
        down_curr_port = []
        new_port = []
        curr_port = []

        #getting the value of pod metrices and save in cpu and ram variable
        cpu=data['pod']['metrices']['CPU']
        ram = data['pod']['metrices']['RAM']

        #copy the current configuration template in variable (template)

        template= copy.deepcopy(iterator.get_initial_config(config_path))

        #scaling down
        if cpu<40 and ram<40:
            #scaling down work when we have more than 1 container
            if len(data['pod']['containers'])!=1:
                #iterate over all container
                for container in data['pod']['containers']:

                    scalingdown_container_services_counter=0
                    if container['id']=='c1':
                        scalingdown_counter_container=scalingdown_counter_container+1
                        #no need to scale down the first container
                        continue
                    #iterate all the services of a container

                    for service in container['services']:
                        #iterate only once
                        for metrices in service['metrices']:
                            if metrices['load'] < 35:
                                print("cpu => ", cpu, " Ram => ", ram)
                                print("load ",metrices['load'])
                                down_prev_port.append(service['port'])

                                #services that need to be eliminate from the current container
                                scalingdown_container_services_counter=scalingdown_container_services_counter+1

                                #overall services need to scale down
                                scalingdown_services_counter=scalingdown_services_counter+1
                                # print('need to scaling down, service load is ',metrices['load'])
                            else:
                                down_curr_port.append(service['port'])
                    #eliminate the services from the current container
                    if scalingdown_container_services_counter>0:

                        if len(container['services'])==scalingdown_container_services_counter:

                            del template[0]['pod']['containers'][scalingdown_counter_container]
                            continue
                        else:
                            print('Services in current container ',down_curr_port)
                            t_new_services=len(container['services'])-scalingdown_container_services_counter

                            template[0]['pod']['containers'][scalingdown_counter_container]['services']=get_new_services(t_new_services,down_curr_port)

                    scalingdown_counter_container = scalingdown_counter_container + 1


                #work when there is 1 or more scaling down services in a container
                if scalingdown_services_counter>0:
                    print('scaling down service to main container',down_prev_port)
                    new_services=get_new_services(scalingdown_services_counter,down_prev_port)
                    for service in new_services:
                        print(service)
                        template[0]['pod']['containers'][0]['services'].append(service)
                    # generate_logs('d', iterator.get_new_filetag1())
                    return template
                else:
                    # generate_logs('n', iterator.get_prev_filetag())







                    #this define how many container services need to stay in the current container
                    container_services_counter = 0


        #sscaling up
        #check if pod's cpu and ram exceeds threshold
        if cpu > 75 and ram > 70:#get the list of pod where cpu and ram are greater than 85
            #iterate over all containers of a pod
            for container in data['pod']['containers']:


                container_services_counter=0
                #if container have one services then move to other container
                if len(container['services'])==1:
                    counter_container=counter_container+1
                    continue

                #iterate over to all of the services of a container
                for service in container['services']:
                    #getting the load of services
                    for metrices in service['metrices']:
                        if metrices['load']>50:
                            new_port.append(service['port'])


                            # to make a filter at container level
                            container_services_counter=container_services_counter+1
                            # make a filter at pod level.increment service_counter to make a filter so we can add all the spliting services of one pod into new one container at a time
                            scalingup_services_counter=scalingup_services_counter+1
                        else:
                            curr_port.append(service['port'])
                #updating the current container services

                if container_services_counter>0:
                    #true when the spliting services equal to current container actual services
                    if len(container['services'])==container_services_counter:
                        #atleast the container must have 1 service remaining in scaling up we are removing the container in scaling down
                        # print(counter_container)
                        template[0]['pod']['containers'][counter_container]['services'] = get_new_services(1,new_port[0:1])
                        print('equal scaling up container ',new_port[0:1])
                        new_port=new_port[1:]
                        #minus one service , because we added that one in the parent container
                        scalingup_services_counter=scalingup_services_counter-1

                    else:
                        services_in_current_container=len(container['services'])-container_services_counter #define the remaining services in the current container
                        #updating the current container services if
                        print('services in remaining ',curr_port)
                        template[0]['pod']['containers'][counter_container]['services']=get_new_services(services_in_current_container,curr_port)
                counter_container = counter_container + 1

            #creating new containers
            #this works if current container have atleast 1 services remaining

            if scalingup_services_counter>0:
                print('services in new container',scalingup_services_counter,new_port)
                # create template for new container and its services
                services_in_new_cotainer = get_new_services(scalingup_services_counter,new_port)
                new_container = get_new_container(services_in_new_cotainer)
                template[0]['pod']['containers'].append(new_container)

            #if template changed after monitoring
            if template != copy.deepcopy(iterator.get_initial_config(config_path)):
                # generate_logs('u', iterator.get_new_filetag())
                return template
            else:
                #if tempalte not change
                # generate_logs('n', iterator.get_prev_filetag())
                return False
    if template == copy.deepcopy(iterator.get_initial_config(config_path)):
        #if no changing in the template after monitoring
        return False




def generate_logs(tag,filetag):
    # print('******************')
    print(str(tag)+' '+str(filetag))
    # print('******************')

    with open('logs.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([tag,filetag])

