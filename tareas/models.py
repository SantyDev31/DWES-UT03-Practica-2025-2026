from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

# Model to stablish the roles of student and teacher to the user extending from AbstractUser wich already gives us the necessary fields
class User(AbstractUser):
    ROLE_STUDENT = 'ST'
    ROLE_TEACHER = 'TE'
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_TEACHER, 'Teacher')
    ]

    # we add this field to store the role of the user with the setted up options
    role = models.CharField(max_length=2,choices=ROLE_CHOICES,default=ROLE_STUDENT)

    def is_student(self):
        return self.role == self.ROLE_STUDENT
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER
    
    def __str__(self):
        return self.username
    
# Model for the groups of users
class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User,related_name='student_groups',limit_choices_to={'role': User.ROLE_STUDENT})

    tutor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='tutored_groups',
        on_delete=models.SET_NULL,
        limit_choices_to={'role': User.ROLE_TEACHER}
    )

    def __str__(self):
        return self.name

class Task(models.Model):
    TYPE_INDIVIDUAL = 'IN'
    TYPE_GROUP = 'GR'
    TYPE_EVALUABLE = 'EV'

    TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, 'Individual'),
        (TYPE_GROUP, 'Group'),
        (TYPE_EVALUABLE, 'Evaluable')
    ]

    STATUS_PENDING = 'PE' # Task just created
    STATUS_PENDING_REVIEW = 'PR' # Task pending teacher review
    STATUS_COMPLETED = 'CO' # Task completed
    STATUS_REJECTED = 'RE' # Task evaluation rejected by teacher

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'), 
        (STATUS_PENDING_REVIEW, 'Pending Review'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REJECTED, 'Rejected')
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=2,choices=TYPE_CHOICES)
    task_status = models.CharField(max_length=2,choices=STATUS_CHOICES, default=STATUS_PENDING)

    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks'
    )

    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='group_tasks'
    )

    completed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_tasks'
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    validated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='validated_tasks'
    )
    validated_at = models.DateTimeField(null=True, blank=True)

    reminder_date = models.DateTimeField(null=False, blank=False)

    grade = models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['task_type']),
            models.Index(fields=['task_status']),
            models.Index(fields=['created_by']),
        ]
    

    def clean(self):
        if(self.task_type == self.TYPE_INDIVIDUAL and self.group is not None):
            raise ValidationError("Individual tasks cant be assigned to groups.")
        if(self.task_type == self.TYPE_GROUP and self.assigned_to is not None):
            raise ValidationError("Group tasks cant be assigned to individuals alone.")
        
        return super().clean()

    def __str__(self):
        return self.title

    def needs_validation(self):
        return self.task_type == self.TYPE_EVALUABLE
    
    def mark_completed(self, user):
        if user.is_student() and not self.needs_validation():
            self.task_status = self.STATUS_COMPLETED
            self.completed_by = user
            self.completed_at = timezone.now()
            self.save()
            return
        
        if user.is_student() and self.needs_validation():
            self.task_status = self.STATUS_PENDING_REVIEW
            self.completed_by = user
            self.completed_at = timezone.now()
            self.save()
            return

        if user.is_teacher() and self.needs_validation():
            self.task_status = self.STATUS_COMPLETED
            self.validated_by = user
            self.validated_at = timezone.now()
            self.save()
            return

    
    