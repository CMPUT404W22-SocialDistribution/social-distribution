from django.db import models

# Create your models here.
class Node(models.Model):
    url = models.URLField(primary_key=True)
    name = models.CharField(max_length=50)

    incoming_username = models.CharField(max_length=20, null=True)
    incoming_password = models.CharField(max_length=20, null=True)

    outgoing_username = models.CharField(max_length=50)  # remote username
    outgoing_password = models.CharField(max_length=100)  # remote password

    
