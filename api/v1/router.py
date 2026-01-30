# Location: .\api\v1\router.py
# ==================== api/v1/router.py ====================
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from apps.users.views import UserViewSet
from apps.students.views import (
    StudentViewSet, ExamViewSet, AttendanceViewSet, GradeViewSet,
    AssignmentViewSet, AssignmentSubmissionViewSet,
    get_class_levels, get_subjects
)
from apps.students.exam_views import ExamSubmissionViewSet
from apps.students.models import ExamSubmission
from apps.teachers.views import TeacherViewSet
from apps.payments.views import PaymentViewSet
from apps.settings.views import SystemSettingsViewSet

router = DefaultRouter()

# Register viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'exam-submissions', ExamSubmissionViewSet, basename='exam-submission')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'assignment-submissions', AssignmentSubmissionViewSet, basename='assignment-submission')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'system-settings', SystemSettingsViewSet, basename='system-settings')


# Build URL patterns
urlpatterns = [
    # Custom endpoints
    path('classes/', get_class_levels, name='class-levels'),
    path('subjects/', get_subjects, name='subjects'),
]

# Add router URLs - the ViewSet's download method will handle exam submission downloads
urlpatterns += router.urls