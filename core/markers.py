from __future__ import annotations
import re

# Canonical citation marker — matches {{cite:SOURCE_ID}} or {{cite:SOURCE_ID:PAGE}}
# Group 1: source_id, Group 2: page reference (optional, may be None)
CITE_RE = re.compile(r"\{\{cite:([^:}]+)(?::([^}]+))?\}\}")
