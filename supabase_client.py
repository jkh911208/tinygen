import os

from supabase import Client, create_client

# Get Supabase URL and anonymous key from environment variables
url = ""
key = ""
SUPABASE_URL = os.getenv("SUPABASE_URL", url)
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", key)

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
