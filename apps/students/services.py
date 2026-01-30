# Location: .\apps\students\services.py
# ==================== apps/students/services.py ====================
from apps.students.models import Student, Attendance, Grade, AssignmentSubmission
from apps.users.models import User
from django.utils import timezone


def create_student_profile(user: User, class_level: str, section: str) -> Student:
    """Create student profile."""
    student = Student.objects.create(
        user=user,
        class_level=class_level,
        section=section
    )
    return student


def mark_attendance(student: Student, date, status: str, subject: str, teacher=None, notes=None):
    """Mark student attendance."""
    attendance, created = Attendance.objects.update_or_create(
        student=student,
        date=date,
        subject=subject,
        defaults={
            'status': status,
            'teacher': teacher,
            'notes': notes
        }
    )
    return attendance


def bulk_mark_attendance(date, subject, records: list, teacher=None):
    """Bulk mark attendance."""
    attendance_objects = []
    
    for record in records:
        student = Student.objects.get(id=record['student_id'])
        attendance_objects.append(
            Attendance(
                student=student,
                date=date,
                status=record['status'],
                subject=subject,
                teacher=teacher,
                notes=record.get('notes')
            )
        )
    
    # Use update_or_create logic
    created_count = 0
    for obj in attendance_objects:
        _, created = Attendance.objects.update_or_create(
            student=obj.student,
            date=obj.date,
            subject=obj.subject,
            defaults={
                'status': obj.status,
                'teacher': obj.teacher,
                'notes': obj.notes
            }
        )
        if created:
            created_count += 1
    
    return created_count


def create_grade(student: Student, teacher, subject: str, exam_type: str,
                exam_name: str, marks_obtained: float, total_marks: float,
                academic_year: str, term: str, exam_date=None, remarks=None):
    """Create grade entry."""
    grade = Grade.objects.create(
        student=student,
        teacher=teacher,
        subject=subject,
        exam_type=exam_type,
        exam_name=exam_name,
        marks_obtained=marks_obtained,
        total_marks=total_marks,
        academic_year=academic_year,
        term=term,
        exam_date=exam_date,
        remarks=remarks
    )
    return grade


def submit_assignment(assignment, student: Student, submission_text=None, attachment_url=None):
    """Submit assignment."""
    submission, created = AssignmentSubmission.objects.update_or_create(
        assignment=assignment,
        student=student,
        defaults={
            'submission_text': submission_text,
            'attachment_url': attachment_url,
            'status': 'submitted',
            'submitted_at': timezone.now()
        }
    )
    return submission


def grade_submission(submission_id, marks_obtained: float, feedback=None):
    """Grade assignment submission."""
    submission = AssignmentSubmission.objects.get(id=submission_id)
    submission.marks_obtained = marks_obtained
    submission.feedback = feedback
    submission.status = 'graded'
    submission.graded_at = timezone.now()
    submission.save()
    
    return submission