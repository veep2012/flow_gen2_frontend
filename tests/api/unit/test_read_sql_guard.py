import ast
import re
from pathlib import Path

SCENARIO_DOC_PATH = Path("documentation/test_scenarios/read_sql_guard_api_test_scenarios.md")
TEST_SCENARIO_MAP = {
    "test_api_sql_uses_workflow_views_only": ["TS-RSG-001"],
}

TARGET_FILES = [
    *sorted(Path("api/routers").glob("*.py")),
    Path("api/utils/helpers.py"),
    Path("api/utils/database.py"),
]

SQL_OBJECT_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+((workflow|core|ref|audit)\.([A-Za-z_][A-Za-z0-9_]*))",
    re.IGNORECASE,
)

ALLOWED_WORKFLOW_FROM_OBJECTS = {
    "add_distribution_list_member",
    "cancel_revision",
    "create_document",
    "create_distribution_list",
    "create_file",
    "create_file_commented",
    "create_notification",
    "create_written_comment",
    "delete_notification",
    "mark_notification_read",
    "replace_notification",
    "transition_revision",
    "update_document",
    "update_file",
    "update_revision",
    "update_written_comment",
}


def _iter_string_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def _collect_violations() -> list[str]:
    violations: list[str] = []
    for path in TARGET_FILES:
        for sql_text in _iter_string_literals(path):
            for match in SQL_OBJECT_RE.finditer(sql_text):
                full_name = match.group(1)
                schema = match.group(2).lower()
                object_name = match.group(3)
                if schema == "workflow":
                    if object_name.startswith("v_") or object_name in ALLOWED_WORKFLOW_FROM_OBJECTS:
                        continue
                    violations.append(f"{path}: non-view workflow read target '{full_name}'")
                    continue

                violations.append(f"{path}: base-schema read target '{full_name}'")
    return violations


def test_api_sql_uses_workflow_views_only() -> None:
    """Scenario IDs: TS-RSG-001."""
    violations = _collect_violations()
    assert not violations, "Read SQL guard violations:\n" + "\n".join(sorted(violations))


def test_read_sql_guard_traceability_contract() -> None:
    assert SCENARIO_DOC_PATH.exists(), f"Missing scenario doc: {SCENARIO_DOC_PATH}"
    doc_text = SCENARIO_DOC_PATH.read_text(encoding="utf-8")

    for test_name, scenario_ids in TEST_SCENARIO_MAP.items():
        assert test_name in doc_text, f"Missing mapped test in scenario doc: {test_name}"
        for scenario_id in scenario_ids:
            assert scenario_id in doc_text, f"Missing scenario ID in scenario doc: {scenario_id}"
