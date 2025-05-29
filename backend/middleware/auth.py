import os
from fastapi import HTTPException, Request
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase URL and Key must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def supabase_auth_middleware(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        user_response = supabase.auth.get_user(token)
        print(user_response)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # You can attach the user to the request state if needed
        # request.state.user = user_response.user 
        
    except Exception as e:
        # Log the exception for debugging
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

    return # Proceed to the next middleware or request handler 