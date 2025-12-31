from fastapi.testclient import TestClient

from api.main import app


def _is_success_response(code: str) -> bool:
    return code.isdigit() and 200 <= int(code) < 300


def _resolve_ref(ref: str, components: dict) -> dict:
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix):
        return {}
    name = ref[len(prefix) :]
    return components.get("schemas", {}).get(name, {})


def _schema_has_examples(schema: dict, components: dict) -> bool:
    if not isinstance(schema, dict):
        return False
    if "examples" in schema or "example" in schema:
        return True
    if "$ref" in schema:
        return _schema_has_examples(_resolve_ref(schema["$ref"], components), components)
    for key in ("allOf", "oneOf", "anyOf"):
        if key in schema:
            return any(_schema_has_examples(item, components) for item in schema.get(key, []))
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for prop in properties.values():
            if isinstance(prop, dict) and ("examples" in prop or "example" in prop):
                return True
    return False


def _has_response_schema(response: dict) -> bool:
    content = response.get("content", {})
    if not isinstance(content, dict):
        return False
    for media in content.values():
        schema = media.get("schema") if isinstance(media, dict) else None
        if schema:
            return True
    return False


def test_openapi_summaries_and_descriptions_present() -> None:
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    paths = openapi.get("paths", {})
    for path, methods in paths.items():
        for method, info in methods.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            assert info.get("summary"), f"Missing summary for {method.upper()} {path}"
            assert info.get("description"), f"Missing description for {method.upper()} {path}"


def test_openapi_response_models_present() -> None:
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    for path, methods in openapi.get("paths", {}).items():
        for method, info in methods.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = info.get("responses", {})
            for code, response in responses.items():
                if code == "204":
                    continue
                if _is_success_response(code):
                    assert _has_response_schema(
                        response
                    ), f"Missing response schema for {method.upper()} {path} {code}"


def test_openapi_body_examples_present() -> None:
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    components = openapi.get("components", {})
    for path, methods in openapi.get("paths", {}).items():
        for method, info in methods.items():
            if method not in {"post", "put", "patch", "delete"}:
                continue
            request_body = info.get("requestBody")
            if not request_body:
                continue
            content = request_body.get("content", {})
            json_body = content.get("application/json")
            if not json_body:
                continue
            if json_body.get("examples") or json_body.get("example"):
                continue
            schema = json_body.get("schema", {})
            assert _schema_has_examples(
                schema, components
            ), f"Missing body examples for {method.upper()} {path}"


def test_openapi_error_examples_present() -> None:
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    for path, methods in openapi.get("paths", {}).items():
        for method, info in methods.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            responses = info.get("responses", {})
            for code in ("400", "404", "422", "500"):
                response = responses.get(code)
                if not response:
                    continue
                content = response.get("content", {}).get("application/json", {})
                assert content.get(
                    "example"
                ), f"Missing error example for {method.upper()} {path} {code}"
