import pytest
import json
from src.server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_lint_valid(client):
    response = client.post('/api/lint', json={
        "yaml": "sensor:\n  - platform: template\n"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['valid'] is True

def test_api_lint_invalid(client):
    response = client.post('/api/lint', json={
        "yaml": "items:\n  - item1\n   - item2\n"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['valid'] is False
    assert data['line'] == 3
    assert data['suggested_indent'] == 2

def test_api_lint_empty(client):
    response = client.post('/api/lint', json={})
    assert response.status_code == 400

def test_api_unify_style(client):
    response = client.post('/api/unify', json={
        "yaml": "sensor:\n  - name: \"Compact\"\nbinary_sensor:\n    - name: \"Nested\"\n",
        "style": "compact"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "yaml" in data
    assert "binary_sensor:\n- name: \"Nested\"" in data["yaml"]
