# Location: .\apps\students\serializers.py
# ==================== apps/students/serializers.py ====================
from rest_framework import serializers
from apps.students.models import (
    Student, Exam, ExamSubmission, Attendance, Grade, 
    Assignment, AssignmentSubmission
)
from apps.users.serializers import UserSerializer


class StudentSerializer(serializers.ModelSerializer):
    """Student serializer with Cameroon education system support."""
    
    user = UserSerializer(read_only=True)
    display_stream = serializers.ReadOnlyField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'student_id', 'class_level', 'section',
            'education_stream', 'specialization', 'art_or_science',
            'a_level_stream', 'subjects', 'display_stream',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student_id', 'created_at', 'updated_at', 'display_stream']


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating student profiles."""
    
    class Meta:
        model = Student
        fields = [
            'class_level', 'section', 'education_stream',
            'specialization', 'art_or_science', 'a_level_stream', 'subjects'
        ]
    
    def validate(self, data):
        """Validate student data based on stream."""
        education_stream = data.get('education_stream')
        
        # Validate Technical stream
        if education_stream == 'technical':
            if not data.get('specialization'):
                raise serializers.ValidationError({
                    'specialization': 'Specialization is required for Technical stream.'
                })
        
        # Validate Commercial stream
        if education_stream == 'commercial':
            if not data.get('specialization'):
                raise serializers.ValidationError({
                    'specialization': 'Specialization is required for Commercial stream.'
                })
        
        # Validate Grammar stream
        if education_stream == 'grammar':
            class_level = data.get('class_level', '')
            
            # Form 4/5 must have art_or_science
            if class_level in ['Form 4', 'Form 5']:
                if not data.get('art_or_science'):
                    raise serializers.ValidationError({
                        'art_or_science': 'Art or Science selection is required for Form 4 and Form 5.'
                    })
            
            # A-Level must have a_level_stream
            if class_level in ['Lower Sixth', 'Upper Sixth']:
                if not data.get('a_level_stream'):
                    raise serializers.ValidationError({
                        'a_level_stream': 'A-Level stream is required for Lower Sixth and Upper Sixth.'
                    })
        
        return data


class ExamSerializer(serializers.ModelSerializer):
    """Updated Exam serializer with multiple classes and subjects support."""
    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    submission_count = serializers.SerializerMethodField()
    grade_count = serializers.SerializerMethodField()
    applicable_classes = serializers.SerializerMethodField()
    applicable_subjects = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = [
            'id', 'exam_name', 'exam_type', 'classes', 'subjects',
            'total_marks', 'term', 'academic_year', 'start_date', 'end_date',
            'instructions', 'is_published', 'created_by', 'created_by_name',
            'submission_count', 'grade_count', 'applicable_classes', 
            'applicable_subjects', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_submission_count(self, obj):
        return obj.submissions.count()
    
    def get_grade_count(self, obj):
        return obj.grades.count()
    
    def get_applicable_classes(self, obj):
        return obj.get_applicable_classes()
    
    def get_applicable_subjects(self, obj):
        return obj.get_applicable_subjects()
    
    def validate(self, data):
        """Validate exam data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        # Ensure at least one class is selected
        classes = data.get('classes', [])
        if not classes:
            raise serializers.ValidationError({
                'classes': 'At least one class must be selected.'
            })
        
        # Ensure at least one subject is selected
        subjects = data.get('subjects', [])
        if not subjects:
            raise serializers.ValidationError({
                'subjects': 'At least one subject must be selected.'
            })
        
        return data


class ExamSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for exam submissions (questions and grades)."""
    
    exam_name = serializers.CharField(source='exam.exam_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.full_name', read_only=True)
    teacher_id = serializers.CharField(source='teacher.teacher_id', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSubmission
        fields = [
            'id', 'exam', 'exam_name', 'teacher', 'teacher_name', 'teacher_id',
            'class_level', 'subject', 'submission_type', 'file', 'file_url',
            'file_name', 'status', 'remarks', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
    
    def get_file_name(self, obj):
        """Get filename from file field."""
        if obj.file:
            try:
                import os
                return os.path.basename(obj.file.name)
            except Exception:
                return None
        return None
    
    def get_file_url(self, obj):
        """Get file URL from storage backend."""
        if obj.file:
            try:
                return obj.file.url
            except Exception:
                return None
        return None
    
    def validate(self, data):
        """Validate submission data."""
        exam = data.get('exam')
        class_level = data.get('class_level')
        subject = data.get('subject')
        teacher = self.context['request'].user.teacher_profile
        
        # Check if teacher is assigned to this exam
        if not exam.is_teacher_assigned(teacher):
            raise serializers.ValidationError(
                'You are not assigned to teach this exam.'
            )
        
        # Check if class is in exam's classes
        applicable_classes = exam.get_applicable_classes()
        if class_level not in applicable_classes:
            raise serializers.ValidationError({
                'class_level': f'This class is not included in the exam. Applicable classes: {applicable_classes}'
            })
        
        # Check if subject is in exam's subjects
        applicable_subjects = exam.get_applicable_subjects()
        if subject not in applicable_subjects:
            raise serializers.ValidationError({
                'subject': f'This subject is not included in the exam. Applicable subjects: {applicable_subjects}'
            })
        
        return data


class AttendanceSerializer(serializers.ModelSerializer):
    """Attendance serializer."""
    
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'student_id', 'date',
            'status', 'teacher', 'subject', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BulkAttendanceSerializer(serializers.Serializer):
    """Bulk attendance marking serializer."""
    
    date = serializers.DateField()
    subject = serializers.CharField(max_length=100)
    records = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )


class GradeSerializer(serializers.ModelSerializer):
    """Updated Grade serializer with class and subject fields."""
    
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    exam_name = serializers.CharField(source='exam.exam_name', read_only=True)
    exam_type = serializers.CharField(source='exam.exam_type', read_only=True)
    total_marks = serializers.DecimalField(source='exam.total_marks', max_digits=5, decimal_places=2, read_only=True)
    term = serializers.CharField(source='exam.term', read_only=True)
    academic_year = serializers.CharField(source='exam.academic_year', read_only=True)
    exam_start_date = serializers.DateField(source='exam.start_date', read_only=True)
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'student_id', 'exam', 'exam_name',
            'class_level', 'subject', 'exam_type', 'teacher', 'marks_obtained', 
            'total_marks', 'percentage', 'grade_letter', 'term', 'academic_year', 
            'exam_start_date', 'remarks', 'created_at'
        ]
        read_only_fields = ['id', 'percentage', 'grade_letter', 'created_at']


class BulkGradeSerializer(serializers.Serializer):
    """Bulk grade entry serializer."""
    
    exam_id = serializers.IntegerField()
    class_level = serializers.CharField()
    subject = serializers.CharField()
    grades = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate(self, data):
        """Validate bulk grade data."""
        exam_id = data.get('exam_id')
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise serializers.ValidationError({'exam_id': 'Exam not found.'})
        
        # Validate grades
        grades = data.get('grades', [])
        for grade_data in grades:
            marks = grade_data.get('marks_obtained', 0)
            if marks < 0 or marks > exam.total_marks:
                raise serializers.ValidationError({
                    'grades': f'Marks must be between 0 and {exam.total_marks}'
                })
        
        return data


class AssignmentSerializer(serializers.ModelSerializer):
    """Assignment serializer."""
    
    teacher_name = serializers.CharField(source='teacher.user.full_name', read_only=True)
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'teacher', 'teacher_name', 'title', 'description',
            'subject', 'class_level', 'due_date', 'total_marks',
            'attachment', 'is_published', 'submission_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_submission_count(self, obj):
        return obj.submissions.count()


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """Assignment submission serializer."""
    
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'assignment_title', 'student',
            'student_name', 'student_id', 'submission_text',
            'attachment', 'marks_obtained', 'feedback',
            'submitted_at', 'graded_at', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at']
