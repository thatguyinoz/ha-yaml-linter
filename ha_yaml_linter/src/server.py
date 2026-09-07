from flask import Flask, request, jsonify, send_from_directory
import os
from src.indent_analyzer import lint_yaml, unify_yaml_style

app = Flask(__name__, static_folder='../web', static_url_path='')

@app.route('/')
def index():
    """Serves the main single-page web application."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/lint', methods=['POST'])
def api_lint():
    """
    API endpoint to validate a YAML string.
    Expects JSON: { "yaml": "your yaml string" }
    Or multipart form data with a file.
    """
    content = ""
    
    if request.is_json:
        data = request.get_json() or {}
        content = data.get('yaml', '')
    elif 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file:
            try:
                content = uploaded_file.read().decode('utf-8')
            except Exception as e:
                return jsonify({
                    "valid": False,
                    "line": None,
                    "column": None,
                    "message": f"Could not read uploaded file: {e}",
                    "suggested_indent": None,
                    "suggestion": None,
                    "marked_line_content": None
                }), 400
    else:
        # Check standard form data
        content = request.form.get('yaml', '')

    if not content:
        return jsonify({
            "valid": False,
            "line": None,
            "column": None,
            "message": "Empty content received.",
            "suggested_indent": None,
            "suggestion": None,
            "marked_line_content": None
        }), 400

    result = lint_yaml(content)
    return jsonify(result)

@app.route('/api/unify', methods=['POST'])
def api_unify():
    """
    API endpoint to unify sequence indentation style.
    Expects JSON: { "yaml": "your yaml string", "style": "compact" | "nested" }
    """
    data = request.get_json() or {}
    yaml_content = data.get('yaml', '')
    target_style = data.get('style', 'compact')
    
    if not yaml_content:
        return jsonify({"error": "Empty content received."}), 400
        
    result_yaml = unify_yaml_style(yaml_content, target_style)
    return jsonify({"yaml": result_yaml})

if __name__ == '__main__':
    # Run server locally
    app.run(host='0.0.0.0', port=5000, debug=True)
