# Location: .\apps\auth\services\clerk.py
import requests
from django.conf import settings


class ClerkService:
    """Service for interacting with Clerk API."""
    
    BASE_URL = "https://api.clerk.com/v1"
    
    def __init__(self):
        self.api_key = settings.CLERK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def update_user_metadata(self, clerk_id: str, public_metadata: dict = None, private_metadata: dict = None):
        """
        Update user metadata in Clerk.
        
        Args:
            clerk_id: The Clerk user ID
            public_metadata: Public metadata to update (visible in JWT)
            private_metadata: Private metadata to update (not visible in JWT)
        
        Returns:
            dict: Updated user data from Clerk
        
        Raises:
            requests.HTTPError: If the update fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        url = f"{self.BASE_URL}/users/{clerk_id}"
        
        data = {}
        if public_metadata is not None:
            data["public_metadata"] = public_metadata
        if private_metadata is not None:
            data["private_metadata"] = private_metadata
        
        logger.info(f"Updating Clerk metadata for user {clerk_id}")
        logger.info(f"Request URL: {url}")
        logger.info(f"Request data: {data}")
        
        try:
            response = requests.patch(url, json=data, headers=self.headers, timeout=10)
            
            logger.info(f"Clerk API response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.error(f"User {clerk_id} not found in Clerk")
                logger.error(f"This usually means the clerk_id is incorrect or the user doesn't exist in Clerk")
                logger.error(f"Response: {response.text}")
            
            response.raise_for_status()
            
            logger.info(f"Successfully updated metadata for user {clerk_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update Clerk metadata: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_user(self, clerk_id: str):
        """Get user data from Clerk."""
        url = f"{self.BASE_URL}/users/{clerk_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


# Singleton instance
clerk_service = ClerkService()
