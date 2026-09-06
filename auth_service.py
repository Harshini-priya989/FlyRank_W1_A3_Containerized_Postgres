import os
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_client: Client | None = None


def supabase_client() -> Client:
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key or url.startswith("your_") or key.startswith("your_"):
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

    _client = create_client(url, key)
    return _client


def sign_up(email: str, password: str) -> Any:
    return supabase_client().auth.sign_up({"email": email, "password": password})


def sign_in(email: str, password: str) -> Any:
    return supabase_client().auth.sign_in_with_password(
        {"email": email, "password": password}
    )


def get_user(access_token: str) -> Any:
    return supabase_client().auth.get_user(access_token)


def sign_out() -> None:
    supabase_client().auth.sign_out()


def public_user(user: Any) -> dict[str, Any]:
    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "created_at": getattr(user, "created_at", None),
    }


def auth_response_payload(response: Any) -> dict[str, Any]:
    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    payload: dict[str, Any] = {}

    if user is not None:
        payload["user"] = public_user(user)
    if session is not None:
        payload["access_token"] = getattr(session, "access_token", None)
        payload["refresh_token"] = getattr(session, "refresh_token", None)
        payload["token_type"] = getattr(session, "token_type", "bearer")
        payload["expires_in"] = getattr(session, "expires_in", None)

    return payload
