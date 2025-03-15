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
    
    # Check exam-related tables
    try:
        # Check if exams table exists
        exams_response = supabase.table('exams').select('id', count='exact').limit(1).execute()
        print(f"Exams table exists with {exams_response.count} records")
    except Exception:
        print("Exams table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE public.exams (
            id UUID PRIMARY KEY,
            exam_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            duration_mins INTEGER NOT NULL,
            is_mcq BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)
    
    try:
        # Check if questions table exists
        questions_response = supabase.table('questions').select('id', count='exact').limit(1).execute()
        print(f"Questions table exists with {questions_response.count} records")
    except Exception:
        print("Questions table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE public.questions (
            id UUID PRIMARY KEY,
            exam_id UUID NOT NULL REFERENCES public.exams(id),
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option VARCHAR(1) NOT NULL,
            marks INTEGER DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)
    
    try:
        # Check if user_exam_results table exists
        results_response = supabase.table('user_exam_results').select('id', count='exact').limit(1).execute()
        print(f"User exam results table exists with {results_response.count} records")
    except Exception:
        print("User exam results table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE public.user_exam_results (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES public.users(id),
            exam_id UUID NOT NULL REFERENCES public.exams(id),
            total_marks INTEGER NOT NULL,
            obtained_marks INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            wrong_answers INTEGER NOT NULL,
            completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)
    
    try:
        # Check if user_question_responses table exists
        responses_response = supabase.table('user_question_responses').select('id', count='exact').limit(1).execute()
        print(f"User question responses table exists with {responses_response.count} records")
    except Exception:
        print("User question responses table may not exist, please create it manually in the Supabase dashboard")
        print("""
        CREATE TABLE public.user_question_responses (
            id UUID PRIMARY KEY,
            result_id UUID NOT NULL REFERENCES public.user_exam_results(id),
            question_id UUID NOT NULL REFERENCES public.questions(id),
            selected_option VARCHAR(1),
            is_correct BOOLEAN NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """)
        
    print("Database check completed")