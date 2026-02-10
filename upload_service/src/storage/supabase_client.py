from supabase import create_client, Client

from upload_service.settings import settings

supabase: Client = create_client(
    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
)
