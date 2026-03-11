from supabase import create_client, Client
from dotenv import load_dotenv
import os
from pathlib import Path


# Load from .env file
load_dotenv(Path(__file__).parent / ".env")


# Database Connection Details:
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")



if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_SERVICE_KEY not configured in .env file")
    print("Please add your Supabase credentials to backend/.env to enable database functionality")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
