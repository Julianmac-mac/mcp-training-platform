from pathlib import Path
 
 
ROOT = Path(__file__).resolve().parents[1]
 
# Términos asociados al servicio de RRHH/talento que no forman parte del
# alcance del training platform y no deben reaparecer en el repositorio,
# sea en db.py, en un archivo "legacy" separado, o en cualquier otro lado.
HR_LEGACY_MARKERS = (
    "DatabaseService",
    "LegacyDatabaseService",
    "get_employee_360",
    "search_collaborators",
    "get_team_consolidated_metrics",
    "search_talent_by_technology",
    "get_skills_catalog_and_training_gaps",
    "Colaboradores",
)
 
 
def _all_python_files() -> list[Path]:
    return [
        p for p in ROOT.rglob("*.py")
        if ".git" not in p.parts and "tests" not in p.parts
    ]
 
 
def test_config_lists_get_user_email_tool() -> None:
    config_text = (ROOT / "namespaces" / "training_platform_mcp_g2" / "config.py").read_text(encoding="utf-8")
    assert '"get_user_email"' in config_text
 
 
def test_no_hr_legacy_code_anywhere_in_repo() -> None:
    offenders = []
    for path in _all_python_files():
        text = path.read_text(encoding="utf-8")
        for marker in HR_LEGACY_MARKERS:
            if marker in text:
                offenders.append(f"{path.relative_to(ROOT)}: {marker}")
    assert not offenders, (
        "Se encontraron restos de código de RRHH/talento fuera del alcance "
        f"del training platform: {offenders}"
    )
 
 
def test_db_module_only_exposes_course_progress_helpers() -> None:
    import ast
 
    db_text = (ROOT / "db.py").read_text(encoding="utf-8")
    tree = ast.parse(db_text)
    defined_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    expected = {
        "DatabaseConnectionError",
        "get_connection",
        "get_course_id",
        "get_stage_id",
        "fetch_course_progress",
        "save_course_progress",
    }
    assert defined_names == expected, (
        f"db.py define nombres inesperados: {defined_names - expected}"
    )