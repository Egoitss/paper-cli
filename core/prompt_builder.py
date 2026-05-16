import json
import config
from core.source_manager import load_sources
from core.state_manager import load_state

_TYPE_INSTRUCTIONS: dict = {
    "scientific": (
        "Focus on peer-reviewed journal articles and academic studies. "
        "Target Google Scholar, ResearchGate, JSTOR. Prioritise papers with DOIs."
    ),
    "legal": (
        "Focus on official EU legislation (EUR-Lex), GDPR text, EU AI Act, "
        "Latvian Labor Law, and regulatory guidance documents."
    ),
    "industry": (
        "Focus on reports from McKinsey, Deloitte, Gartner, SHRM, "
        "World Economic Forum, or IBM Institute for Business Value."
    ),
    "general": (
        "Focus on books, verified news articles, professional publications, "
        "and reputable online resources."
    ),
}


def build_system(include_sources: bool = True) -> str:
    state = load_state()
    state_lines = "\n".join(f"    {k}: {v}" for k, v in state.items())
    sources_block = ""
    if include_sources:
        sources = load_sources()
        sources_block = (
            f"  <sources>\n{json.dumps(sources, ensure_ascii=False, indent=2)}\n  </sources>"
        )
    return (
        f"<system>\n"
        f"  <role>You are an academic research writer specialising in "
        f"{config.PAPER_DOMAIN}. Write in formal academic English, third person only, "
        f"no first-person pronouns.</role>\n"
        f"  <project>\n"
        f"    <title>{config.PAPER_TITLE}</title>\n"
        f"    <style>Academic, formal, {config.PAPER_DOMAIN}</style>\n"
        f"    <writing_style>\n"
        f"      <rule>Use short, clear sentences. Break long compound sentences into two or more shorter ones.</rule>\n"
        f"      <rule>Use simple, direct language. Avoid unnecessarily complex vocabulary.</rule>\n"
        f"      <rule>Do NOT use em dashes (—). Use a period, comma, or rewrite the sentence.</rule>\n"
        f"      <rule>These rules apply to all original text. Direct quotes from sources are excluded.</rule>\n"
        f"    </writing_style>\n"
        f"    <target_length>40 pages total</target_length>\n"
        f"    <institution>{config.INSTITUTION}</institution>\n"
        f"  </project>\n"
        f"  <state>\n{state_lines}\n  </state>\n"
        f"  {sources_block}\n"
        f"</system>"
    )


def build_write_prompt(section: str, sources_to_use: list) -> str:
    meta = config.SECTION_META[section]
    min_w, max_w = meta["target_words"]
    kind = meta["kind"]
    special = _special_instructions(kind)
    desc = meta.get("description", "")
    desc_block = (
        f"    <section_description>{desc.strip()}</section_description>\n" if desc else ""
    )
    return (
        f"<user>\n"
        f"  <task>Write section: {meta['title']}</task>\n"
        f"  <requirements>\n"
        f"    <length>{min_w}-{max_w} words</length>\n"
        f"    <sources_to_use>{', '.join(sources_to_use)}</sources_to_use>\n"
        f"    <citation_format>Mark citations as {{{{cite:SOURCE_ID:PAGE}}}} "
        f"immediately after the referenced text, e.g. {{{{cite:src_001:p.45}}}}</citation_format>\n"
        f"    {special}\n"
        f"{desc_block}"
        f"  </requirements>\n"
        f"</user>"
    )


def _special_instructions(kind: str) -> str:
    if kind == "introduction":
        return (
            "<must_include>\n"
            "      <item>Topic characterization and relevance to current practice</item>\n"
            "      <item>Overview of prior research naming at least 2 key authors</item>\n"
            "      <item>Clearly formulated goal and objectives of the paper</item>\n"
            "      <item>Justified paper structure (briefly describe each chapter)</item>\n"
            "      <item>Research scope and boundaries</item>\n"
            "      <item>Research methods: analysis, synthesis, comparative, descriptive, empirical</item>\n"
            "    </must_include>"
        )
    if kind == "empirical":
        return (
            "<must_include>\n"
            "      <item>Concrete real-world examples or documented cases relevant to the topic</item>\n"
            "      <item>Evaluation of identified problems or compliance issues</item>\n"
            "      <item>End with a conclusions paragraph highlighting key findings</item>\n"
            "    </must_include>"
        )
    if kind == "conclusions":
        return (
            "<must_include>\n"
            "      <item>Broader generalizations evaluating all analysed processes</item>\n"
            "      <item>Statement of what this research has contributed to the topic</item>\n"
            "      <item>Concrete actionable proposals and recommendations for problem resolution</item>\n"
            "    </must_include>"
        )
    return (
        "<must_include>\n"
        "      <item>Reference at least one applicable legal framework "
        "(GDPR, EU AI Act, or labor law) where relevant</item>\n"
        "      <item>End with a brief conclusions paragraph highlighting "
        "key insights or problems</item>\n"
        "    </must_include>"
    )


