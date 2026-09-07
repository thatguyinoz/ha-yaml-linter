import ruamel.yaml
from src.parser import parse_yaml

def get_indent(line: str) -> int:
    """Returns the number of leading spaces in a line."""
    return len(line) - len(line.lstrip(' '))

def is_leaf_key_value(line: str) -> bool:
    """
    Determines if a line is a leaf key-value pair (e.g. 'rooms: 4' or 'platform: template').
    A leaf key-value pair has a value defined on the same line and does not introduce a block.
    """
    stripped = line.strip()
    if stripped.startswith('-'):
        # Check if it contains a key-value inside, e.g. '- platform: template'
        content = stripped[1:].lstrip()
        if ':' in content:
            parts = content.split(':', 1)
            val = parts[1].strip()
            return bool(val and not val.startswith('#'))
        return False
        
    if ':' in stripped:
        parts = stripped.split(':', 1)
        val = parts[1].strip()
        return bool(val and not val.startswith('#'))
    return False

def is_hybrid_line(line: str) -> bool:
    """
    Determines if a line starts with a list bullet '-' and contains a dictionary key (e.g., '- sensor:').
    """
    stripped = line.strip()
    if not stripped.startswith('-'):
        return False
    # Exclude plain sequence item list bullets, e.g., '-' or '- val'
    content = stripped[1:].lstrip()
    if ':' in content:
        parts = content.split(':', 1)
        # Ensure it's a valid key-value structure by checking that the colon
        # is followed by a space, a comment, or nothing.
        after_colon = parts[1]
        if not after_colon or after_colon.startswith(' ') or after_colon.startswith('#'):
            return True
    return False

def is_block_scalar_start(line: str) -> bool:
    """
    Determines if a line starts a multiline block scalar (starts with '>' or '|').
    """
    stripped = line.strip()
    if ':' in stripped:
        parts = stripped.split(':', 1)
        val = parts[1].strip()
        if '#' in val:
            val = val.split('#', 1)[0].strip()
        return val.startswith('|') or val.startswith('>')
    elif stripped.startswith('-'):
        val = stripped[1:].strip()
        if '#' in val:
            val = val.split('#', 1)[0].strip()
        return val == '|' or val == '>' or val.startswith('|-') or val.startswith('>-') or val.startswith('|+') or val.startswith('>+')
    return False

def get_unclosed_quote(line: str) -> str | None:
    """
    Returns "'" if the line starts a single-quoted string that is not closed,
    '"' if it starts a double-quoted string that is not closed,
    or None otherwise.
    """
    stripped = line.strip()
    if ':' in stripped:
        parts = stripped.split(':', 1)
        val = parts[1].strip()
        if '#' in val:
            val = val.split('#', 1)[0].strip()
        if not val:
            return None
            
        if val.startswith("'"):
            temp = val.replace("''", "")
            q_count = temp.count("'")
            if q_count % 2 != 0:
                return "'"
        elif val.startswith('"'):
            temp = val.replace('\\"', "")
            q_count = temp.count('"')
            if q_count % 2 != 0:
                return '"'
    return None

