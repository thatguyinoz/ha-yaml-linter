import pytest
from textwrap import dedent
from src.indent_analyzer import lint_yaml

def test_lint_valid_yaml():
    yaml_str = dedent("""\
    sensor:
      - platform: template
        sensors:
          wifi_password: !secret wifi_password_secret
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_tabs_detection():
    yaml_str = "light:\n\t- platform: group"  # Contains tab
    result = lint_yaml(yaml_str)
    assert result['valid'] is False
    assert result['line'] == 2
    assert "Tab characters are forbidden" in result['message']

def test_lint_mismatched_key_indent():
    # 'garage' is indented at 3 spaces (mismatched with 'rooms' at 2 spaces)
    yaml_str = dedent("""\
    house:
      rooms: 4
       garage: true
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is False
    assert result['line'] == 3  # rooms is on line 2, garage is on line 3 (due to dedent and stripped \n)
    assert result['suggested_indent'] == 2
    assert "Aligns with sibling key on line 2" in result['suggestion']

def test_lint_mismatched_list_item():
    # The second list item `- sensor2` is indented at 3 spaces, first is 2
    yaml_str = dedent("""\
    items:
      - sensor1
       - sensor2
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is False
    assert result['line'] == 3  # sensor2 is on line 3
    assert result['suggested_indent'] == 2
    assert "Aligns with sibling list item on line 2" in result['suggestion']

def test_lint_compact_hybrid_lines():
    yaml_str = dedent("""\
    - sensor:
      - name: "Used Amps Now"
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_nested_hybrid_lines():
    yaml_str = dedent("""\
    - sensor:
        - name: "Used Amps Now"
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_mixed_hybrid_lines_and_keys():
    yaml_str = dedent("""\
    - sensor:
      - platform: template
        sensors:
          wifi_password: !secret wifi_password_secret
      - platform: template2
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_invalid_hybrid_alignment():
    # Sibling list item on line 3 is misaligned (3 spaces instead of 2)
    yaml_str = dedent("""\
    - sensor:
      - name: "Sensor 1"
       - name: "Sensor 2"
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is False
    assert result['line'] == 3
    assert result['suggested_indent'] == 2
    assert "Aligns with sibling list item on line 2" in result['suggestion']

def test_lint_block_scalars():
    yaml_str = dedent("""\
    - sensor:
      - name: "Used Amps Now"
        state: >
          {% set load_p = states('sensor.total') | float * 1000 %}
          {{ load_p | round(1) }}
      - name: "Another Sensor"
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_flow_scalars_single_quoted():
    yaml_str = dedent("""\
    - sensor:
      - name: Day of Week
        state: '{{ [''Monday'',''Tuesday'',''Wednesday''][now().weekday()]
          }}'
      - name: Another
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_flow_scalars_double_quoted():
    yaml_str = dedent(r"""
    - sensor:
      - name: Test
        state: "This is a \"double-quoted\" multi-line
          string"
      - name: Another
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None

def test_lint_style_metrics():
    # 1. Compact Style file
    compact_yaml = dedent("""\
    - sensor:
      - name: "Compact 1"
      - name: "Compact 2"
    - binary_sensor:
      - name: "Compact 3"
    """)
    res = lint_yaml(compact_yaml)
    assert res['valid'] is True
    assert res['style_info']['compact_count'] == 3
    assert res['style_info']['nested_count'] == 0
    assert res['style_info']['mixed'] is False
    assert res['style_info']['majority'] == "compact"

    # 2. Nested Style file
    nested_yaml = dedent("""\
    - sensor:
        - name: "Nested 1"
        - name: "Nested 2"
    """)
    res = lint_yaml(nested_yaml)
    assert res['valid'] is True
    assert res['style_info']['compact_count'] == 0
    assert res['style_info']['nested_count'] == 2
    assert res['style_info']['mixed'] is False
    assert res['style_info']['majority'] == "nested"

    # 3. Mixed Styles file
    mixed_yaml = dedent("""\
    - sensor:
      - name: "Compact"
    - binary_sensor:
        - name: "Nested"
    """)
    res = lint_yaml(mixed_yaml)
    assert res['valid'] is True
    assert res['style_info']['compact_count'] == 1
    assert res['style_info']['nested_count'] == 1
    assert res['style_info']['mixed'] is True
    assert res['style_info']['majority'] is None

def test_unify_yaml_style():
    from src.indent_analyzer import unify_yaml_style
    
    mixed_yaml = dedent("""\
    - sensor:
      - name: "Compact"
    - binary_sensor:
        - name: "Nested"
    """)
    
    # 1. Unify mixed to compact
    compact_unified = unify_yaml_style(mixed_yaml, 'compact')
    expected_compact = dedent("""\
    - sensor:
      - name: "Compact"
    - binary_sensor:
      - name: "Nested"
    """)
    assert compact_unified == expected_compact
    
    # 2. Unify mixed to nested
    nested_unified = unify_yaml_style(mixed_yaml, 'nested')
    expected_nested = dedent("""\
    - sensor:
        - name: "Compact"
    - binary_sensor:
        - name: "Nested"
    """)
    assert nested_unified == expected_nested

def test_lint_compact_sequence_exiting():
    # Sibling key 'action' on Line 4 is a sibling of 'trigger', not part of the nested platform list
    yaml_str = dedent("""\
    - trigger:
      - platform: time_pattern
        seconds: "/10"
      action:
      - action: rest_command.receive_signal_messages
    """)
    result = lint_yaml(yaml_str)
    assert result['valid'] is True
    assert result['line'] is None
