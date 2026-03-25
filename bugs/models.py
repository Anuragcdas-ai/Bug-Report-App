from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Bug(models.Model):
    STATUS_CHOICES =[('Open','Open'),('In Progress','In progress'),('Closed','Closed'),]

    PRIORITY_CHOICES =[('Low','Low'),('Medium','Medium'),('High','High'),('Critical','Critical'),]


    title = models.CharField(max_length = 200)
    description = models.TextField()
    status = models.CharField(max_length = 20, choices = STATUS_CHOICES, default='Open',null=True)
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

    
    bug_id = models.CharField(max_length=10, blank=True, null=True)
    updated_by = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, related_name='updated_bugs')


    class Meta:
     permissions = [
           ("can_change_status", "Can change bug status"),
        ]




    def __str__(self):
        return self.title


    def save(self, *args, **kwargs):
        if not self.bug_id:
            last_bug = Bug.objects.order_by('-id').first()

            if last_bug and last_bug.bug_id:
                last_id = int(last_bug.bug_id.replace('BUG', ''))
                new_id = last_id + 1
            else:
                new_id = 1

            self.bug_id = f"BUG{new_id:03d}"

        super().save(*args, **kwargs)


class Profile(models.Model):

    
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    # Helper properties — reads directly from User, no duplication
    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    class Meta:
        permissions = [
            ("edit_user_profile_perm", "Can edit user profile"),
        ]


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)  # simple, no extra logic needed

@receiver(post_save, sender=Profile)
def assign_user_to_group(sender, instance, **kwargs):
    user = instance.user

    # Remove user from all role-based groups first
    user.groups.clear()

    if instance.role == 'tester':
        group, _ = Group.objects.get_or_create(name='Tester')
        user.groups.add(group)

    elif instance.role == 'developer':
        group, _ = Group.objects.get_or_create(name='Developer')
        user.groups.add(group)

    elif instance.role == 'admin':
        group, _ = Group.objects.get_or_create(name='Admin')
        user.groups.add(group)


