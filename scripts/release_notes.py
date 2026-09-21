"""Print the changelog entry corresponding to a release tag."""
from pathlib import Path
import re
import sys

tag = sys.argv[1] if len(sys.argv) == 2 else ''
if not re.match(r'^v[0-9]+\.[0-9]+\.[0-9]+\Z', tag):
    sys.exit('Expected a vMAJOR.MINOR.PATCH tag')
changelog = (Path(__file__).resolve().parents[1] / 'CHANGELOG.md').read_text(encoding='utf-8')
entry = re.search(r'^## \[' + re.escape(tag[1:]) + r'\][^\n]*\n(.*?)(?=^## |\Z)',
                  changelog, re.MULTILINE | re.DOTALL)
if not entry or not entry[1].strip():
    sys.exit('No changelog entry for this tag')
print(entry[1].strip())
