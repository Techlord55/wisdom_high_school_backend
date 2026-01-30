# Location: .\apps\students\selectors.py
# ==================== apps/students/selectors.py ====================
from apps.students.models import Student, Attendance, Grade, Assignment


def get_student_by_user(user):
    """Get student by user."""
    return Student.objects.get(user=user)


def get_student_attendance(student, start_date=None, end_date=None):
    """Get student attendance records."""
    queryset = Attendance.objects.filter(student=student)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    return queryset.order_by('-date')


def get_student_grades(student, subject=None, term=None, academic_year=None):
    """Get student grades."""
    queryset = Grade.objects.filter(student=student)
    
    if subject:
        queryset = queryset.filter(subject=subject)
    if term:
        queryset = queryset.filter(term=term)
    if academic_year:
        queryset = queryset.filter(academic_year=academic_year)
    
    return queryset.order_by('-exam_date')


def get_published_assignments(class_level):
    """Get published assignments for a class."""
    return Assignment.objects.filter(
        class_level=class_level,
        is_published=True
    ).order_by('-due_date')

