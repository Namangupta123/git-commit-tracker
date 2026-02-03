import os
from tree_sitter import Parser

# Import official language bindings
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_go
import tree_sitter_java

# Map extensions to the actual language module
EXTENSION_MAP = {
    '.ts': tree_sitter_typescript.language_typescript, 
    '.tsx': tree_sitter_typescript.language_tsx,
    '.js': tree_sitter_javascript.language,
    '.jsx': tree_sitter_javascript.language,
    '.py': tree_sitter_python.language,
    '.go': tree_sitter_go.language,
    '.java': tree_sitter_java.language,
}

PARSER_CACHE = {}

def get_parser_and_language(filename: str):
    _, ext = os.path.splitext(filename)
    lang_func = EXTENSION_MAP.get(ext)

    if not lang_func:
        return None, None, None

    cache_key = ext
    if cache_key not in PARSER_CACHE:
        try:
            # The language bindings imported in EXTENSION_MAP already expose
            # a ready-to-use Language object (e.g. tree_sitter_python.language).
            language = lang_func

            # Create Parser and attach the language
            parser = Parser()
            parser.set_language(language)

            PARSER_CACHE[cache_key] = (language, parser)
        except Exception as e:
            print(f"DEBUG: Error loading parser for {ext}: {e}")
            return None, None, None

    language, parser = PARSER_CACHE[cache_key]
    
    # Map back to simple string name for query lookup
    lang_name_map = {
        '.ts': 'typescript', '.tsx': 'typescript',
        '.js': 'javascript', '.jsx': 'javascript',
        '.py': 'python',
        '.go': 'go',
        '.java': 'java'
    }
    lang_name = lang_name_map.get(ext)

    return language, parser, lang_name

def get_query_for_language(lang_name: str) -> str:
    # Simplified Queries (capturing the full string node is safer)
    if lang_name in ['typescript', 'javascript']:
        return """
        (call_expression
          function: [
            (identifier) @func_name
            (member_expression property: (property_identifier) @func_name)
          ]
          arguments: (arguments (string) @test_name)
          (#match? @func_name "^(test|describe|it)$")
        )
        """
    elif lang_name == 'python':
        return """
        (function_definition
          name: (identifier) @test_name
          (#match? @test_name "^test_")
        )
        """
    elif lang_name == 'go':
        return """
        (function_declaration
          name: (identifier) @test_name
          parameters: (parameter_list (parameter_declaration type: (pointer_type (type_identifier) @type)))
          (#match? @test_name "^Test")
          (#match? @type "T")
        )
        """
    elif lang_name == 'java':
        return """
        (method_declaration
          (modifiers (marker_annotation name: (identifier) @annotation))
          name: (identifier) @test_name
          (#match? @annotation "Test")
        )
        """
    return ""