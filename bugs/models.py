from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Bug(models.Model):
    STATUS_CHOICES =[('Open','Open'),('In Progress','In progress'),('Closed','Closed'),]

    PRIORITY_CHOICES =[('Low','Low'),('Medium','Medium'),('High','High'),('Critical','Critical'),]


    title = models.CharField(max_length = 200)
    description = models.TextField()
    status = models.CharField(max_length = 20, choices = STATUS_CHOICES, default='Open')
    created_by = models.ForeignKey(User,on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    image = models.ImageField(upload_to ='bug_images/',blank =True, null =True)

    ## new fields
    priority= models.CharField(max_length =20,choices =PRIORITY_CHOICES, default='Medium')
    progress= models.PositiveIntegerField(default = 0)
    time_spent = models.PositiveIntegerField(default =0)
    assigned_to = models.ForeignKey(
        User,on_delete = models.SET_NULL , null= True, blank = True,
        related_name ='assigned_bugs' 
    )
    updated_at = models.DateTimeField(auto_now = True)
    due_date = models.DateTimeField(null =True, blank = True)
    notes  = models.TextField(blank = True)

    




    def __str__(self):
        return self.title