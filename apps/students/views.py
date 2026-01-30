# Location: .\apps\students\views.py
# ==================== apps/students/views.py ====================
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from apps.students.models import Student, Exam, ExamSubmission, Attendance, Grade, Assignment, AssignmentSubmission
from apps.students.serializers import (
    StudentSerializer, StudentCreateSerializer, ExamSerializer,
    ExamSubmissionSerializer, AttendanceSerializer, GradeSerializer, 
    AssignmentSerializer, AssignmentSubmissionSerializer, 
    BulkAttendanceSerializer, BulkGradeSerializer
)
from apps.students import selectors, services
from apps.common.permissions import IsStudent, IsTeacher, IsTeacherOrAdmin
from apps.common.utils import success_response, error_response


class StudentViewSet(viewsets.ModelViewSet):
    """Student viewset."""
    
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['class_level', 'section', 'education_stream']
    
    def get_serializer_class(self):
        """Use different serializer for create."""
        if self.action == 'create':
            return StudentCreateSerializer
        return StudentSerializer
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            return Student.objects.filter(user=user)
        
        return Student.objects.all()
    
    def perform_create(self, serializer):
        """Create student profile for current user."""
        from django.db import IntegrityError
        
        # Check if student profile already exists
        if hasattr(self.request.user, 'student_profile'):
            raise serializers.ValidationError({
                'detail': 'Student profile already exists for this user.'
            })
        
        try:
            serializer.save(user=self.request.user)
            # Update user role to student
            self.request.user.role = 'student'
            self.request.user.save(update_fields=['role'])
        except IntegrityError:
            raise serializers.ValidationError({
                'detail': 'Student profile already exists for this user.'
            })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current student profile."""
        try:
            student = selectors.get_student_by_user(request.user)
            serializer = self.get_serializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return error_response('Student profile not found', status=404)


class ExamViewSet(viewsets.ModelViewSet):
    """Exam viewset - Admin creates exams with multiple classes/subjects support."""
    
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['exam_type', 'term', 'academic_year', 'is_published']
    
    def get_queryset(self):
        """Filter based on role and teacher assignments."""
        user = self.request.user
        qs = super().get_queryset()
        
        if user.role == 'student':
            # Students see only published exams for their class
            try:
                student = selectors.get_student_by_user(user)
                return qs.filter(
                    Q(classes__contains=[student.class_level]) | Q(classes__contains=['all']),
                    is_published=True
                )
            except Student.DoesNotExist:
                return Exam.objects.none()
        elif user.role == 'teacher':
            # Teachers see exams where their classes/subjects overlap
            teacher = user.teacher_profile
            teacher_classes = set(teacher.classes_assigned or [])
            teacher_subjects = set(teacher.subjects or [])
            
            if not teacher_classes or not teacher_subjects:
                return Exam.objects.none()
            
            # Filter exams where teacher has matching classes AND subjects
            matching_exams = []
            
            for exam in qs.all():
                exam_classes = set(exam.get_applicable_classes())
                exam_subjects = set(exam.get_applicable_subjects())
                
                # Check if teacher's assignments overlap with exam
                if (teacher_classes & exam_classes) and (teacher_subjects & exam_subjects):
                    matching_exams.append(exam.id)
            
            return qs.filter(id__in=matching_exams)
        
        # Admin sees all
        return qs
    
    def perform_create(self, serializer):
        """Set created_by on create."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_exams(self, request):
        """Get exams assigned to current teacher."""
        if request.user.role != 'teacher':
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        exams = self.get_queryset()
        serializer = self.get_serializer(exams, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    """Attendance viewset."""
    
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'date', 'status', 'subject']
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            try:
                student = selectors.get_student_by_user(user)
                return Attendance.objects.filter(student=student)
            except Student.DoesNotExist:
                return Attendance.objects.none()
        
        return Attendance.objects.all()
    
    def get_permissions(self):
        """Custom permissions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance."""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        teacher = None
        if request.user.role == 'teacher':
            teacher = request.user.teacher_profile
        
        count = services.bulk_mark_attendance(
            date=serializer.validated_data['date'],
            subject=serializer.validated_data['subject'],
            records=serializer.validated_data['records'],
            teacher=teacher
        )
        
        return success_response(
            {'count': count},
            f'Attendance marked for {count} students'
        )
    
    @action(detail=False, methods=['get'])
    def my_attendance(self, request):
        """Get current student's attendance."""
        try:
            student = selectors.get_student_by_user(request.user)
            
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            attendance = selectors.get_student_attendance(
                student,
                start_date=start_date,
                end_date=end_date
            )
            
            serializer = self.get_serializer(attendance, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return error_response('Student profile not found', status=404)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get attendance statistics."""
        student_id = request.query_params.get('student_id')
        
        if request.user.role == 'student':
            try:
                student = selectors.get_student_by_user(request.user)
            except Student.DoesNotExist:
                return error_response('Student profile not found', status=404)
        elif student_id:
            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return error_response('Student not found', status=404)
        else:
            return error_response('student_id is required for teachers/admins', status=400)
        
        attendance = Attendance.objects.filter(student=student)
        
        stats = {
            'total': attendance.count(),
            'present': attendance.filter(status='present').count(),
            'absent': attendance.filter(status='absent').count(),
            'late': attendance.filter(status='late').count(),
            'excused': attendance.filter(status='excused').count(),
        }
        
        if stats['total'] > 0:
            stats['attendance_rate'] = (stats['present'] / stats['total']) * 100
        else:
            stats['attendance_rate'] = 0
        
        return Response(stats)


class GradeViewSet(viewsets.ModelViewSet):
    """Grade viewset."""
    
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'exam', 'exam__subject', 'exam__term', 'exam__academic_year']
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            try:
                student = selectors.get_student_by_user(user)
                return Grade.objects.filter(student=student)
            except Student.DoesNotExist:
                return Grade.objects.none()
        
        return Grade.objects.all()
    
    def get_permissions(self):
        """Custom permissions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create grades for an exam."""
        serializer = BulkGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        exam_id = serializer.validated_data['exam_id']
        grade_data = serializer.validated_data['grades']
        
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return error_response('Exam not found', status=404)
        
        teacher = None
        if request.user.role == 'teacher':
            teacher = request.user.teacher_profile
        
        grades = []
        for data in grade_data:
            student = Student.objects.get(id=data['student_id'])
            
            # Update or create grade
            grade, created = Grade.objects.update_or_create(
                student=student,
                exam=exam,
                defaults={
                    'teacher': teacher,
                    'marks_obtained': data['marks_obtained'],
                    'remarks': data.get('remarks', '')
                }
            )
            grades.append(grade)
        
        return success_response(
            GradeSerializer(grades, many=True).data,
            f'{len(grades)} grades saved successfully'
        )
    
    @action(detail=False, methods=['get'])
    def my_grades(self, request):
        """Get current student's grades."""
        try:
            student = selectors.get_student_by_user(request.user)
            
            term = request.query_params.get('term')
            academic_year = request.query_params.get('academic_year')
            subject = request.query_params.get('subject')
            
            grades = Grade.objects.filter(student=student)
            
            if term:
                grades = grades.filter(exam__term=term)
            if academic_year:
                grades = grades.filter(exam__academic_year=academic_year)
            if subject:
                grades = grades.filter(exam__subject=subject)
            
            serializer = self.get_serializer(grades, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return error_response('Student profile not found', status=404)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get grade statistics."""
        student_id = request.query_params.get('student_id')
        academic_year = request.query_params.get('academic_year')
        term = request.query_params.get('term')
        
        if request.user.role == 'student':
            # Students can only see their own stats
            try:
                student = selectors.get_student_by_user(request.user)
            except Student.DoesNotExist:
                return error_response('Student profile not found', status=404)
            
            grades = Grade.objects.filter(student=student)
            
        elif request.user.role in ['teacher', 'admin']:
            # Teachers/admins can request specific student stats or overall stats
            if student_id:
                # Get stats for a specific student
                try:
                    student = Student.objects.get(id=student_id)
                except Student.DoesNotExist:
                    return error_response('Student not found', status=404)
                
                grades = Grade.objects.filter(student=student)
            else:
                # Return overall statistics for all students
                grades = Grade.objects.all()
        else:
            return error_response('Unauthorized', status=403)
        
        # Apply filters
        if academic_year:
            grades = grades.filter(exam__academic_year=academic_year)
        if term:
            grades = grades.filter(exam__term=term)
        
        if not grades.exists():
            return Response({
                'total_grades': 0,
                'average_grade': 0,
                'by_subject': {},
                'overall': {
                    'average': 0,
                    'total_exams': 0,
                    'highest': 0,
                    'lowest': 0
                }
            })
        
        # Calculate statistics by subject
        by_subject = {}
        for grade in grades:
            subject = grade.exam.subject
            if subject not in by_subject:
                by_subject[subject] = {
                    'grades': [],
                    'average': 0,
                    'highest': 0,
                    'lowest': 100
                }
            
            percentage = float(grade.percentage)
            by_subject[subject]['grades'].append(percentage)
        
        for subject, data in by_subject.items():
            grades_list = data['grades']
            data['average'] = sum(grades_list) / len(grades_list)
            data['highest'] = max(grades_list)
            data['lowest'] = min(grades_list)
            del data['grades']
        
        # Overall statistics
        all_percentages = [float(g.percentage) for g in grades]
        overall = {
            'average': sum(all_percentages) / len(all_percentages),
            'total_exams': len(all_percentages),
            'highest': max(all_percentages),
            'lowest': min(all_percentages)
        }
        
        return Response({
            'total_grades': overall['total_exams'],
            'average_grade': overall['average'],
            'by_subject': by_subject,
            'overall': overall
        })


class AssignmentViewSet(viewsets.ModelViewSet):
    """Assignment viewset."""
    
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['subject', 'class_level', 'is_published']
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            try:
                student = selectors.get_student_by_user(user)
                return selectors.get_published_assignments(student.class_level)
            except Student.DoesNotExist:
                return Assignment.objects.none()
        elif user.role == 'teacher':
            return Assignment.objects.filter(teacher=user.teacher_profile)
        
        return Assignment.objects.all()
    
    def get_permissions(self):
        """Custom permissions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Set teacher on create."""
        if self.request.user.role == 'teacher':
            serializer.save(teacher=self.request.user.teacher_profile)
        else:
            serializer.save()


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    """Assignment submission viewset."""
    
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['assignment', 'student', 'status']
    
    def get_queryset(self):
        """Filter based on role."""
        user = self.request.user
        
        if user.role == 'student':
            try:
                student = selectors.get_student_by_user(user)
                return AssignmentSubmission.objects.filter(student=student)
            except Student.DoesNotExist:
                return AssignmentSubmission.objects.none()
        
        # Teachers see submissions for their assignments
        if user.role == 'teacher':
            return AssignmentSubmission.objects.filter(
                assignment__teacher=user.teacher_profile
            )
        
        return AssignmentSubmission.objects.all()
    
    def perform_create(self, serializer):
        """Set student on create."""
        try:
            student = selectors.get_student_by_user(self.request.user)
            serializer.save(student=student)
        except Student.DoesNotExist:
            raise ValueError('Student profile not found')
    
    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Grade a submission."""
        submission = self.get_object()
        
        marks = request.data.get('marks_obtained')
        feedback = request.data.get('feedback')
        
        if marks is None:
            return error_response('Marks are required')
        
        graded_submission = services.grade_submission(
            submission_id=submission.id,
            marks_obtained=marks,
            feedback=feedback
        )
        
        serializer = self.get_serializer(graded_submission)
        return success_response(serializer.data, 'Submission graded successfully')


# API views for class levels and subjects
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_class_levels(request):
    """Get all available class levels in Cameroon education system."""
    class_levels = [
        {'id': 'Form 1', 'name': 'Form 1'},
        {'id': 'Form 2', 'name': 'Form 2'},
        {'id': 'Form 3', 'name': 'Form 3'},
        {'id': 'Form 4', 'name': 'Form 4'},
        {'id': 'Form 5', 'name': 'Form 5'},
        {'id': 'Lower Sixth', 'name': 'Lower Sixth'},
        {'id': 'Upper Sixth', 'name': 'Upper Sixth'},
    ]
    return Response({'results': class_levels})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subjects(request):
    """Get all available subjects."""
    # Common subjects across all classes
    subjects = [
        {'id': 'Mathematics', 'name': 'Mathematics'},
        {'id': 'English Language', 'name': 'English Language'},
        {'id': 'French', 'name': 'French'},
        {'id': 'Physics', 'name': 'Physics'},
        {'id': 'Chemistry', 'name': 'Chemistry'},
        {'id': 'Biology', 'name': 'Biology'},
        {'id': 'History', 'name': 'History'},
        {'id': 'Geography', 'name': 'Geography'},
        {'id': 'Literature', 'name': 'Literature'},
        {'id': 'Economics', 'name': 'Economics'},
        {'id': 'Computer Science', 'name': 'Computer Science'},
        {'id': 'ICT', 'name': 'ICT'},
        {'id': 'Religious Studies', 'name': 'Religious Studies'},
        {'id': 'Physical Education', 'name': 'Physical Education'},
        {'id': 'Citizenship', 'name': 'Citizenship'},
        {'id': 'Music', 'name': 'Music'},
        {'id': 'Art', 'name': 'Art'},
        {'id': 'Additional Mathematics', 'name': 'Additional Mathematics'},
        {'id': 'Further Mathematics', 'name': 'Further Mathematics'},
        {'id': 'Accounting', 'name': 'Accounting'},
        {'id': 'Business Studies', 'name': 'Business Studies'},
        {'id': 'Commerce', 'name': 'Commerce'},
    ]
    return Response({'results': subjects})
