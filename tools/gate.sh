#!/usr/bin/env bash
# Run the publish gate with this project's exceptions. These files legitimately contain the word DRAFT or a
# bracketed placeholder as part of their job: the gate itself and the upload tools; the scripts in code/ (the draft
# switch, the figure stamp, and Python indexing such as x[nz] that the placeholder pattern mistakes for "[n...]");
# the paper build script (writes the banner only when DRAFT is on); the glossary (defines "Draft stamp");
# the checklist and publish guide (tell the author about draft stamps and the DOI step).
# Secrets are still checked everywhere. Everything else, including every data table, README, CITATION.cff,
# and the paper, is checked for draft stamps and placeholders.
cd "$(dirname "$0")/.."
python3 tools/publish_gate.py . --allow-draft-in tools/ code/ paper/make_tex_inputs.py \
  docs/GLOSSARY.md docs/VERIFY_CHECKLIST.md docs/PUBLISH_GUIDE.md docs/CHANGELOG.md