def check_text_alignment(lines: list[str]) -> dict:
    """
    Checks for structural indentation misalignment in the lines of a YAML file
    using a hierarchical block stack analyzer.
    Returns an error dict if a misalignment is found, or a success dict with style metrics if consistent.
    """
    # Stack stores: (line_number, indent, block_type, is_leaf)
    # block_type is either 'map' or 'list'
    stack = []
    block_scalar_indent = None
    open_quote_char = None
    
    compact_count = 0
    nested_count = 0
    sequence_blocks = []
    
    def record_sequence_item(line_num, block_indent, parent_indent):
        nonlocal compact_count, nested_count
        if block_indent == parent_indent:
            compact_count += 1
            sequence_blocks.append({
                "line": line_num,
                "bullet_indent": block_indent,
                "key_indent": parent_indent,
                "style": "compact"
            })
        elif block_indent > parent_indent:
            nested_count += 1
            sequence_blocks.append({
                "line": line_num,
                "bullet_indent": block_indent,
                "key_indent": parent_indent,
                "style": "nested"
            })
            
    def push_block(line_num, block_indent, block_type, leaf_status):
        if block_type == 'list' and stack and stack[-1][2] == 'map':
            record_sequence_item(line_num, block_indent, stack[-1][1])
        stack.append((line_num, block_indent, block_type, leaf_status))
        
    def update_stack_top(line_num, block_indent, block_type, leaf_status):
        if block_type == 'list' and stack and stack[-1][2] == 'list' and len(stack) >= 2 and stack[-2][2] == 'map':
            record_sequence_item(line_num, block_indent, stack[-2][1])
        stack[-1] = (line_num, block_indent, block_type, leaf_status)
    
    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        if not line or line.strip().startswith('#'):
            continue
            
        indent = get_indent(raw_line)
        
        # If we are inside an open quoted string, skip version checking but check if it closes
        if open_quote_char is not None:
            stripped = raw_line.strip()
            if open_quote_char == "'":
                temp = stripped.replace("''", "")
                if temp.count("'") % 2 != 0:
                    open_quote_char = None
            elif open_quote_char == '"':
                temp = stripped.replace('\\"', "")
                if temp.count('"') % 2 != 0:
                    open_quote_char = None
            continue
            
        # If we are currently inside a block scalar, skip any line with deeper indentation
        if block_scalar_indent is not None:
            if indent > block_scalar_indent:
                continue
            else:
                # We have exited the block scalar
                block_scalar_indent = None
                
        # Determine current line element properties
        is_hybrid = is_hybrid_line(raw_line)
        is_block_scalar = is_block_scalar_start(raw_line)
        unclosed_quote = get_unclosed_quote(raw_line)
        is_multiline_val = is_block_scalar or (unclosed_quote is not None)
        
        if is_hybrid:
            bullet_indent = get_indent(raw_line)
            # Find key indent
            bullet_idx = raw_line.find('-')
            rest = raw_line[bullet_idx + 1:]
            key_offset = len(rest) - len(rest.lstrip(' '))
            key_indent = bullet_idx + 1 + key_offset
            
            # The list part of the hybrid line
            current_type = 'list'
            indent = bullet_indent
            is_leaf = False  # The list item itself contains a block (the mapping)
        else:
            indent = get_indent(raw_line)
            stripped = raw_line.strip()
            is_list = stripped.startswith('-')
            current_type = 'list' if is_list else 'map'
            is_leaf = is_leaf_key_value(raw_line) if not is_multiline_val else False
            
        if not stack:
            push_block(idx + 1, indent, current_type, is_leaf)
            if is_hybrid:
                key_is_leaf = is_leaf_key_value(raw_line) if not is_multiline_val else False
                push_block(idx + 1, key_indent, 'map', key_is_leaf)
            if is_block_scalar:
                block_scalar_indent = key_indent if is_hybrid else indent
            if unclosed_quote is not None:
                open_quote_char = unclosed_quote
            continue
            
        top_line, top_indent, top_type, top_is_leaf = stack[-1]
        
        # Rule 1: Consecutive List Item Rule
        # Consecutive list items in the same logical block must align exactly
        if current_type == 'list' and top_type == 'list':
            if indent != top_indent:
                diff = top_indent - indent
                direction = "right" if diff > 0 else "left"
                return {
                    "valid": False,
                    "line": idx + 1,
                    "column": indent + 1,
                    "message": "Mismatched list item indentation.",
                    "suggested_indent": top_indent,
                    "suggestion": f"Aligns with sibling list item on line {top_line} (shift {direction} by {abs(diff)} space{'s' if abs(diff) > 1 else ''} to {top_indent} spaces).",
                    "marked_line_content": raw_line
                }
                
        # Rule 2: Leaf Nesting Rule
        # Cannot nest elements under a completed leaf key-value pair
        if top_type == 'map' and top_is_leaf and indent > top_indent:
            diff = top_indent - indent
            direction = "right" if diff > 0 else "left"
            return {
                "valid": False,
                "line": idx + 1,
                "column": indent + 1,
                "message": "Mismatched indentation.",
                "suggested_indent": top_indent,
                "suggestion": f"Aligns with sibling key on line {top_line} (shift {direction} by {abs(diff)} space{'s' if abs(diff) > 1 else ''} to {top_indent} spaces).",
                "marked_line_content": raw_line
            }
            
        if indent > top_indent:
            # Valid nesting under a non-leaf map/list block
            push_block(idx + 1, indent, current_type, is_leaf)
            
        elif indent < top_indent:
            # We are exiting one or more blocks, pop stack to find active sibling level
            popped_elements = []
            while stack and stack[-1][1] > indent:
                popped_elements.append(stack.pop())
                
            if not stack:
                push_block(idx + 1, indent, current_type, is_leaf)
            else:
                new_top_line, new_top_indent, new_top_type, new_top_is_leaf = stack[-1]
                if new_top_indent == indent:
                    # Found matching sibling level. Ensure block types are consistent
                    if new_top_type != current_type:
                        # Allow compact sequence notation
                        if new_top_type == 'map' and not new_top_is_leaf and current_type == 'list':
                            push_block(idx + 1, indent, current_type, is_leaf)
                        # Exiting compact sequence (list bullet followed by sibling map key)
                        elif new_top_type == 'list' and current_type == 'map':
                            stack.pop() # Exit the list block
                            if stack:
                                new_top_line, new_top_indent, new_top_type, new_top_is_leaf = stack[-1]
                                if new_top_indent == indent and new_top_type == current_type:
                                    update_stack_top(idx + 1, indent, current_type, is_leaf)
                                else:
                                    push_block(idx + 1, indent, current_type, is_leaf)
                            else:
                                push_block(idx + 1, indent, current_type, is_leaf)
                        else:
                            return {
                                "valid": False,
                                "line": idx + 1,
                                "column": indent + 1,
                                "message": "Mixed block structure. Cannot mix mapping keys and list items at the same indentation level.",
                                "suggested_indent": new_top_indent,
                                "suggestion": f"Check alignment with line {new_top_line}.",
                                "marked_line_content": raw_line
                            }
                    else:
                        # Update top element status (leaf status can change on new sibling)
                        update_stack_top(idx + 1, indent, current_type, is_leaf)
                else:
                    # Misalignment! Indent is strictly between parent indent and popped sibling level
                    # Find a sibling of the same type for better suggestion
                    candidates = popped_elements + list(reversed(stack))
                    matching_candidates = [c for c in candidates if c[2] == current_type]
                    if matching_candidates:
                        best_sibling = matching_candidates[0]
                    else:
                        best_sibling = popped_elements[-1] if popped_elements else (new_top_line, new_top_indent, new_top_type, new_top_is_leaf)
                    sibling_line, sibling_indent, sibling_type, _ = best_sibling
                    
                    diff = sibling_indent - indent
                    direction = "right" if diff > 0 else "left"
                    type_str = "list item" if sibling_type == 'list' else "key"
                    return {
                        "valid": False,
                        "line": idx + 1,
                        "column": indent + 1,
                        "message": "Mismatched indentation.",
                        "suggested_indent": sibling_indent,
                        "suggestion": f"Aligns with sibling {type_str} on line {sibling_line} (shift {direction} by {abs(diff)} space{'s' if abs(diff) > 1 else ''} to {sibling_indent} spaces).",
                        "marked_line_content": raw_line
                    }
        else: # indent == top_indent
            # Continuing current block level. Ensure consistency of element type
            if top_type != current_type:
                # Allow compact sequence notation
                if top_type == 'map' and not top_is_leaf and current_type == 'list':
                    push_block(idx + 1, indent, current_type, is_leaf)
                # Exiting compact sequence (list bullet followed by sibling map key)
                elif top_type == 'list' and current_type == 'map':
                    stack.pop() # Exit the list block
                    if stack:
                        new_top_line, new_top_indent, new_top_type, new_top_is_leaf = stack[-1]
                        if new_top_indent == indent and new_top_type == current_type:
                            update_stack_top(idx + 1, indent, current_type, is_leaf)
                        else:
                            push_block(idx + 1, indent, current_type, is_leaf)
                    else:
                        push_block(idx + 1, indent, current_type, is_leaf)
                else:
                    return {
                        "valid": False,
                        "line": idx + 1,
                        "column": indent + 1,
                        "message": "Mixed block structure. Cannot mix mapping keys and list items at the same indentation level.",
                        "suggested_indent": top_indent,
                        "suggestion": f"Check structure around line {top_line}.",
                        "marked_line_content": raw_line
                    }
            else:
                # Update the leaf status of the active block level
                update_stack_top(idx + 1, indent, current_type, is_leaf)
                
        # If this is a hybrid line, we must now push the nested 'map' block to the stack
        if is_hybrid:
            key_is_leaf = is_leaf_key_value(raw_line) if not is_multiline_val else False
            push_block(idx + 1, key_indent, 'map', key_is_leaf)
            
        # Set block scalar tracking state if needed
        if is_block_scalar:
            block_scalar_indent = key_indent if is_hybrid else indent
            
        # Set open quote state if needed
        if unclosed_quote is not None:
            open_quote_char = unclosed_quote
            
    style_info = {
        "mixed": bool(compact_count > 0 and nested_count > 0),
        "compact_count": compact_count,
        "nested_count": nested_count,
        "majority": "compact" if compact_count > nested_count else ("nested" if nested_count > compact_count else None),
        "sequence_blocks": sequence_blocks
    }
    return {
        "valid": True,
        "style_info": style_info
    }

