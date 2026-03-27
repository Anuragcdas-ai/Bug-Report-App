from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.db.models import Sum, Avg



# =========================
class Sprint(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Team
    lead_developer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lead_sprints',
        limit_choices_to={'profile__role': 'developer'}
    )

    developers = models.ManyToManyField(
        User,
        related_name='assigned_sprints',
        limit_choices_to={'profile__role': 'developer'},
        blank=True
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sprints')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # ✅ Validation
    def clean(self):
        from django.core.exceptions import ValidationError

        if self.pk and self.lead_developer:
            if self.developers.filter(id=self.lead_developer.id).exists():
                raise ValidationError("Lead developer cannot be in developers list")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

 
    # ✅ Total hours
    def total_hours_spent(self):
        total_minutes = sum(bug.time_spent for bug in self.bugs.all())
        return total_minutes / 60

    # ✅ Developer-wise total hours
    def developer_hours_spent(self):
        all_developers = list(self.developers.all())

        if self.lead_developer:
            all_developers.append(self.lead_developer)

        all_developers = list(set(all_developers))

        developer_hours = {}

        for dev in all_developers:
            total_minutes = self.bugs.filter(assigned_to=dev).aggregate(
                total=Sum('time_spent')
            )['total'] or 0

            developer_hours[dev.username] = {
                'hours': total_minutes / 60,
                'user': dev,
                'total_minutes': total_minutes
            }

        return developer_hours

    # ✅ FIXED (based on CharField)
    def platform_wise_avg_time(self):
        """Get average time spent per platform"""
        
        platforms = self.bugs.values_list('platforms', flat=True).distinct()

        platform_avg = {}

        for platform in platforms:
            avg_minutes = self.bugs.filter(platforms=platform).aggregate(
                avg=Avg('time_spent')
            )['avg'] or 0

            platform_avg[platform] = avg_minutes / 60  # convert to hours

        return platform_avg

    # ✅ Developer-wise average
    def developer_wise_avg_time(self):
        all_developers = list(self.developers.all())

        if self.lead_developer:
            all_developers.append(self.lead_developer)

        all_developers = list(set(all_developers))

        developer_avg = {}

        for dev in all_developers:
            avg_minutes = self.bugs.filter(assigned_to=dev).aggregate(
                avg=Avg('time_spent')
            )['avg'] or 0

            developer_avg[dev.username] = {
                'hours': avg_minutes / 60,
                'user': dev
            }

        return developer_avg




# Create your models here.

class Bug(models.Model):
        # Add new fields
    sprint = models.ForeignKey(
        Sprint, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='bugs'
    )
    platforms = models.CharField(max_length = 200,default="Mobile")
    


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


    @property
    def time_spent_display(self):
        hours = self.time_spent // 60
        minutes = self.time_spent % 60
        return f"{hours}h {minutes}m"


    class Meta:
     permissions = [
           ("can_change_status", "Can change bug status"),
        ]




    def __str__(self):
        return self.title


    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # Step 1: Save first to get ID (for new objects)
        if is_new:
            super().save(*args, **kwargs)

            # Generate bug_id AFTER first save
            if not self.bug_id:
                self.bug_id = f"BUG{self.id:03d}"

            super().save(update_fields=['bug_id'])
            return

        # Step 2: Existing object → track status change
        old = Bug.objects.get(pk=self.pk)

        if old.status != self.status:
            duration = now() - self.created_at
            self.time_spent = int(duration.total_seconds() // 60)

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