def build_evaluate_system(section: str) -> str:
    meta = config.SECTION_META[section]
    min_w, max_w = meta["target_words"]
    kind = meta["kind"]

    legal_criterion = (
        '    <legal_norms>references applicable legal norms (GDPR, EU AI Act, or labor law)</legal_norms>\n'
        if kind != "empirical" else ""
    )
    intro_criterion = (
        "    <introduction_elements>contains: topic relevance, prior research with author "
        "names, goal and objectives, structure justification, scope, research methods"
        "</introduction_elements>\n"
        if kind == "introduction" else ""
    )
    proposals_criterion = (
        "    <conclusions_proposals>contains both summary conclusions AND concrete "
        "actionable proposals</conclusions_proposals>\n"
        if kind == "conclusions" else ""
    )
    subchapter_conclusions = (
        "    <subchapter_conclusions>ends with a conclusions paragraph</subchapter_conclusions>\n"
        if kind not in ("introduction",) else ""
    )

    require_scientific = config.FEATURES.get("require_scientific", True)
    scientific_criterion = (
        "    <scientific_sources>at least 1 scientific publication cited</scientific_sources>\n"
        if require_scientific else ""
    )
    return (
        f"<system>\n"
        f"  <role>You are an academic quality reviewer for a {config.PAPER_DOMAIN} qualification paper</role>\n"
        f"  <criteria>\n"
        f"    <word_count>between {min_w} and {max_w} words</word_count>\n"
        f"    <sources_cited>minimum 2 citation markers {{{{cite:...}}}} present</sources_cited>\n"
        f"{scientific_criterion}"
        f"{legal_criterion}"
        f"{intro_criterion}"
        f"{proposals_criterion}"
        f"{subchapter_conclusions}"
        f"    <tone>formal academic, no first person (no I, we, my)</tone>\n"
        f"    <sentence_style>short clear sentences; no em dashes (—) in original text</sentence_style>\n"
        f"    <structure>clear opening sentence, coherent body paragraphs, closing summary</structure>\n"
        f"    <topic_alignment>stays within scope of: {meta['title']}</topic_alignment>\n"
        f"  </criteria>\n"
        f"</system>"
    )


def build_evaluate_prompt(section: str, draft: str) -> str:
    return (
        f"<user>\n"
        f'  <task>Evaluate this draft. Return JSON only: {{"pass": true/false, '
        f'"failures": [{{"criterion": "...", "detail": "..."}}], "word_count": N}}</task>\n'
        f"  <draft>{draft}</draft>\n"
        f"</user>"
    )


def build_research_prompt(query: str, source_type: str, existing_urls: list) -> str:
    existing = "\n".join(existing_urls) if existing_urls else "none"
    instruction = _TYPE_INSTRUCTIONS.get(source_type, _TYPE_INSTRUCTIONS["general"])
    return (
        f"<user>\n"
        f"  <task>Find sources about: {query}</task>\n"
        f"  <type_instruction>{instruction}</type_instruction>\n"
        f"  <already_collected>\n{existing}\n  </already_collected>\n"
        f"  <output_format>Return a JSON array. Each object must have: "
        f"author (string, surname only or empty if corporate), title (string), "
        f"year (integer), publisher (string), url (string), "
        f"summary (3-5 sentences), key_quotes (array of 2-3 strings), "
        f'type ("{source_type}")</output_format>\n'
        f"  <constraints>\n"
        f"    <item>Never return URLs already in already_collected</item>\n"
        f"    <item>Every source must be real and verifiable</item>\n"
        f"    <item>Return 3-5 sources per search</item>\n"
        f"  </constraints>\n"
        f"</user>"
    )
