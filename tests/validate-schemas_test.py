import json
import os
import glob
import pytest

SCHEMA_DIR = "fabric/item"

def find_json_files(root_dir):
    """Yield all .json files under a directory recursively."""
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                yield os.path.join(dirpath, filename)

def extract_refs(schema, base_path):
    """Recursively extract $ref values from a schema and yield the resolved path."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "$ref" and isinstance(value, str):
                if not value.startswith("#") and not value.startswith("https://developer.microsoft.com/json-schemas"): # Ignore internal references and our published URLs
                    ref_path = value.split("#")[0]
                    resolved_path = os.path.normpath(os.path.join(base_path, ref_path))
                    yield resolved_path
            else:
                yield from extract_refs(value, base_path)
    elif isinstance(schema, list):
        for item in schema:
            yield from extract_refs(item, base_path)

@pytest.mark.parametrize("json_file", list(find_json_files(SCHEMA_DIR)))
def test_refs_exist(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            schema = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file}: {e}")

    base_path = os.path.dirname(json_file)
    for ref_path in extract_refs(schema, base_path):
        assert os.path.isfile(ref_path), f"Missing file for $ref in {json_file}: {ref_path}"