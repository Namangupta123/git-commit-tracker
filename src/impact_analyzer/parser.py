from typing import List, Dict
from .languages import get_parser_and_language

def find_tests_in_code(filename: str, source_code: bytes) -> List[Dict]:
    language, parser, lang_name = get_parser_and_language(filename)
    
    if not parser or not lang_name:
        # print(f"DEBUG: No parser found for {filename}")
        return []

    try:
        tree = parser.parse(source_code)
        root_node = tree.root_node
    except Exception as e:
        print(f"DEBUG: Parsing failed for {filename}: {e}")
        return []

    tests = []
    
    # --- Strategy: Manual Tree Walk (More Robust) ---
    # S-expressions can be fragile if the grammar version changes.
    # We will walk the tree and look for CallExpressions manually.
    
    cursor = tree.walk()
    visited_children = False
    
    while True:
        if not visited_children:
            node = cursor.node
            
            # Check if this node is a function call
            if node.type == 'call_expression':
                # Check 1: Is it a test function? (test, describe, it)
                func_node = node.child_by_field_name('function')
                if func_node:
                    func_text = func_node.text.decode('utf8', errors='ignore')
                    
                    # Matches: test(...), test.describe(...), it(...)
                    if func_text in ['test', 'describe', 'it'] or func_text.endswith('.describe') or func_text.endswith('.only') or func_text.endswith('.skip'):
                        
                        # Check 2: Get the first argument (the test name)
                        args_node = node.child_by_field_name('arguments')
                        if args_node and args_node.child_count > 0:
                            # The first child of arguments is usually '(', so we look at children to find a string
                            first_arg = None
                            for i in range(args_node.child_count):
                                child = args_node.children[i]
                                if child.type == 'string':
                                    first_arg = child
                                    break
                            
                            if first_arg:
                                raw_name = first_arg.text.decode('utf8', errors='ignore')
                                # Strip quotes ("name" -> name)
                                clean_name = raw_name.strip('"\'`')
                                
                                tests.append({
                                    'name': clean_name,
                                    'start': node.start_point[0] + 1,
                                    'end': node.end_point[0] + 1
                                })

            # Check for Python/Go/Java definitions
            elif node.type == 'function_definition' and lang_name == 'python':
                name_node = node.child_by_field_name('name')
                if name_node and name_node.text.decode('utf8').startswith('test_'):
                     tests.append({
                        'name': name_node.text.decode('utf8'),
                        'start': node.start_point[0] + 1,
                        'end': node.end_point[0] + 1
                    })

        # --- Navigation Logic ---
        if cursor.goto_first_child():
            visited_children = False
        elif cursor.goto_next_sibling():
            visited_children = False
        elif cursor.goto_parent():
            visited_children = True
        else:
            break

    return tests