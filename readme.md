# Impact Analyzer

Impact Analyzer is a small CLI utility to determine which tests a given Git commit touches by mapping changed file ranges to test definitions discovered via Tree-sitter ASTs.

## Key principles

- AST-first: parse files to locate test definitions and compute exact line ranges.
- Language-driven: pick a parser by file extension and cache parsers for reuse.
- Conservative impact: report tests that overlap changed line ranges (added, removed, or modified).

## Quick start

Prerequisites

- Python 3.8+
- Git

Install for development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install from PyPI

```bash
pip install git-impact-analyzer
```

Run the CLI

```bash
impact-analyzer --commit <SHA> --repo <PATH_OR_URL>
```

## Common examples

- Analyze a remote repo (auto-clones): `impact-analyzer --commit 75cdcc5 --repo https://github.com/example/repo`
- Analyze a local repo: `impact-analyzer --commit 45433fd --repo ./my-local-project`

## What it detects

- JavaScript / TypeScript: `test`, `it`, `describe` call expressions (including `.only`, `.skip`).
- Python: functions named `test_*`.
- Other languages: extend by adding parsers and detection rules.

## Project structure

- `src/impact_analyzer/cli.py`: CLI entrypoint and repo handling (cloning, temp dirs).
- `src/impact_analyzer/engine.py`: Main orchestration—diff inspection, parsing, and result formatting.
- `src/impact_analyzer/parser.py`: Tree-sitter parsing and AST traversal to find tests and ranges.
- `src/impact_analyzer/languages.py`: Extension-to-parser mapping and parser caching.
- `src/impact_analyzer/git_utils.py`: Helpers to extract changed line ranges from commit diffs.

## Architecture notes

- The CLI resolves the repo (local path or remote URL) and checks out the requested commit.
- `git_utils` extracts hunks and changed line sets between the commit and its parent.
- Parsers in `languages.py` are looked up by extension; `parser.py` walks the AST and emits test identifiers and their line ranges.
- `engine.py` computes intersections between changed lines and test ranges to produce the final impact report.

## Extending the tool

1. Add a Tree-sitter grammar dependency (if needed) and expose it via `languages.py`.
2. Add detection logic for new test forms in `parser.py`.

## License

MIT
