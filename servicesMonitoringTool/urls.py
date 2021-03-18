"""servicesMonitoringTool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth.views import LogoutView,LoginView,PasswordResetView,PasswordResetCompleteView,PasswordResetConfirmView,PasswordResetDoneView
from devops import views as app_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

    path('accounts/password_reset/',PasswordResetView.as_view(),name='password_reset_view'),
    path('changePassword/',app_views.changePassword,name='changePassword'),
    path('getDeploymentFile/',app_views.get_deploymentfile,name='getDeploymentFile'),
    path('github_cloning/', app_views.github_cloning, name="github_cloning"),
    path("projectDeployment/", app_views.projectDeployment, name="projectDeployment"),
    path('deleteProject/', app_views.deleteProject, name='deleteProject'),
    # path('getDockerFile/', app_views.get_default_dockerFile, name='getDockerFile'),
    path('startMonitoring/', app_views.start_monitoring, name='startMonitoring'),
    # path('getServicesFile/', app_views.get_default_servicesFile, name="getServicesFile"),
    # path('getDeploymentFile', app_views.get_default_deploymentFile, name='getDeploymentFile'),
    path('signup/', app_views.signup, name='signup'),
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # path('signup/',app_views.Registration.as_view(),name='signup'),
    path('deploy/', app_views.deploy, name='deploy'),
    path('monitoring/', app_views.monitoring, name='monitoring'),
    path('', app_views.Home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]
urlpatterns+=staticfiles_urlpatterns()