def find_most_likely_indent(lines: list[str], err_line_idx: int) -> tuple[int | None, str]:
    """
    Fallback context analyzer if a standard parser error is raised.
    Analyzes surrounding lines to suggest the correct indentation.
    """
    if err_line_idx < 0 or err_line_idx >= len(lines):
        return None, "Error line index is out of bounds."

    err_line = lines[err_line_idx]
    err_indent = get_indent(err_line)
    
    stripped_err = err_line.strip()
    is_list_item = stripped_err.startswith('-')
    is_key_value = ':' in stripped_err

    # Gather surrounding lines (5 up, 5 down)
    start_idx = max(0, err_line_idx - 5)
    end_idx = min(len(lines), err_line_idx + 6)
    
    context_lines = []
    for idx in range(start_idx, end_idx):
        if idx == err_line_idx:
            continue
        line = lines[idx]
        if not line.strip() or line.strip().startswith('#'):
            continue
            
        indent = get_indent(line)
        stripped = line.strip()
        
        context_lines.append({
            'idx': idx,
            'indent': indent,
            'is_list': stripped.startswith('-'),
            'is_key': ':' in stripped,
            'dist': abs(idx - err_line_idx)
        })

    if not context_lines:
        suggested = round(err_indent / 2) * 2
        if suggested == err_indent:
            suggested = max(0, err_indent - 2)
        return suggested, f"Inconsistent indentation. Standard YAML uses a multiple of 2 spaces (suggested: {suggested} spaces)."

    # Filter same type siblings
    same_type_siblings = []
    for c in context_lines:
        if is_list_item and c['is_list']:
            same_type_siblings.append(c)
        elif not is_list_item and is_key_value and c['is_key'] and not c['is_list']:
            same_type_siblings.append(c)
            
    same_type_siblings.sort(key=lambda x: x['dist'])
    
    if same_type_siblings:
        best_sibling = same_type_siblings[0]
        suggested = best_sibling['indent']
        if suggested == err_indent:
            for s in same_type_siblings[1:]:
                if s['indent'] != err_indent:
                    suggested = s['indent']
                    break
        if suggested != err_indent:
            diff = suggested - err_indent
            direction = "right" if diff > 0 else "left"
            return suggested, f"Aligns with sibling element on line {best_sibling['idx'] + 1} (shift {direction} by {abs(diff)} space{'s' if abs(diff) > 1 else ''} to {suggested} spaces)."

    # Standardize to nearest even indent
    even_indents = [c['indent'] for c in context_lines if c['indent'] % 2 == 0]
    if even_indents:
        closest_indent = min(even_indents, key=lambda x: abs(x - err_indent))
        diff = closest_indent - err_indent
        direction = "right" if diff > 0 else "left"
        return closest_indent, f"Aligns indentation with nearby block on line {context_lines[0]['idx'] + 1} (shift {direction} by {abs(diff)} space{'s' if abs(diff) > 1 else ''} to {closest_indent} spaces)."

    suggested = round(err_indent / 2) * 2
    if suggested == err_indent:
        suggested = max(0, err_indent - 2)
    return suggested, f"Inconsistent indentation. Standard YAML uses a multiple of 2 spaces (suggested: {suggested} spaces)."


