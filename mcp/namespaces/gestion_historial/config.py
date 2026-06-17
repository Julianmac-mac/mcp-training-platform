NAMESPACE_CONFIG = {
    "name": "historial-cursos",
    "display_name": "Historial Cursos Namespace",
    "description": "Tools for Historial Cursos progress management via SQL Server and token validation",
    "route": "/historial-cursos",
    "auth_mode": "go-token",
    "tools": [
        "get_course_progress",
        "save_course_progress",
    ],
    "resources": [
        "historial-cursos://welcome-resource",
    ],
    "prompts": [
        "welcome_prompt",
    ],
}
