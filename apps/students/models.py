# Location: .\apps\students\models.py
# ==================== apps/students/models.py ====================
from django.db import models
from apps.common.models import TimeStampedModel
from apps.users.models import User


class Student(TimeStampedModel):
    """Student profile model with Cameroon education system support."""
    
    # Education Stream Choices (Cameroon MINESEC)
    STREAM_CHOICES = [
        ('grammar', 'Grammar'),
        ('technical', 'Technical'),
        ('commercial', 'Commercial'),
    ]
    
    # Art or Science for Form 4/5
    ART_OR_SCIENCE_CHOICES = [
        ('arts', 'Arts'),
        ('science', 'Science'),
    ]
    
    # A-Level Streams
    A_LEVEL_STREAM_CHOICES = [
        ('A1', 'A1 - Arts with Languages'),
        ('A2', 'A2 - Arts with Social Sciences'),
        ('A3', 'A3 - Arts with Mathematics'),
        ('A4', 'A4 - Arts with Science'),
        ('S1', 'S1 - Physical Sciences'),
        ('S2', 'S2 - Biological Sciences'),
        ('S3', 'S3 - Mathematics & Computer Science'),
        ('S4', 'S4 - Engineering Sciences'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Basic Info
    class_level = models.CharField(max_length=50)  # Form 1, Form 2, ..., Lower Sixth, Upper Sixth
    section = models.CharField(max_length=20, choices=STREAM_CHOICES, default='grammar')
    
    # Education Stream & Specialization
    education_stream = models.CharField(max_length=20, choices=STREAM_CHOICES, blank=True, null=True)
    
    # For Technical & Commercial students
    specialization = models.CharField(max_length=100, blank=True, null=True)
    # Technical: Electrical Power System, Building & Construction, Motor Mechanic, etc.
    # Commercial: Accounting, Bespoke Tailoring, Secretarial Studies, etc.
    
    # For Grammar students - Form 4/5
    art_or_science = models.CharField(max_length=10, choices=ART_OR_SCIENCE_CHOICES, blank=True, null=True)
    
    # For Grammar students - A-Level (Lower/Upper Sixth)
    a_level_stream = models.CharField(max_length=5, choices=A_LEVEL_STREAM_CHOICES, blank=True, null=True)
    
    # Subjects
    subjects = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['student_id']
    
    def __str__(self):
        return f"{self.student_id} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.student_id:
            # Auto-generate student ID: WHS + Year + Sequential Number
            import datetime
            year = str(datetime.datetime.now().year)[-2:]
            last_student = Student.objects.filter(
                student_id__startswith=f'WHS{year}'
            ).order_by('student_id').last()
            
            if last_student:
                last_num = int(last_student.student_id[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.student_id = f'WHS{year}{str(new_num).zfill(4)}'
        
        super().save(*args, **kwargs)
    
    @property
    def display_stream(self):
        """Return a human-readable stream description."""
        if self.education_stream == 'technical' and self.specialization:
            return f"Technical - {self.specialization}"
        elif self.education_stream == 'commercial' and self.specialization:
            return f"Commercial - {self.specialization}"
        elif self.education_stream == 'grammar':
            if self.a_level_stream:
                return f"Grammar - A-Level {self.a_level_stream}"
            elif self.art_or_science:
                return f"Grammar - {self.art_or_science.title()}"
            else:
                return "Grammar"
        return self.section.title()


class Exam(TimeStampedModel):
    """Exam/Test model - Created by Admin, graded by Teachers.
    
    Updated to support:
    - Multiple classes (can select specific classes or all)
    - Multiple subjects (can select specific subjects or all)
    - Start and end dates
    - Question paper uploads by teachers
    - Grade sheet uploads by teachers
    """
    
    EXAM_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('test', 'Class Test'),
        ('midterm', 'Mid-Term Exam'),
        ('final', 'Final Exam'),
        ('mock', 'Mock Exam'),
    ]
    
    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]
    
    # Exam details
    exam_name = models.CharField(max_length=255)  # e.g., "Mid-Term Mathematics Exam"
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    
    # Multiple classes and subjects - stored as JSON arrays
    # e.g., ["Form 1", "Form 2"] or ["all"] for all classes
    classes = models.JSONField(default=list, help_text="List of class levels or ['all']")
    
    # e.g., ["Mathematics", "English"] or ["all"] for all subjects
    subjects = models.JSONField(default=list, help_text="List of subjects or ['all']")
    
    # Scoring
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    
    # Timing - Now with start and end dates
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=20)
    start_date = models.DateField(help_text="Exam start date")
    end_date = models.DateField(help_text="Exam end date")
    
    # Additional info
    instructions = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=True)  # If students can see it
    
    # Admin who created it
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_exams')
    
    class Meta:
        db_table = 'exams'
        ordering = ['-start_date', '-created_at']
    
    def __str__(self):
        classes_str = "All Classes" if "all" in self.classes else ", ".join(self.classes[:2])
        subjects_str = "All Subjects" if "all" in self.subjects else ", ".join(self.subjects[:2])
        return f"{self.exam_name} - {subjects_str} - {classes_str}"
    
    def get_applicable_classes(self):
        """Get list of classes this exam applies to."""
        if "all" in self.classes:
            # Return all class levels from Form 1 to Upper Sixth
            return [
                "Form 1", "Form 2", "Form 3", "Form 4", "Form 5",
                "Lower Sixth", "Upper Sixth"
            ]
        return self.classes
    
    def get_applicable_subjects(self):
        """Get list of subjects this exam applies to."""
        if "all" in self.subjects:
            # You might want to fetch this from a Subject model or settings
            # For now, return common subjects
            return [
                "Mathematics", "English", "French", "Physics", "Chemistry",
                "Biology", "History", "Geography", "Literature"
            ]
        return self.subjects
    
    def is_teacher_assigned(self, teacher):
        """Check if a teacher is assigned to this exam."""
        from apps.teachers.models import Teacher
        
        if not isinstance(teacher, Teacher):
            return False
        
        # Check if teacher's assigned classes overlap with exam classes
        teacher_classes = set(teacher.classes_assigned)
        exam_classes = set(self.get_applicable_classes())
        
        # Check if teacher's subjects overlap with exam subjects
        teacher_subjects = set(teacher.subjects)
        exam_subjects = set(self.get_applicable_subjects())
        
        # Teacher is assigned if they have at least one matching class AND one matching subject
        return bool(teacher_classes & exam_classes) and bool(teacher_subjects & exam_subjects)