def lint_yaml(yaml_content: str) -> dict:
    """
    Lints a YAML string. Matches tabs first, then performs the Sibling Alignment
    structural check, and finally executes the ruamel.yaml parser fallback.
    """
    lines = yaml_content.splitlines()

    # 1. Search for tab characters immediately
    for idx, line in enumerate(lines):
        if '\t' in line:
            return {
                "valid": False,
                "line": idx + 1,
                "column": line.find('\t') + 1,
                "message": "Tab characters are forbidden for indentation in YAML.",
                "suggested_indent": None,
                "suggestion": "Replace all tabs with spaces. Home Assistant uses 2-space indentation.",
                "marked_line_content": line
            }

    # 2. Perform raw text-based Sibling Alignment checks
    alignment_result = check_text_alignment(lines)
    if not alignment_result["valid"]:
        return alignment_result

    style_info = alignment_result.get("style_info")

    # 3. Fallback to parsing with ruamel.yaml to catch syntax errors
    try:
        parse_yaml(yaml_content)
        return {
            "valid": True,
            "line": None,
            "column": None,
            "message": "Valid YAML with style inconsistency." if (style_info and style_info["mixed"]) else "Valid YAML.",
            "suggested_indent": None,
            "suggestion": None,
            "marked_line_content": None,
            "style_info": style_info
        }
    except ruamel.yaml.error.YAMLError as e:
        line = None
        column = None
        message = str(e)
        
        if hasattr(e, "problem_mark") and e.problem_mark is not None:
            line = e.problem_mark.line + 1
            column = e.problem_mark.column + 1
        elif hasattr(e, "context_mark") and e.context_mark is not None:
            line = e.context_mark.line + 1
            column = e.context_mark.column + 1

        if line is None:
            line = len(lines)
            column = 1

        err_line_idx = line - 1
        marked_line = lines[err_line_idx] if err_line_idx < len(lines) else ""
        
        user_message = message
        if "mapping values are not allowed here" in message:
            user_message = "Mismatched mapping key or incorrect block structure."
        elif "did not find expected key" in message:
            user_message = "Expected a dictionary key but found mismatched indentation."
        elif "did not find expected '-' indicator" in message:
            user_message = "Expected a list item starting with '-' but found a structure mismatch."

        suggested_indent, suggestion = find_most_likely_indent(lines, err_line_idx)

        return {
            "valid": False,
            "line": line,
            "column": column,
            "message": user_message,
            "suggested_indent": suggested_indent,
            "suggestion": suggestion,
            "marked_line_content": marked_line
        }


