NAMESPACE_CONFIG = {
    "name": "training-platform-mcp-g2",
    "display_name": "Training Platform MCP Namespace",
    "description": "Tools for Training Platform MCP progress management via SQL Server and token validation",
    "route": "/training-platform-mcp-g2",
    "auth_mode": "go-dev",
    "tools": [
        "get_course_progress",
        "save_course_progress",
    ],
    "resources": [
        "training-platform-mcp-g2://welcome-resource",
    ],
    "prompts": [
        "welcome_prompt",
    ],
}
