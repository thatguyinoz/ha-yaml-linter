import sys
import os
import argparse
from src.indent_analyzer import lint_yaml, unify_yaml_style

# ANSI escape sequences for colorized output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @classmethod
    def disable(cls):
        cls.GREEN = ''
        cls.RED = ''
        cls.YELLOW = ''
        cls.CYAN = ''
        cls.BOLD = ''
        cls.RESET = ''

def main():
    # Disable color output if not writing to a terminal
    if not sys.stdout.isatty():
        Colors.disable()

    parser = argparse.ArgumentParser(description="HA YAML Indentation Linter & Auto-Fixer")
    parser.add_argument('file_path', nargs='?', default=None, help="Path to the YAML file to validate. If omitted or '-', reads from stdin.")
    parser.add_argument('--fix-style', choices=['compact', 'nested'], help="Automatically unify sequence indentation style throughout the file.")
    
    args = parser.parse_args()

    content = ""
    source_name = ""

    # Parse file path
    if args.file_path and args.file_path != "-":
        file_path = args.file_path
        if not os.path.exists(file_path):
            print(f"{Colors.RED}{Colors.BOLD}Error:{Colors.RESET} File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        if os.path.isdir(file_path):
            print(f"{Colors.RED}{Colors.BOLD}Error:{Colors.RESET} {file_path} is a directory, expected a file.", file=sys.stderr)
            sys.exit(1)
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            source_name = file_path
        except Exception as e:
            print(f"{Colors.RED}{Colors.BOLD}Error reading file:{Colors.RESET} {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from standard input (stdin)
        if sys.stdin.isatty():
            print(f"{Colors.YELLOW}{Colors.BOLD}Reading from stdin... (Paste your YAML, then press Ctrl+D to finish){Colors.RESET}\n")
        content = sys.stdin.read()
        source_name = "stdin"

    if not content.strip():
        print(f"{Colors.YELLOW}Warning: Empty input received. No YAML to lint.{Colors.RESET}")
        sys.exit(0)

    # If --fix-style is specified, we perform the rewrite
    if args.fix_style:
        unified_content = unify_yaml_style(content, args.fix_style)
        if args.file_path and args.file_path != "-":
            try:
                with open(args.file_path, 'w', encoding='utf-8') as f:
                    f.write(unified_content)
                print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Successfully unified sequence indentation style of {args.file_path} to '{args.fix_style}' style!{Colors.RESET}\n")
                sys.exit(0)
            except Exception as e:
                print(f"{Colors.RED}{Colors.BOLD}Error writing updated file:{Colors.RESET} {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # For stdin, we write to stdout
            sys.stdout.write(unified_content)
            sys.exit(0)

    # Standard execution: Execute linter
    result = lint_yaml(content)

    if result['valid']:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ YAML is valid and properly formatted! ({source_name}){Colors.RESET}")
        
        # Report Style Warnings if there are any mixed styles
        style_info = result.get('style_info')
        if style_info:
            compact_count = style_info.get('compact_count', 0)
            nested_count = style_info.get('nested_count', 0)
            if style_info.get('mixed'):
                print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Style Consistency Warning:{Colors.RESET}")
                print(f"   Found a mixture of sequence indentation styles in {source_name}:")
                print(f"     - Compact style items: {compact_count}")
                print(f"     - Nested style items:  {nested_count}")
                print(f"\n   {Colors.CYAN}To automatically unify the formatting of this file, run:{Colors.RESET}")
                if source_name != "stdin":
                    print(f"     python3 -m src.cli {source_name} --fix-style compact")
                    print(f"     python3 -m src.cli {source_name} --fix-style nested")
                else:
                    print(f"     python3 -m src.cli --fix-style compact")
                    print(f"     python3 -m src.cli --fix-style nested")
                print()
            else:
                active_style = "compact" if compact_count > 0 else ("nested" if nested_count > 0 else None)
                if active_style:
                    print(f"   (Formatting style: 100% consistent {active_style} style)\n")
                else:
                    print()
        else:
            print()
        sys.exit(0)
    else:
        line_num = result['line']
        col_num = result['column']
        message = result['message']
        suggestion = result['suggestion']
        marked_line = result['marked_line_content']

        print(f"\n{Colors.RED}{Colors.BOLD}✗ LINT ERROR in {source_name}:{Colors.RESET}")
        print(f"  Line {line_num}, Column {col_num}: {Colors.BOLD}{message}{Colors.RESET}\n")
        
        # Display the failed line and caret pointer
        if marked_line is not None:
            print(f"  {Colors.BOLD}{line_num:4d} |{Colors.RESET} {marked_line}")
            pointer_space = " " * (col_num - 1 if col_num > 1 else 0)
            print(f"       | {pointer_space}{Colors.RED}{Colors.BOLD}^{Colors.RESET}")

        if suggestion:
            print(f"\n{Colors.CYAN}{Colors.BOLD}Most Likely Fix:{Colors.RESET}")
            print(f"  {suggestion}\n")
            
        sys.exit(1)

if __name__ == '__main__':
    main()