def unify_yaml_style(yaml_content: str, target_style: str) -> str:
    """
    Rewrites YAML content to unify sequence indentation style to either 'compact' or 'nested'.
    """
    if target_style not in ('compact', 'nested'):
        return yaml_content

    lines = yaml_content.splitlines()
    alignment_result = check_text_alignment(lines)
    if not alignment_result["valid"]:
        # If there's an indentation error, we can't unify style cleanly, so return as-is
        return yaml_content

    style_info = alignment_result.get("style_info")
    if not style_info:
        return yaml_content

    sequence_blocks = style_info.get("sequence_blocks", [])
    shift_offsets = [0] * len(lines)
    
    # Process from top to bottom
    for block in sequence_blocks:
        start_idx = block["line"] - 1
        
        # Calculate current updated bullet indent for this block
        current_bullet_indent = block["bullet_indent"] + shift_offsets[start_idx]
        current_key_indent = block["key_indent"] + shift_offsets[start_idx]
        
        # Check current style
        current_style = "compact" if current_bullet_indent == current_key_indent else "nested"
        if current_style == target_style:
            continue
            
        # Calculate shift
        if target_style == 'compact':
            shift = current_key_indent - current_bullet_indent
        else: # target_style == 'nested'
            shift = (current_key_indent + 2) - current_bullet_indent
            
        # Apply shift to this line and all its children
        for i in range(start_idx, len(lines)):
            if i == start_idx:
                shift_offsets[i] += shift
            else:
                if not lines[i].strip():
                    continue
                line_indent = get_indent(lines[i]) + shift_offsets[i]
                if line_indent > current_bullet_indent:
                    shift_offsets[i] += shift
                else:
                    break
                    
    new_lines = []
    for i, line in enumerate(lines):
        if not line.strip():
            new_lines.append(line)
            continue
        shift = shift_offsets[i]
        if shift > 0:
            new_lines.append(' ' * shift + line)
        elif shift < 0:
            # Shift left: remove leading spaces
            leading_spaces = len(line) - len(line.lstrip(' '))
            remove_count = min(leading_spaces, abs(shift))
            new_lines.append(line[remove_count:])
        else:
            new_lines.append(line)
            
    result = '\n'.join(new_lines)
    if yaml_content.endswith('\n'):
        result += '\n'
    return result
