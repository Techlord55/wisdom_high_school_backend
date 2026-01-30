# Location: .\apps\users\views.py
# ==================== apps/users/views.py ====================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from apps.users.models import User
from apps.users.serializers import UserSerializer, UserUpdateSerializer
from apps.users import selectors
from apps.common.permissions import IsAdmin
from apps.auth.services.clerk import clerk_service
import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """User viewset."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.role == 'admin':
            return selectors.get_all_users()
        
        # Users can only see themselves
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        """Custom permissions."""
        if self.action in ['list', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    @transaction.atomic  # Ensure transaction completes
    def update_profile(self, request):
        """Update current user profile and optionally sync with Clerk."""
        user = request.user
        
        logger.info(f"Updating profile for user {user.id} with data: {request.data}")
        
        # Validate and save the update
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        
        # Explicitly refresh from database to ensure we have latest data
        updated_user.refresh_from_db()
        
        logger.info(f"Successfully updated user {user.id}. New data: first_name={updated_user.first_name}, last_name={updated_user.last_name}")
        
        # Try to sync with Clerk, but don't fail if it doesn't work
        if 'role' in request.data and user.clerk_id:
            try:
                clerk_service.update_user_metadata(
                    clerk_id=user.clerk_id,
                    public_metadata={
                        'role': user.role,
                        'profile_completed': True
                    }
                )
                logger.info(f"Successfully synced role '{user.role}' to Clerk for user {user.clerk_id}")
            except Exception as e:
                # Log the error but don't fail the request
                # Backend database is the source of truth for roles
                logger.warning(f"Could not sync role to Clerk for user {user.clerk_id}: {str(e)}")
                logger.info("Continuing anyway - backend is source of truth for roles")
        
        # Return the refreshed user data
        response_serializer = UserSerializer(updated_user)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['post'])
    def sync_clerk_metadata(self, request):
        """
        Attempt to sync current user's role to Clerk metadata.
        This is optional - if it fails, the backend role is still valid.
        """
        user = request.user
        
        if not user.clerk_id:
            return Response(
                {'error': 'User does not have a Clerk ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try to sync current role to Clerk's publicMetadata
            clerk_service.update_user_metadata(
                clerk_id=user.clerk_id,
                public_metadata={
                    'role': user.role,
                    'profile_completed': True,
                    'last_synced': str(user.updated_at)
                }
            )
            
            logger.info(f"Successfully synced metadata to Clerk for user {user.clerk_id} with role '{user.role}'")
            
            return Response({
                'success': True,
                'message': 'Metadata synced to Clerk successfully',
                'role': user.role
            })
            
        except Exception as e:
            # Don't return 500 - just indicate that sync wasn't possible
            # The user can still use the app with their backend role
            logger.warning(f"Could not sync metadata to Clerk for user {user.clerk_id}: {str(e)}")
            
            return Response(
                {
                    'success': False,
                    'message': 'Could not sync to Clerk, but your role is saved in our system',
                    'detail': str(e),
                    'role': user.role
                },
                status=status.HTTP_200_OK  # Return 200, not 500
            )
