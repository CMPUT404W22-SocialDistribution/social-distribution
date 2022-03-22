from django.contrib import admin
from .models import Node
# Register your models here.

class NodeAdmin(admin.ModelAdmin):
    list_display = ('url', 'outgoing_username', 'outgoing_password')


admin.site.register(Node, NodeAdmin)