class ExamSubmission(TimeStampedModel):
    """Track teacher submissions for exams (question papers and grade sheets)."""
    
    SUBMISSION_TYPE_CHOICES = [
        ('questions', 'Question Paper'),
        ('grades', 'Grade Sheet'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='exam_submissions')
    
    # What class and subject is this submission for
    class_level = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    
    # Submission details
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_TYPE_CHOICES)
    file = models.FileField(
        upload_to='exam_submissions/',
        null=True,
        blank=True
    )
    
    @property
    def file_name(self):
        """Extract filename from file field."""
        if self.file:
            import os
            return os.path.basename(self.file.name)
        return 'download'
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    
    # Approval
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'exam_submissions'
        unique_together = ['exam', 'teacher', 'class_level', 'subject', 'submission_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.teacher.teacher_id} - {self.exam.exam_name} - {self.submission_type} - {self.class_level} - {self.subject}"


class Attendance(TimeStampedModel):
    """Attendance tracking model."""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['student', 'date', 'subject']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.date} - {self.status}"


class Grade(TimeStampedModel):
    """Grade/Marks tracking model - Links to Exam."""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Specific class and subject for this grade
    class_level = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    
    # Marks
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, editable=False, default=0)
    grade_letter = models.CharField(max_length=3, blank=True)
    
    # Additional
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'grades'
        unique_together = ['student', 'exam', 'subject']
        ordering = ['-exam__start_date', '-created_at']
    
    def __str__(self):
        return f"{self.student.student_id} - {self.exam.exam_name} - {self.subject} - {self.marks_obtained}/{self.exam.total_marks}"
    
    def save(self, *args, **kwargs):
        # Calculate percentage
        if self.exam.total_marks > 0:
            self.percentage = (self.marks_obtained / self.exam.total_marks) * 100
        
        # Calculate grade letter
        self.grade_letter = self._calculate_grade_letter()
        
        super().save(*args, **kwargs)
    
    def _calculate_grade_letter(self):
        """Calculate grade letter based on percentage."""
        if self.percentage >= 90:
            return 'A+'
        elif self.percentage >= 85:
            return 'A'
        elif self.percentage >= 80:
            return 'A-'
        elif self.percentage >= 75:
            return 'B+'
        elif self.percentage >= 70:
            return 'B'
        elif self.percentage >= 65:
            return 'B-'
        elif self.percentage >= 60:
            return 'C+'
        elif self.percentage >= 55:
            return 'C'
        elif self.percentage >= 50:
            return 'C-'
        elif self.percentage >= 45:
            return 'D'
        else:
            return 'F'


class Assignment(TimeStampedModel):
    """Assignment model."""
    
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=100)
    class_level = models.CharField(max_length=50)
    due_date = models.DateTimeField()
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    attachment = models.FileField(
        upload_to='assignments/',
        null=True,
        blank=True
    )
    is_published = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'assignments'
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.title} - {self.subject}"


class AssignmentSubmission(TimeStampedModel):
    """Assignment submission model."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_text = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to='assignment_submissions/',
        null=True,
        blank=True
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        db_table = 'assignment_submissions'
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.assignment.title} - {self.student.student_id}"
