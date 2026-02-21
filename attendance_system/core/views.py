# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import SimpleRegisterForm

from datetime import date
from .models import Subject, ClassYear

from django.contrib.auth.decorators import login_required
from datetime import date
from .models import ClassYear, Subject, Student, AttendanceRecord, AttendanceSession
from collections import defaultdict

from django.utils.timezone import now
from datetime import timedelta
import qrcode
import io
import base64
import uuid
from .models import AttendanceSession, Subject

from openpyxl import Workbook
from django.http import HttpResponse
from .models import AttendanceRecord
from datetime import date 

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import AttendanceSession, Student, AttendanceRecord
from uuid import UUID
from .utils import is_within_radius, is_session_expired

import logging
from django.shortcuts import render, redirect, get_object_or_404
from uuid import UUID
from .models import AttendanceSession, Student, AttendanceRecord
from .utils import is_within_radius, is_session_expired
from django.db import IntegrityError



def home(request):
    return render(request, 'core/home.html')

def register_view(request):
    if request.method == 'POST':
        form = SimpleRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registered successfully! Please log in.")

            return redirect('login')  
    else:
        form = SimpleRegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')  # update later
        else:
            messages.error(request, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def teacher_dashboard(request):
    years = ClassYear.objects.all()
    subjects = Subject.objects.all()
    today = date.today()

    # Filter values
    selected_class_year_id = request.GET.get('class_year')
    selected_subject_id = request.GET.get('subject')

    selected_class_year = None
    selected_subject = None

    # Get class year object (if selected)
    if selected_class_year_id:
        try:
            selected_class_year = ClassYear.objects.get(id=selected_class_year_id)
        except ClassYear.DoesNotExist:
            selected_class_year = None

    # Get subject object (if selected)
    if selected_subject_id:
        try:
            selected_subject = Subject.objects.get(id=selected_subject_id)
        except Subject.DoesNotExist:
            selected_subject = None

    # Filter students
    students_qs = Student.objects.all()
    if selected_class_year:
        students_qs = students_qs.filter(class_year=selected_class_year)

    total_students = students_qs.count()

    # Filter today's sessions
    sessions_today = AttendanceSession.objects.filter(
        teacher=request.user,
        date=today
    )
    if selected_class_year:
        sessions_today = sessions_today.filter(class_year=selected_class_year)
    if selected_subject:
        sessions_today = sessions_today.filter(subject=selected_subject)

    present_today = AttendanceRecord.objects.filter(session__in=sessions_today).count()
    attendance_percent = round((present_today / total_students) * 100, 2) if total_students else 0

    # ✅ Leave this unchanged – Attendance Records Table
    if selected_class_year:
        attendance_sessions = AttendanceSession.objects.filter(teacher=request.user, class_year=selected_class_year)
    else:
        attendance_sessions = AttendanceSession.objects.filter(teacher=request.user)

    attendance_records = []
    for session in attendance_sessions:
        total_students_for_session = Student.objects.filter(class_year=session.class_year).count()
        present_count = AttendanceRecord.objects.filter(session=session).count()
        absent_count = total_students_for_session - present_count
        attendance_records.append({
            'date': session.date,
            'subject': session.subject.name,
            'class_year': session.class_year.name,
            'present_count': present_count,
            'absent_count': absent_count
        })

    # Student attendance list for sessions today (unchanged)
    student_attendance_map = defaultdict(list)
    for session in sessions_today:
        records = AttendanceRecord.objects.filter(session=session).select_related('student')
        for record in records:
            student_attendance_map[session.id].append({
                'name': record.student.name,
                'roll': record.student.roll_number,
                'subject': session.subject.name,
                'class': session.class_year.name,
                'time': record.timestamp.strftime('%H:%M:%S'),
            })

    return render(request, 'core/dashboard.html', {
        'years': years,
        'subjects': subjects,
        'today': today,
        'total_students': total_students,
        'present_today': present_today,
        'attendance_percent': attendance_percent,
        'attendance_records': attendance_records,
        'selected_class_year': int(selected_class_year_id) if selected_class_year_id else '',
        'selected_subject_id': int(selected_subject_id) if selected_subject_id else '',
        'student_attendance_map': student_attendance_map,
    })

# dynamic subject
from django.http import JsonResponse

def get_subjects_by_class_year(request):
    class_year_id = request.GET.get('class_year_id')
    subjects = Subject.objects.filter(year_id=class_year_id)
    data = [{'id': subj.id, 'name': subj.name} for subj in subjects]
    return JsonResponse(data, safe=False)



def generate_qr(request):
    if request.method == 'POST':
        class_year_id = request.POST.get('ClassYears')  # 🔄 use correct key
        subject_id = request.POST.get('Subject')
        now = timezone.now()
        latitude = float(request.POST.get('latitude'))
        longitude = float(request.POST.get('longitude'))

        # Get actual DB objects
        subject = Subject.objects.get(id=subject_id)
        class_year = ClassYear.objects.get(id=class_year_id)

        # Create session with expiry (1 mins)
        expiry = timezone.now() + timedelta(minutes=1)

        # Generate unique token
        token = str(uuid.uuid4())
        while AttendanceSession.objects.filter(token=token).exists():
            token = str(uuid.uuid4())

        session = AttendanceSession.objects.create(
            teacher=request.user,
            subject=subject,
            class_year=class_year,
            date=timezone.now().date(),
            expires_at=expiry,
            token=token,
            latitude=latitude,
            longitude=longitude
        )

        # Link to student attendance form
        scan_url = request.build_absolute_uri(f"/student/mark/{session.token}/")

        # Generate QR code
        qr = qrcode.make(scan_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        return render(request, 'core/qr_display.html', {
            'qr_image': qr_image,
            'expires_at': expiry.strftime('%Y-%m-%dT%H:%M:%S'),
            'scan_url': scan_url,
        })

    return redirect('teacher_dashboard')


def export_attendance(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    ws.append(['Class', 'Roll No.', 'Name', 'Subject', 'Date', 'Time'])

    today = date.today()
    sessions_today = AttendanceSession.objects.filter(teacher=request.user, date=today)

    records = AttendanceRecord.objects.select_related(
        'student', 'session__subject', 'student__class_year', 'session'
    ).filter(session__in=sessions_today)

    for record in records:
        ws.append([
            record.student.class_year.name,
            record.student.roll_number,
            record.student.name,
            record.session.subject.name,
            record.session.date.strftime('%Y-%m-%d'),
            record.timestamp.strftime('%H:%M:%S')
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=today_attendance.xlsx'
    wb.save(response)
    return response

def attendance_expired(request):
    return render(request, 'core/attendance_expired.html')

def attendance_success(request):
    return render(request, 'core/attendance_success.html')




# Set up logging
logger = logging.getLogger(__name__)

def mark_attendance(request, token):
    logger.info(f"Received token: {token}")
    logger.info(f"Request method: {request.method}")
    
    try:
        token = str(token).replace("urn:", "").replace("uuid:", "")
        session = get_object_or_404(AttendanceSession, token=UUID(token))
        logger.info(f"Session found: {session}")
        today = timezone.now().date()
        if session.date != today:
            session.date = today
            session.save(update_fields=['date']) 

    except (ValueError, TypeError):
        logger.error("Invalid session token.")
        messages.error(request, "Invalid session token.")
        return redirect('home')
    
                                       
    if is_session_expired(session.expires_at):
        logger.warning("Session has expired.")
        return render(request, 'core/attendance_expired.html')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()

        logger.info(f"Submitted Name: {name}, Submitted Roll Number: {roll_number}")
        
        # Server-side validation
        if not name or not roll_number:
            logger.error("Name or roll number is empty.")
            messages.error(request, "Please fill out all fields.")
            return redirect('mark_attendance', token=token)

        
        if not name or not roll_number:
            logger.error("Name or roll number is empty.")
            messages.error(request, "Please fill out all fields.")
            return redirect('mark_attendance', token=token)

        logger.info(f"Attempting to mark attendance for {name} with roll number {roll_number}")

        # Hardcoded for testing
        # roll_number = "12"  # Uncomment for testing

        try:
            student = Student.objects.get(roll_number=roll_number)
            logger.info(f"Student found: {student}")
        except Student.DoesNotExist:
            logger.error(f"Student with roll number {roll_number} not found.")
            messages.error(request, "Student not found.")
            return redirect('mark_attendance', token=token)

        if AttendanceRecord.objects.filter(session=session, student=student).exists():
            logger.warning("Attendance already marked for this student in this session.")
            messages.warning(request, "Attendance already marked.")
            return redirect('mark_attendance', token=token)
        try:
            AttendanceRecord.objects.create(
                session=session,
                student=student,
                name=student.name,
                roll_number=student.roll_number,
                timestamp=timezone.now()
            )
            logger.info("Attendance marked successfully.")
            messages.success(request, "Attendance marked successfully.")
            return render(request, 'core/attendance_success.html', {
                'session': session,
                'student': student
            })
        except IntegrityError:
                logger.warning("Duplicate attendance entry attempted.")
                messages.warning(request, "Attendance has already been marked for this session.")
                return redirect('mark_attendance', token=token)


    logger.info("Rendering attendance marking form.")
    return render(request, 'core/student_mark_attendance.html', {
        'session': session
    })