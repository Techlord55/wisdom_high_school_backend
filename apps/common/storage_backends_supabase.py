"""
Supabase Storage Backend for Django
Replaces Cloudinary/R2 with Supabase Storage
"""
from django.core.files.storage import Storage
from django.conf import settings
from django.core.files.base import ContentFile
from supabase import create_client, Client
from io import BytesIO
import mimetypes
import os
from urllib.parse import urljoin


class SupabaseStorage(Storage):
    """
    Custom storage backend for Supabase Storage
    """
    
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print(f"🔧 Initialized SupabaseStorage: bucket={self.bucket_name}")
        
    def _get_bucket(self):
        """Get or create storage bucket"""
        try:
            # Try to get existing bucket
            bucket = self.supabase.storage.get_bucket(self.bucket_name)
            return bucket
        except Exception:
            # Create bucket if it doesn't exist
            try:
                self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": True}  # Make bucket public
                )
                print(f"✅ Created Supabase bucket: {self.bucket_name}")
            except Exception as e:
                print(f"⚠️  Bucket may already exist or error: {e}")
        
    def _save(self, name, content):
        """
        Save file to Supabase Storage
        """
        print(f"\n📤 SupabaseStorage._save() called")
        print(f"   Original path: {name}")
        
        # CRITICAL: Normalize path separators - Supabase requires forward slashes
        # Windows uses backslashes, but Supabase needs forward slashes
        name = name.replace('\\', '/')
        print(f"   Normalized path: {name}")
        
        # Ensure bucket exists
        self._get_bucket()
        
        # Read file content
        if hasattr(content, 'read'):
            file_content = content.read()
        else:
            file_content = content
        
        print(f"   Size: {len(file_content)} bytes")
            
        # Get content type - force application/octet-stream for better compatibility
        content_type, _ = mimetypes.guess_type(name)
        
        # Map to supported MIME types
        if content_type is None:
            content_type = 'application/octet-stream'
        elif content_type == 'text/plain':
            # Supabase might not support text/plain, use octet-stream
            content_type = 'application/octet-stream'
        elif content_type.startswith('text/'):
            # For any text type, use octet-stream for better compatibility
            content_type = 'application/octet-stream'
        
        print(f"   Content-Type: {content_type}")
        
        try:
            # Upload to Supabase
            print(f"   Uploading to Supabase...")
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=name,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",  # 1 hour cache
                    "upsert": "true"  # Overwrite if exists
                }
            )
            
            print(f"✅ Uploaded to Supabase: {name}")
            return name
            
        except Exception as e:
            print(f"❌ Error uploading to Supabase: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _open(self, name, mode='rb'):
        """
        Retrieve file from Supabase Storage
        """
        # Normalize path
        name = name.replace('\\', '/')
        print(f"📥 Opening file from Supabase: {name}")
        
        try:
            # Download file
            response = self.supabase.storage.from_(self.bucket_name).download(name)
            print(f"✅ File downloaded from Supabase")
            return ContentFile(response)
        except Exception as e:
            print(f"❌ Error downloading from Supabase: {e}")
            raise
    
    def delete(self, name):
        """
        Delete file from Supabase Storage
        """
        # Normalize path
        name = name.replace('\\', '/')
        
        try:
            self.supabase.storage.from_(self.bucket_name).remove([name])
            print(f"🗑️  Deleted from Supabase: {name}")
        except Exception as e:
            print(f"❌ Error deleting from Supabase: {e}")
    
    def exists(self, name):
        """
        Check if file exists in Supabase Storage
        """
        # Normalize path
        name = name.replace('\\', '/')
        print(f"🔍 Checking if file exists: {name}")
        
        try:
            # Try to get file info
            files = self.supabase.storage.from_(self.bucket_name).list(path=os.path.dirname(name))
            filename = os.path.basename(name)
            exists = any(f['name'] == filename for f in files)
            print(f"   Result: {'✅ File exists' if exists else '❌ File not found'}")
            return exists
        except Exception as e:
            print(f"   Error checking existence: {e}")
            return False
    
    def url(self, name):
        """
        Return the public URL for the file
        """
        # Normalize path
        name = name.replace('\\', '/')
        
        # Get public URL from Supabase
        public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(name)
        return public_url
    
    def size(self, name):
        """
        Return the size of the file
        """
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(path=os.path.dirname(name))
            filename = os.path.basename(name)
            for f in files:
                if f['name'] == filename:
                    return f.get('metadata', {}).get('size', 0)
            return 0
        except Exception:
            return 0
    
    def listdir(self, path):
        """
        List the contents of the specified path
        """
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(path=path)
            directories = []
            filenames = []
            
            for item in files:
                if item.get('id'):  # It's a file
                    filenames.append(item['name'])
                else:  # It's a directory
                    directories.append(item['name'])
            
            return directories, filenames
        except Exception:
            return [], []
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's available in the storage mechanism
        """
        # Supabase supports upsert, so we can use the same name
        return name
    
    def get_accessed_time(self, name):
        """
        Return the last accessed time of the file
        """
        # Supabase doesn't provide access time
        return None
    
    def get_created_time(self, name):
        """
        Return the creation time of the file
        """
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(path=os.path.dirname(name))
            filename = os.path.basename(name)
            for f in files:
                if f['name'] == filename:
                    # Parse created_at timestamp if available
                    return f.get('created_at')
            return None
        except Exception:
            return None
    
    def get_modified_time(self, name):
        """
        Return the last modified time of the file
        """
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(path=os.path.dirname(name))
            filename = os.path.basename(name)
            for f in files:
                if f['name'] == filename:
                    return f.get('updated_at')
            return None
        except Exception:
            return None