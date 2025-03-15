import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def initialize_database():
    """
    Check if required tables exist and provide instructions to create them
    """
    print("Checking database tables...")
    
    try:
        # Check if users table exists (now with password_hash field)
        users_response = supabase.table('users').select('id', count='exact').limit(1).execute()
        print(f"Users table exists with {users_response.count} records")
    except Exception:
        print("Users table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE IF NOT EXISTS public.users (
            id UUID PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)
    
    try:
        # Check if tokens table exists
        tokens_response = supabase.table('tokens').select('token', count='exact').limit(1).execute()
        print(f"Tokens table exists with {tokens_response.count} records")
    except Exception:
        print("Tokens table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE IF NOT EXISTS public.tokens (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES public.users(id),
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_revoked BOOLEAN DEFAULT FALSE
        );
        """)