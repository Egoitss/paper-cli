# paper-cli

A CLI tool for writing, citing, and assembling academic qualification papers using the Anthropic API.

## Requirements

| Requirement | Purpose | Notes |
|---|---|---|
| Python 3.11+ | Runtime | |
| Anthropic API key | Writing, research, evaluation, summaries | Paid — billed per token |
| Google Translate | Chapter translation to Latvian (`translate_sections.py`) | Free — no API key needed |

All Python dependencies install via `pip install -r requirements.txt`:

| Package | Used for |
|---|---|
| `anthropic` | Anthropic API client |
| `click` | CLI commands |
| `python-docx` | Word document assembly |
| `python-dotenv` | Loading `.env` file |
| `pyyaml` | Parsing `paper.yaml` |
| `rich` | Terminal output formatting |
| `deep-translator` | Google Translate (chapter translation) |

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in `paper-cli/` (or export to your shell):

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Managing papers

Each paper is a self-contained project under `papers/<slug>/`.

```bash
python3 cli.py new <slug> --title "Paper Title"   # create and activate a new paper
python3 cli.py use <slug>                          # switch active paper
python3 cli.py list                                # show all papers and which is active
```

When creating a new paper, Claude will ask for the institution name and formatting guidelines.
Guidelines are stored at `papers/<slug>/guidelines.md` and consulted during all formatting decisions.

## Writing pipeline

Run commands in order:

```bash
python3 cli.py research "topic query" --type scientific|legal|industry|general
python3 cli.py write --section <section-id>
python3 cli.py cite
python3 cli.py build
```

| Command | What it does |
|---|---|
| `research` | Searches for sources via tool-use loop; appends to `data/sources.json` deduplicated by URL |
| `write` | Generates a draft section, auto-evaluates it (up to 3 retries), saves to `data/chapters/<id>.md` |
| `cite` | Replaces `{{cite:SOURCE_ID:PAGE}}` markers with Unicode superscripts; builds `citations.json` — **one-way** |
| `build` | Assembles approved chapters into `submission_draft.docx` (no API call) |
| `build-lv` | Same as `build` but produces the Latvian-language version |

## Additional commands

```bash
python3 cli.py improve --section <section-id>     # targeted rewrite of one section
python3 cli.py improve-all                        # run improve over all drafted sections
python3 cli.py summary                            # generate standalone summary_document.docx
python3 cli.py generate-tests                     # generate bibliography formatter tests for active paper
```

Run `generate-tests` after adding new sources via `research`. It writes `tests/test_generated_bibliography.py` with one test per source type present in the active paper — covering every formatter the project actually uses. Re-run any time sources change.

## Workflow

1. `research` — collect sources for a topic
2. `write --section <id>` — draft a section (marked `[~]` in `project_state.md`)
3. Review and edit `data/chapters/<id>.md` manually; set status to `[x]` when approved
4. Repeat steps 1–3 for all sections
5. `cite` — convert citation markers to superscripts
6. `build` — produce the final `.docx`

## Paper structure

```
papers/<slug>/
  paper.yaml          # section list, headings, word targets, institution
  guidelines.md       # institution formatting rules
  guidelines.pdf      # original PDF (optional)
  data/
    sources.json
    project_state.md
    chapters/
    appendices/
```

`paper.yaml` controls section order, word targets, chapter headings, and feature flags. See an existing paper for the schema.

## Testing

```bash
python3 -m pytest          # full suite (no real API calls — all mocked)
python3 -m pytest -v tests/test_write.py
```
