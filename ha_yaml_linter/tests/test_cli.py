import sys
import io
import pytest
from unittest.mock import patch
from src.cli import main

def test_cli_valid_file(tmp_path):
    # Create a temporary valid YAML file
    test_file = tmp_path / "valid.yaml"
    test_file.write_text("sensor:\n  - platform: template\n")

    # Mock sys.argv to pass the file path
    with patch("sys.argv", ["cli.py", str(test_file)]), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout, \
         pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert "✓ YAML is valid and properly formatted!" in mock_stdout.getvalue()

def test_cli_invalid_file(tmp_path):
    # Create a temporary invalid YAML file (mismatched list item)
    test_file = tmp_path / "invalid.yaml"
    test_file.write_text("items:\n  - item1\n   - item2\n")

    with patch("sys.argv", ["cli.py", str(test_file)]), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout, \
         pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    output = mock_stdout.getvalue()
    assert "✗ LINT ERROR" in output
    assert "Mismatched list item indentation." in output
    assert "Aligns with sibling list item on line 2" in output

def test_cli_stdin_valid():
    # Mock reading valid YAML from stdin
    with patch("sys.argv", ["cli.py"]), \
         patch("sys.stdin", io.StringIO("house:\n  rooms: 4\n")), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout, \
         pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert "✓ YAML is valid" in mock_stdout.getvalue()

def test_cli_stdin_invalid():
    # Mock reading invalid YAML from stdin (tab character)
    with patch("sys.argv", ["cli.py"]), \
         patch("sys.stdin", io.StringIO("light:\n\t- platform: group")), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout, \
         pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    output = mock_stdout.getvalue()
    assert "Tab characters are forbidden" in output
