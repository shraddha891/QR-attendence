from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from datetime import date

class ClassYear(models.Model):
    name = models.CharField(max_length=50)  # FY, SY, TY

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)
    teachers = models.ManyToManyField(User)  # multiple teachers can teach one subject

    def __str__(self):
        return f"{self.name} ({self.year})"


class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20)
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.class_year}"


class AttendanceSession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    class_year = models.ForeignKey(ClassYear, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    expires_at = models.DateTimeField(default=timezone.now) 
    # New fields for location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject.name} - {self.date}"



class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="unknown")
    roll_number = models.CharField(max_length=20, default='unknown')
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.student.name} - {self.student.roll_number} - {self.session.subject.name} - {self.session.date}"

