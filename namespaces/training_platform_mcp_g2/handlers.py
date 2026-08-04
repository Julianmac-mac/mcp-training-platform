import logging
from datetime import datetime
from fastmcp import FastMCP, Context
from ffmcp import GO_BASE_PATH

from .auth import extract_access_token, resolve_user_email
from db import (
    get_connection,
    get_course_id,
    get_stage_id,
    fetch_course_progress,
    save_course_progress as db_save_course_progress,
)

logger = logging.getLogger(__name__)

training_platform_mcp_g2_namespace = FastMCP("TrainingPlatformMcpG2Namespace")


def _build_progress_response(user_email: str, course_name: str, stage_name: str, updated_at: datetime) -> dict:
    return {
        "user_email": user_email,
        "current_course": course_name,
        "current_stage": stage_name,
        "updated_at": updated_at.isoformat(),
    }


async def _get_authenticated_user_email(ctx: Context) -> tuple[str | None, dict[str, str] | None]:
    """Validate the request token and resolve the authenticated user's email."""
    access_token = extract_access_token(ctx)
    if not access_token:
        logger.error("Access token not found")
        return None, {"error": "Authorization token is required"}

    try:
        return await resolve_user_email(access_token), None
    except ValueError as exc:
        logger.error("Token validation failed: %s", exc)
        return None, {"error": "Invalid or expired token"}


@training_platform_mcp_g2_namespace.tool()
async def get_course_progress(ctx: Context) -> dict:
    """
    Retrieve the current course progress for the authenticated user.
    """
    logger.info("get_course_progress called")

    user_email, auth_error = await _get_authenticated_user_email(ctx)
    if auth_error:
        return auth_error

    try:
        connection = get_connection()
    except Exception as exc:
        logger.exception("Database connection failed")
        return {"error": "Database connection failed"}

    try:
        progress = fetch_course_progress(connection, user_email)
        if progress is None:
            return {
                "user_email": user_email,
                "current_course": None,
                "current_stage": None,
                "updated_at": None,
                "message": "No progress record found for user",
            }

        course_name, stage_name, updated_at = progress
        return _build_progress_response(user_email, course_name, stage_name, updated_at)
    except Exception:
        logger.exception("Failed to fetch course progress")
        return {"error": "Failed to fetch course progress"}
    finally:
        connection.close()


@training_platform_mcp_g2_namespace.tool()
async def save_course_progress(course_name: str, stage_name: str, ctx: Context) -> dict:
    """
    Save or update the authenticated user's course progress.
    """
    logger.info("save_course_progress called with course_name=%s stage_name=%s", course_name, stage_name)

    user_email, auth_error = await _get_authenticated_user_email(ctx)
    if auth_error:
        return auth_error

    if not course_name or not stage_name:
        logger.error("Course name or stage name missing")
        return {"error": "course_name and stage_name are required"}

    try:
        connection = get_connection()
    except Exception:
        logger.exception("Database connection failed")
        return {"error": "Database connection failed"}

    try:
        course_id = get_course_id(connection, course_name)
        stage_id = get_stage_id(connection, stage_name)
        updated_at = db_save_course_progress(connection, user_email, course_id, stage_id)
        return {
            "status": "ok",
            "user_email": user_email,
            "saved_course": course_name,
            "saved_stage": stage_name,
            "updated_at": updated_at.isoformat(),
        }
    except Exception:
        logger.exception("Failed to save course progress")
        return {"error": "Failed to save course progress"}
    finally:
        connection.close()


@training_platform_mcp_g2_namespace.resource("training-platform-mcp-g2://welcome-resource")
def welcome_resource() -> str:
    return (
        "Welcome to the Training Platform MCP server. "
        "Use get_course_progress and save_course_progress to manage user progress."
    )


@training_platform_mcp_g2_namespace.prompt()
def welcome_prompt(topic: str) -> str:
    return f"Provide a concise explanation of {topic} with examples and best practices."


@training_platform_mcp_g2_namespace.tool()
async def get_user_email(ctx: Context) -> dict:
    """
    Get the email of the currently authenticated user from their access token.
    """
    logger.info("get_user_email called")

    # 1. Extraer el token de acceso desde el contexto
    access_token = extract_access_token(ctx)
    if not access_token:
        logger.error("Access token not found")
        return {"error": "Authorization token is required"}

    # 2. Resolver y validar el email del usuario usando el token
    try:
        user_email = await resolve_user_email(access_token)
        return {
            "status": "ok",
            "user_email": user_email
        }
    except ValueError as exc:
        logger.error("Token validation failed: %s", exc)
        return {"error": "Invalid or expired token"}