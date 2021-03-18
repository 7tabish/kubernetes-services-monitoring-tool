from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from devops.forms import UserRegistrationForms,ChangePasswordForm
from django.contrib.auth import login, authenticate,update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegistrationForms,GithubUrlForm
from django.shortcuts import render, redirect,HttpResponse
from  django.urls import reverse_lazy
from django.views.generic import TemplateView,CreateView
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from devops.models import Github,Docker,Kubernetes,Endpoints
from django.http import JsonResponse
from git import Repo
import shutil
import subprocess
import shutil
import os
import tempfile
import devops.dataGenerationAndMonitoring.main as main
from django.contrib.auth.decorators import login_required

def signup(request):
    if request.method == 'POST':
        form = UserRegistrationForms(request.POST)
        if form.is_valid():
            form.save()
            email=form.cleaned_data['email']
            username = form.cleaned_data['username']
            raw_password = form.cleaned_data['password1']
            user = authenticate(email=email,username=username, password=raw_password)
            login(request, user)
            path=os.path.join(os.getcwd(),username)
            if not os.path.exists(path):
                os.mkdir(path)
            return redirect("home")
    else:
        form = UserRegistrationForms()
    return render(request, 'registration.html', {'form': form})

def get_deploymentfile(request):
    url=request.GET.get('url')
    type=request.GET.get('type')
    filename = request.GET.get('filename')
    if url is None or type is None or filename is None:
        return JsonResponse({'Error ','all fields are required url,type, filename'})
    def_allowed_types=['defDocker','defYaml']
    new_allowed_types=['newyaml','newDocker','newConfig','newHelm']
    if type not in def_allowed_types and type not in new_allowed_types:
        return JsonResponse({'error':'Type not supported'})
    github =Github.objects.filter(url=url)
    if len(github)==0:
        return  JsonResponse({'error':'No project found with this url'})
    docker=Docker.objects.filter(github=github[0])
    if len(docker)==0:
        return JsonResponse({'error':'url is not deployed'})
    kubernetes=Kubernetes.objects.get(docker=docker[0])


    if type in def_allowed_types:
        if type=="defDocker":
            kubernetes=Kubernetes(docker=docker[0])
        if type=="defYaml":
            kubernetes=Kubernetes(defhelmChartPath=kubernetes.defhelmChartPath)
        filecontent = kubernetes.get_deployment_file(type, filename)
        return JsonResponse({'data':filecontent})

    if type in new_allowed_types:
        if type == "newConfig":
            kubernetes = Kubernetes(configDataPath=kubernetes.configDataPath)
        if type == "newDocker":
            kubernetes = Kubernetes(docker=docker[0])
        if type == "newyaml":
            kubernetes = Kubernetes(yamlDeployments=kubernetes.yamlDeployments)
        if type=="newHelm":
            filepath = os.path.join(str(kubernetes.helmDeployments), filename)
            print(filename, filepath)
            if os.path.exists(filepath):
                response = HttpResponse(open(filepath, 'rb'), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
                return response
        filecontent = kubernetes.get_config_data_file(type, filename)
        return render(request, 'files.html', {"content": filecontent, "filename": filename})


def monitoring(request):
    url=request.GET.get('url')
    github = Github.objects.filter(user=request.user, url=url)
    if len(github)==0:
        project_notFound="No project found with this url."
        return render(request,'monitoring.html',{"project_notFound":project_notFound})
    docker=Docker.objects.filter(github=github[0])
    kubernetes=Kubernetes.objects.filter(docker=docker[0])
    endpoints=Endpoints.objects.filter(kubernetes=kubernetes[0])
    if len(kubernetes)==0:
        request.session['project_url']=url
        return  redirect('projectDeployment')
    return render(request,'monitoring.html',{'endpoints':endpoints})


def start_monitoring(request):
    #get the data from github table against username and  url
    github = Github.objects.get(user=request.user, url=request.GET.get('url'))
    docker=Docker.objects.get(github=github)
    kubernetes=Kubernetes.objects.get(docker=docker)
    endpoints=Endpoints.objects.filter(kubernetes=kubernetes)
    main.run(docker, kubernetes,endpoints)
    configFiles=os.listdir(str(kubernetes.configDataPath))
    dockerFiles = os.listdir(str(docker.deploymentPath))
    yamlFiles = os.listdir(str(kubernetes.yamlDeployments))
    helmDeployments=os.listdir(str(kubernetes.helmDeployments))
    files={"url":request.GET.get("url"),"files":[{"config":configFiles},{"dockerfile":dockerFiles},{"yaml":yamlFiles},{'helm':helmDeployments}]}
    return JsonResponse({'data':files})

@login_required
def deploy(request):
    if "ports" in request.session:
        ports=request.session['ports']
        del request.session['ports']
    else:
        ports=False


    form=GithubUrlForm
    github=Github.objects.filter(user=request.user)
    data={'github_form':form,'github':github,'ports':ports}
    return render(request,'deploy.html',data)

def github_cloning(request):
    try:
        clone_url=request.GET.get("url")
        loggedin_user = User.objects.get(username=request.user)
        is_github_exists = Github.objects.filter(user=loggedin_user, url=clone_url)
        if not is_github_exists:
            # no record exists with that username and url
            # get current directory and define path for temporay directory
            DIR = os.getcwd()
            DIR = os.path.join(DIR, str(request.user))
            cloning_dir = tempfile.mkdtemp(dir=DIR)
            # save loggedin user, github url and cloned directory path to DB
            github = Github(user=loggedin_user, url=clone_url, cloned_directory=cloning_dir)
            if github.cloning():
                print('cloning save')
                github.save()
            else:
                return JsonResponse({"error":"Error while downloading repository"})
        else:
            return JsonResponse({"error":"URL already exists"})
    except Exception as e:
        return JsonResponse({"error":e})
    return JsonResponse({"status":True})



def projectDeployment(request):
    if "project_url" in request.session:
        project_url=request.session['project_url']
    else:
        project_url = request.GET.get("url")
    loggedin_user = request.user
    github = Github.objects.filter(user=loggedin_user, url=project_url)
    print("gituhb ",github)
    if len(github)==0:
        return JsonResponse({'Error':'No project exists with provided url'})
    isDockerExists = Docker.objects.filter(github=github[0])
    print("docker ",isDockerExists)
    if len(isDockerExists)!=0:
        return JsonResponse({'Error ':'Url already deployed'})

    # docker=Docker.objects.filter(github=github)
    # if len(docker)!=0:
    #     return JsonResponse({"Error ":"This url already deployed"})
    if request.method=="GET":
        return render(request,"image.html")
    if request.method=="POST":
        github=Github.objects.filter(user=loggedin_user,url=project_url)
        if len(github)!=0:
            try:
                cloned_dir=github[0].cloned_directory
                image_name = str('tabishmanzoor/' + str(request.user) + str(os.path.basename(cloned_dir)))
                DeploymentPath = os.path.join(cloned_dir,"dockerDeployments")
                os.mkdir(DeploymentPath)

                #this path is already available
                defaultDockerFilePath=os.path.join(cloned_dir,"Dockerfile")
                docker=Docker(github=github[0],dockerImage=image_name,deploymentPath=DeploymentPath,defaultDockerFilePath=defaultDockerFilePath)
                docker.create_image()
                docker.push_image()


                #create helm chart

                #kubernetes.createHelmChart
                configDataPath=os.path.join(cloned_dir,"config_data")
                os.mkdir(configDataPath)

                yamlDeployments=os.path.join(cloned_dir,"yamlDeployments")
                os.mkdir(yamlDeployments)

                defhelmChartPath= os.path.join(cloned_dir, "defHelmChart")
                templates=os.path.join(defhelmChartPath,"templates")
                os.makedirs(templates)

                helmDeployments=os.path.join(cloned_dir,'helmDeployments')
                os.mkdir(helmDeployments)

                getDocker=Docker.objects.filter(github=github[0])
                #if length >0 it means there is already project exists with deployment
                if len(getDocker)!=0:
                    deploymentTag=len(getDocker)+1

                #get all the rows from endpoints table
                endpoints = Endpoints.objects.all()
                #initialize an object of Endpoint class so we can call its method/function
                endpoints_=Endpoints()
                #calling a method of endpoint class and we will get array of port number in return
                services_ports=endpoints_.generate_port_numbers(endpoints)
                print("port are ",services_ports)


                #create a deployment name, differnet for each deployment
                deploymentName=str(request.user)+"-nodeapp-"+str(len(Docker.objects.all())+1)


                #initialize a kubernetes object
                kubernetes=Kubernetes(docker=docker,
                           configDataPath=configDataPath,yamlDeployments=yamlDeployments,deploymentName=deploymentName,defhelmChartPath=defhelmChartPath,helmDeployments=helmDeployments)
                #call kubernetes methods
                kubernetes.createChart(services_ports)
                kubernetes.deployChart()

                #save record in docker and kubernetes table
                docker.save()
                kubernetes.save()

                #save ports to enpoits
                for port in services_ports:
                    endpoints =Endpoints(kubernetes=kubernetes,ports=port)
                    endpoints.save()
                #add list of port in session so we can show it on our deploy page for only one time after completion of deployment
                request.session['ports']=services_ports
                #this whole function will run on 2 condition first when we clone project then click on create deployment button and second when we click on url from table and if project is not deployed on kybernetes then this function also run to deploy that project and that why we pass project_urlk in session to pass url from other function to this function

                if 'project_url' in request.session:
                    del request.session['project_url']
            except Exception as e:
                return JsonResponse({"Error: ":e})

        return redirect("deploy")
        #created docker image
        #create Helm chart




def Home(request):
    return render(request,'home.html')







import time
@login_required
def deleteProject(request):
    url=request.GET.get('url')
    github_project=Github.objects.filter(user=request.user,url=url)
    if len(github_project)==0:
        return JsonResponse({'error':'No project exist with this url'})
    docker=Docker.objects.filter(github=github_project[0])
    if len(docker)!=0:
        dockerImage=docker[0].dockerImage
        kubernetes=Kubernetes.objects.filter(docker=docker[0])
        deploymentName=kubernetes[0].deploymentName
        kubernetes=Kubernetes(deploymentName=deploymentName)
        print("calling remove helm deploymetn")
        kubernetes.remove_helm_deployment()
        #wait for remove of helm deployments
        print("wait..")
        time.sleep(5)
        print("Deleting docker image")
        docker=Docker(dockerImage=dockerImage)
        docker.remove_image()
    github_project.delete()
    return redirect("deploy")

def changePassword(request):
    form=PasswordChangeForm(request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('changePassword')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request,'changePassword.html',{'form':form})

