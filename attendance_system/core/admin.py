
# Register your models here.
from django.contrib import admin
from .models import ClassYear, Subject, Student, AttendanceSession, AttendanceRecord

admin.site.register(ClassYear)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
