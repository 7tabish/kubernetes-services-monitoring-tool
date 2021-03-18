from django.contrib import admin
from devops import models
# Register your models here.

admin.site.register(models.Github)
admin.site.register(models.Docker)
admin.site.register(models.Kubernetes)
admin.site.register(models.Endpoints)