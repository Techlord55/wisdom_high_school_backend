# apps/teachers/clerk_sync.py
"""
Utility functions for syncing teachers with Clerk.
"""
import os
import requests
from django.conf import settings


def create_teacher_in_clerk(email, first_name, last_name, password=None, send_invitation=False):
    """
    Create a teacher user in Clerk.
    
    Args:
        email: Teacher's email address
        first_name: Teacher's first name
        last_name: Teacher's last name
        password: Optional password (if not provided, teacher will need to set it)
        send_invitation: If True, sends an invitation email
    
    Returns:
        dict: Clerk user object with 'id' field
    
    Raises:
        Exception: If Clerk API request fails
    """
    clerk_secret_key = settings.CLERK_SECRET_KEY
    
    if not clerk_secret_key:
        raise Exception("CLERK_SECRET_KEY not configured")
    
    # Prepare the request
    url = "https://api.clerk.com/v1/users"
    headers = {
        "Authorization": f"Bearer {clerk_secret_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email_address": [email],
        "first_name": first_name,
        "last_name": last_name,
        "public_metadata": {
            "role": "teacher"
        },
        "private_metadata": {},
        "skip_password_checks": False,
        "skip_password_requirement": password is None,
    }
    
    # Add password if provided
    if password:
        payload["password"] = password
    
    # Make the request to Clerk
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        error_detail = response.json() if response.content else {}
        raise Exception(
            f"Failed to create user in Clerk: {response.status_code} - {error_detail}"
        )
    
    clerk_user = response.json()
    
    # TODO: If send_invitation is True, send invitation email
    # This can be implemented using Clerk's invitation API or your email service
    
    return clerk_user


def update_teacher_in_clerk(clerk_id, email=None, first_name=None, last_name=None):
    """
    Update a teacher user in Clerk.
    
    Args:
        clerk_id: Clerk user ID
        email: New email (optional)
        first_name: New first name (optional)
        last_name: New last name (optional)
    
    Returns:
        dict: Updated Clerk user object
    
    Raises:
        Exception: If Clerk API request fails
    """
    clerk_secret_key = settings.CLERK_SECRET_KEY
    
    if not clerk_secret_key:
        raise Exception("CLERK_SECRET_KEY not configured")
    
    url = f"https://api.clerk.com/v1/users/{clerk_id}"
    headers = {
        "Authorization": f"Bearer {clerk_secret_key}",
        "Content-Type": "application/json"
    }
    
    payload = {}
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if email:
        payload["email_address"] = [email]
    
    if not payload:
        return None
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        error_detail = response.json() if response.content else {}
        raise Exception(
            f"Failed to update user in Clerk: {response.status_code} - {error_detail}"
        )
    
    return response.json()


def update_teacher_password_in_clerk(clerk_id, new_password):
    """
    Update a teacher's password in Clerk.
    
    Args:
        clerk_id: Clerk user ID
        new_password: New password to set
    
    Returns:
        dict: Updated Clerk user object
    
    Raises:
        Exception: If Clerk API request fails
    """
    clerk_secret_key = settings.CLERK_SECRET_KEY
    
    if not clerk_secret_key:
        raise Exception("CLERK_SECRET_KEY not configured")
    
    url = f"https://api.clerk.com/v1/users/{clerk_id}"
    headers = {
        "Authorization": f"Bearer {clerk_secret_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "password": new_password,
        "skip_password_checks": False
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        error_detail = response.json() if response.content else {}
        raise Exception(
            f"Failed to update password in Clerk: {response.status_code} - {error_detail}"
        )
    
    return response.json()


def delete_teacher_from_clerk(clerk_id):
    """
    Delete a teacher user from Clerk.
    
    Args:
        clerk_id: Clerk user ID
    
    Raises:
        Exception: If Clerk API request fails
    """
    clerk_secret_key = settings.CLERK_SECRET_KEY
    
    if not clerk_secret_key:
        raise Exception("CLERK_SECRET_KEY not configured")
    
    url = f"https://api.clerk.com/v1/users/{clerk_id}"
    headers = {
        "Authorization": f"Bearer {clerk_secret_key}",
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code not in [200, 204]:
        error_detail = response.json() if response.content else {}
        raise Exception(
            f"Failed to delete user from Clerk: {response.status_code} - {error_detail}"
        )
    
    return True
