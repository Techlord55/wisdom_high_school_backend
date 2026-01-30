from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, FileResponse
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import transaction
import os
import logging

from .models import ExamSubmission, Exam, Student
from .serializers import ExamSubmissionSerializer, ExamSerializer

# Configure logging instead of print statements
logger = logging.getLogger(__name__)


class ExamSubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing exam submissions."""
    queryset = ExamSubmission.objects.select_related(
        'exam', 'teacher__user', 'reviewed_by'
    ).all()
    serializer_class = ExamSubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.role == 'admin':
            return self.queryset
        elif user.role == 'teacher':
            return self.queryset.filter(teacher__user=user)
        
        return ExamSubmission.objects.none()
    
    @action(detail=False, methods=['get'], url_path='teacher_assignments')
    def teacher_assignments(self, request):
        """
        Get teacher's assigned classes and subjects.
        Returns the classes and subjects that the teacher is assigned to teach.
        """
        user = request.user
        
        if user.role != 'teacher':
            return Response(
                {'error': 'Only teachers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            teacher = user.teacher_profile
            teacher_classes = teacher.classes_assigned or []
            teacher_subjects = teacher.subjects or []
            
            logger.info(
                f"Teacher assignments retrieved - Teacher: {teacher.teacher_id}, "
                f"Classes: {teacher_classes}, Subjects: {teacher_subjects}"
            )
            
            return Response({
                'classes': teacher_classes,
                'subjects': teacher_subjects
            }, status=status.HTTP_200_OK)
            
        except AttributeError:
            logger.error(f"Teacher profile not found for user {user.id}")
            return Response(
                {'error': 'Teacher profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error fetching teacher assignments: {str(e)}")
            return Response(
                {'error': 'Error fetching assignments'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='upload_questions')
    @transaction.atomic
    def upload_questions(self, request):
        """Upload question paper for an exam."""
        user = request.user
        
        if user.role != 'teacher':
            return Response(
                {'error': 'Only teachers can upload questions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            teacher = user.teacher_profile
        except AttributeError:
            return Response(
                {'error': 'Teacher profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate required fields
        exam_id = request.data.get('exam_id')
        class_level = request.data.get('class_level')
        subject = request.data.get('subject')
        file = request.FILES.get('file')
        
        if not all([exam_id, class_level, subject, file]):
            return Response(
                {'error': 'Missing required fields: exam_id, class_level, subject, file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (10MB limit)
        max_file_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_file_size:
            return Response(
                {'error': 'File size exceeds 10MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exam = Exam.objects.get(id=exam_id)
            
            logger.info(
                f"Question upload - Teacher: {teacher.teacher_id}, Exam: {exam.exam_name}, "
                f"Class: {class_level}, Subject: {subject}, File: {file.name}"
            )
            
            # Create or update submission
            submission, created = ExamSubmission.objects.update_or_create(
                exam=exam,
                teacher=teacher,
                class_level=class_level,
                subject=subject,
                submission_type='questions',
                defaults={
                    'file': file,
                    'status': 'submitted'
                }
            )
            
            logger.info(f"Submission {'created' if created else 'updated'}: {submission.id}")
            
            serializer = ExamSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exam.DoesNotExist:
            return Response(
                {'error': 'Exam not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error uploading questions: {str(e)}")
            return Response(
                {'error': 'Failed to upload questions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='upload_grades')
    @transaction.atomic
    def upload_grades(self, request):
        """Upload grade sheet for an exam."""
        user = request.user
        
        if user.role != 'teacher':
            return Response(
                {'error': 'Only teachers can upload grades'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            teacher = user.teacher_profile
        except AttributeError:
            return Response(
                {'error': 'Teacher profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate required fields
        exam_id = request.data.get('exam_id')
        class_level = request.data.get('class_level')
        subject = request.data.get('subject')
        file = request.FILES.get('file')
        
        if not all([exam_id, class_level, subject, file]):
            return Response(
                {'error': 'Missing required fields: exam_id, class_level, subject, file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (5MB limit for CSV/Excel)
        max_file_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_file_size:
            return Response(
                {'error': 'File size exceeds 5MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_extensions = ['.csv', '.xls', '.xlsx']
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exam = Exam.objects.get(id=exam_id)
            
            logger.info(
                f"Grade upload - Teacher: {teacher.teacher_id}, Exam: {exam.exam_name}, "
                f"Class: {class_level}, Subject: {subject}, File: {file.name}"
            )
            
            # Create or update submission
            submission, created = ExamSubmission.objects.update_or_create(
                exam=exam,
                teacher=teacher,
                class_level=class_level,
                subject=subject,
                submission_type='grades',
                defaults={
                    'file': file,
                    'status': 'submitted'
                }
            )
            
            logger.info(f"Submission {'created' if created else 'updated'}: {submission.id}")
            
            serializer = ExamSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exam.DoesNotExist:
            return Response(
                {'error': 'Exam not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error uploading grades: {str(e)}")
            return Response(
                {'error': 'Failed to upload grades'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='download_template')
    def download_template(self, request):
        """Download grade sheet template with student list."""
        user = request.user
        
        if user.role != 'teacher':
            return Response(
                {'error': 'Only teachers can download templates'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate required parameters
        exam_id = request.query_params.get('exam_id')
        class_level = request.query_params.get('class_level')
        subject = request.query_params.get('subject')
        
        if not all([exam_id, class_level, subject]):
            return Response(
                {'error': 'Missing required parameters: exam_id, class_level, subject'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import csv
            from io import StringIO
            
            exam = Exam.objects.get(id=exam_id)
            
            # Get students in the class - optimized query
            students = Student.objects.filter(
                class_level=class_level
            ).select_related('user').order_by('student_id')
            
            logger.info(
                f"Template download - Exam: {exam.exam_name}, Class: {class_level}, "
                f"Subject: {subject}, Students: {students.count()}"
            )
            
            # Create CSV in memory
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Student ID',
                'Full Name',
                'Class',
                'Subject',
                f'Marks (out of {exam.total_marks})',
                'Remarks (Optional)'
            ])
            
            # Student rows
            for student in students:
                writer.writerow([
                    student.student_id,
                    student.user.full_name,
                    class_level,
                    subject,
                    '',  # Empty marks field
                    ''   # Empty remarks field
                ])
            
            # Create response
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            # Sanitize filename to prevent injection
            safe_class = class_level.replace(' ', '_')
            safe_subject = subject.replace(' ', '_')
            response['Content-Disposition'] = f'attachment; filename="Grade_Template_{safe_class}_{safe_subject}.csv"'
            
            return response
            
        except Exam.DoesNotExist:
            return Response(
                {'error': 'Exam not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error generating template: {str(e)}")
            return Response(
                {'error': 'Failed to generate template'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Download a submitted file from storage."""
        submission = self.get_object()
        
        # Permission check
        user = request.user
        if user.role == 'teacher':
            if submission.teacher.user != user:
                return Response(
                    {'error': 'You can only download your own submissions'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif user.role != 'admin':
            return Response(
                {'error': 'Only teachers and admins can download submissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not submission.file:
            return Response(
                {'error': 'No file attached'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            file_path = submission.file.name
            
            # Security: Validate file path to prevent directory traversal
            if '..' in file_path or file_path.startswith('/'):
                logger.warning(f"Suspicious file path detected: {file_path}")
                return Response(
                    {'error': 'Invalid file path'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if file exists
            if not default_storage.exists(file_path):
                logger.error(f"File not found in storage: {file_path}")
                return Response(
                    {'error': 'File not found in storage'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Open file from storage
            file_obj = default_storage.open(file_path, 'rb')
            filename = os.path.basename(file_path)
            
            # Determine content type based on extension
            content_type_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.csv': 'text/csv',
            }
            
            file_ext = os.path.splitext(filename)[1].lower()
            content_type = content_type_map.get(file_ext, 'application/octet-stream')
            
            # Create response
            response = FileResponse(file_obj, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            logger.info(f"File downloaded - Submission: {pk}, User: {user.id}")
            
            return response
            
        except Exception as e:
            logger.exception(f"Error downloading file: {str(e)}")
            return Response(
                {'error': 'Failed to download file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='approve')
    @transaction.atomic
    def approve(self, request, pk=None):
        """Approve a submission (Admin only)."""
        user = request.user
        
        if user.role != 'admin':
            return Response(
                {'error': 'Only admins can approve submissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            submission = self.get_object()
            
            # Prevent approving already approved submissions
            if submission.status == 'approved':
                return Response(
                    {'error': 'Submission is already approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            submission.status = 'approved'
            submission.reviewed_by = user
            submission.reviewed_at = timezone.now()
            submission.remarks = ''  # Clear any previous rejection remarks
            submission.save()
            
            logger.info(
                f"Submission approved - ID: {submission.id}, Exam: {submission.exam.exam_name}, "
                f"Teacher: {submission.teacher.teacher_id}, Admin: {user.full_name}"
            )
            
            serializer = ExamSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Error approving submission: {str(e)}")
            return Response(
                {'error': 'Failed to approve submission'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='reject')
    @transaction.atomic
    def reject(self, request, pk=None):
        """Reject a submission (Admin only)."""
        user = request.user
        
        if user.role != 'admin':
            return Response(
                {'error': 'Only admins can reject submissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        remarks = request.data.get('remarks', '').strip()
        
        # Require remarks for rejection
        if not remarks:
            return Response(
                {'error': 'Remarks are required when rejecting a submission'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit remarks length
        if len(remarks) > 500:
            return Response(
                {'error': 'Remarks must be 500 characters or less'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            submission = self.get_object()
            
            # Prevent rejecting already approved submissions
            if submission.status == 'approved':
                return Response(
                    {'error': 'Cannot reject an approved submission'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            submission.status = 'rejected'
            submission.remarks = remarks
            submission.reviewed_by = user
            submission.reviewed_at = timezone.now()
            submission.save()
            
            logger.info(
                f"Submission rejected - ID: {submission.id}, Exam: {submission.exam.exam_name}, "
                f"Teacher: {submission.teacher.teacher_id}, Admin: {user.full_name}"
            )
            
            serializer = ExamSubmissionSerializer(submission)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Error rejecting submission: {str(e)}")
            return Response(
                {'error': 'Failed to reject submission'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
