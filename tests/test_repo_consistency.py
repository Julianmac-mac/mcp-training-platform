from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_config_lists_get_user_email_tool() -> None:
    config_text = (ROOT / "namespaces" / "training_platform_mcp_g2" / "config.py").read_text(encoding="utf-8")
    assert '"get_user_email"' in config_text


def test_db_module_no_longer_contains_legacy_database_service() -> None:
    db_text = (ROOT / "db.py").read_text(encoding="utf-8")
    assert "class DatabaseService" not in db_text
