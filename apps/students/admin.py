from django.contrib import admin
from apps.students.models import Student, Attendance, Grade, Assignment, AssignmentSubmission, Exam


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'user', 'class_level', 'section', 'created_at']
    list_filter = ['class_level', 'section']
    search_fields = ['student_id', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_name', 'get_subjects', 'get_classes', 'exam_type', 'term', 
                   'academic_year', 'start_date', 'end_date', 'total_marks', 'is_published']
    list_filter = ['exam_type', 'term', 'academic_year', 'is_published']
    search_fields = ['exam_name']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']
    
    def get_subjects(self, obj):
        """Display subjects in a readable format."""
        if 'all' in obj.subjects:
            return 'All Subjects'
        return ', '.join(obj.subjects[:3]) + ('...' if len(obj.subjects) > 3 else '')
    get_subjects.short_description = 'Subjects'
    
    def get_classes(self, obj):
        """Display classes in a readable format."""
        if 'all' in obj.classes:
            return 'All Classes'
        return ', '.join(obj.classes[:3]) + ('...' if len(obj.classes) > 3 else '')
    get_classes.short_description = 'Classes'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'subject', 'teacher']
    list_filter = ['status', 'date', 'subject']
    search_fields = ['student__student_id', 'student__user__first_name']
    date_hierarchy = 'date'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_exam_name', 'subject', 'class_level', 'marks_obtained', 
                   'get_total_marks', 'percentage', 'grade_letter', 'get_start_date']
    list_filter = ['subject', 'class_level', 'exam__exam_type', 'exam__term', 'exam__academic_year']
    search_fields = ['student__student_id', 'exam__exam_name', 'student__user__first_name', 'subject']
    readonly_fields = ['percentage', 'grade_letter']
    
    def get_exam_name(self, obj):
        return obj.exam.exam_name
    get_exam_name.short_description = 'Exam'
    get_exam_name.admin_order_field = 'exam__exam_name'
    
    def get_total_marks(self, obj):
        return obj.exam.total_marks
    get_total_marks.short_description = 'Total Marks'
    get_total_marks.admin_order_field = 'exam__total_marks'
    
    def get_start_date(self, obj):
        return obj.exam.start_date
    get_start_date.short_description = 'Exam Date'
    get_start_date.admin_order_field = 'exam__start_date'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_level', 'teacher', 
                   'due_date', 'is_published', 'created_at']
    list_filter = ['subject', 'class_level', 'is_published']
    search_fields = ['title', 'subject']
    date_hierarchy = 'due_date'


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'status', 'marks_obtained', 
                   'submitted_at', 'graded_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['assignment__title', 'student__student_id']
