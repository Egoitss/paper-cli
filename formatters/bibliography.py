from __future__ import annotations

EN_DASH = "–"

# Section order for bibliography:
# legislation → books → articles → internet resources → court practice → other
_SECTION_SUBTYPE_ORDER: dict[str, int] = {
    "legislation": 0,
    "book": 1,
    "monograph": 1,
    "article": 2,
    "internet": 3,
    "court": 4,
    "other": 5,
}

# Legislation sorted most-authoritative first within the legislation block
_LEGISLATION_ORDER = [
    "constitution", "international", "law", "cabinet", "ministerial", "legislation",
]


# ── Per-subtype format functions ─────────────────────────────────────────────

def format_legislation(
    title: str,
    adopted_date: str,
    publication: str,
    pub_ref: str,
    pub_date: str,
) -> str:
    """
    Tiesību akti format:
      Title (adopted_date)// Publication, pub_ref (pub_date).
    adopted_date is omitted when empty (EU regs already embed the date in title).
    pub_ref must include any prefix supplied by caller: "Nr. 43", "L 119/1", etc.
    No space before //.
    """
    date_part = f" ({adopted_date})" if adopted_date else ""
    return f"{title}{date_part}// {publication}, {pub_ref} ({pub_date})."


def format_book_1_to_3(
    surname: str,
    initial: str,
    title: str,
    city: str,
    publisher: str,
    year: int,
    pages: int,
    page_unit: str = "lpp.",
) -> str:
    """
    Grāmatas (1–3 authors):
      Surname I. Title.– City: Publisher, Year, X lpp.
    Separator is period immediately followed by en-dash (no space before dash).
    """
    return (
        f"{surname} {initial}. {title}.{EN_DASH} {city}: {publisher}, {year}, {pages} {page_unit}"
    )


def format_book_4_plus(
    title: str,
    initial: str,
    surname: str,
    city: str,
    publisher: str,
    year: int,
    pages: int,
    page_unit: str = "lpp.",
) -> str:
    """
    Grāmatas (4+ authors): title leads, first author listed as Initial. Surname u. c.
      Title/ I. Surname u. c.– City: Publisher, Year, X lpp.
    Note: initial precedes surname (reversed vs 1-3 author format).
    """
    return (
        f"{title}/ {surname} {initial}. u. c.{EN_DASH} {city}: {publisher}, {year}, {pages} {page_unit}"
    )


def format_article(
    surname: str,
    initial: str,
    article_title: str,
    journal: str,
    issue: str,
    year: int,
    pages: str,
) -> str:
    """
    Raksti grāmatās, žurnālos, laikrakstos (1–3 authors):
      Surname I. Article Title// Journal, issue, year[, pages].
    When initial is empty, surname is treated as a fully pre-formatted author string
    (e.g. "Tambe P., Cappelli P., Yakubovich V."). Pages are omitted when empty.
    """
    author_str = f"{surname} {initial}." if initial else surname
    tail = f"{journal}, {issue}, {year}" if issue else f"{journal}, {year}"
    if pages:
        tail += f", {pages}"
    return f"{author_str} {article_title}// {tail}."


def format_article_4_plus(
    article_title: str,
    surname: str,
    initial: str,
    journal: str,
    issue: str,
    year: int,
    pages: str,
) -> str:
    """
    Raksti (4+ authors): title leads, first author listed as Surname I. u. c.
      Article Title/ Surname I. u. c.// Journal, issue, year[, pages].
    Pages are omitted when empty.
    """
    tail = f"{journal}, {issue}, {year}" if issue else f"{journal}, {year}"
    if pages:
        tail += f", {pages}"
    return f"{article_title}/ {surname} {initial}. u. c.// {tail}."


def format_internet(
    surname: str,
    initial: str,
    title: str,
    url: str,
    accessed: str,
) -> str:
    """
    Interneta resursi:
      [Surname I.] Title.– URL.– (Sk. DD.MM.YYYY.).
    accessed should be "DD.MM.YYYY." (Latvian date with trailing period).
    """
    author_part = f"{surname} {initial}. " if surname else ""
    return f"{author_part}{title}.{EN_DASH} {url}.{EN_DASH} (Sk. {accessed})."


def format_court(
    case_title: str,
    date: str,
    court: str,
    case_no: str,
    url: str,
    accessed: str,
) -> str:
    """
    Tiesu prakse:
      Case title. Date Court spriedums lietā Nr. Case_No.– URL.– (Sk. DD.MM.YYYY.).
    """
    return (
        f"{case_title}. {date} {court} spriedums lietā Nr. {case_no}."
        f"{EN_DASH} {url}.{EN_DASH} (Sk. {accessed})."
    )


# ── Dispatcher: routes a source dict to the correct format function ──────────

def format_source(source: dict) -> str:
    subtype = source.get("source_subtype", "")
    author = source.get("author", "")
    title = source.get("title", "")
    year = source.get("year", 0)
    publisher = source.get("publisher", "")
    url = source.get("url", "")
    accessed = source.get("accessed", "")
    pages = source.get("pages", 0)
    city = source.get("city", "")
    authors = source.get("authors", [])
    page_unit = source.get("page_unit", "lpp.")

    if subtype == "legislation":
        return format_legislation(
            title=title,
            adopted_date=source.get("adopted_date", ""),
            publication=source.get("publication", publisher),
            pub_ref=source.get("pub_ref", source.get("pub_number", "")),
            pub_date=source.get("pub_date", ""),
        )
    if subtype == "court":
        return format_court(
            case_title=title,
            date=source.get("judgment_date", ""),
            court=source.get("court", ""),
            case_no=source.get("case_no", ""),
            url=url,
            accessed=accessed,
        )
    if subtype in ("book", "monograph"):
        author_count = len(authors) if authors else (1 if author else 0)
        initial = source.get("initial", "")
        if author_count >= 4:
            # 4+ authors: initial placed before surname
            return format_book_4_plus(
                title, initial, author, city, publisher, year, pages, page_unit
            )
        return format_book_1_to_3(
            author, initial, title, city, publisher, year, pages, page_unit
        )
    if subtype == "article":
        author_count = len(authors) if authors else (1 if author else 0)
        initial = source.get("initial", "")
        journal = source.get("journal", publisher)
        issue = source.get("issue", "")
        page_range = source.get("page_range", "")
        if author_count >= 4:
            return format_article_4_plus(title, author, initial, journal, issue, year, page_range)
        return format_article(author, initial, title, journal, issue, year, page_range)
    # Default: internet / online resource
    initial = source.get("initial", "")
    return format_internet(author, initial, title, url, accessed or "")


# ── Sorting: legislation block first, then by source type ────────────────────

def sort_bibliography(sources: list[dict]) -> list[dict]:
    legislation = [s for s in sources if s.get("source_subtype") == "legislation"]
    others = [s for s in sources if s.get("source_subtype") != "legislation"]

    def _leg_order(s: dict) -> int:
        hint = s.get("legislation_level", "legislation").lower()
        for i, level in enumerate(_LEGISLATION_ORDER):
            if level in hint:
                return i
        return len(_LEGISLATION_ORDER)

    def _section_order(s: dict) -> int:
        return _SECTION_SUBTYPE_ORDER.get(s.get("source_subtype", ""), 5)

    def _lang_order(s: dict) -> int:
        # Latvian first, then English, then German, then Cyrillic, then other
        lang = s.get("language", "").lower()
        if lang in ("lv", "latvian"):
            return 0
        if lang in ("en", "english"):
            return 1
        if lang in ("de", "german"):
            return 2
        if lang in ("ru", "russian", "be", "belarusian", "uk", "ukrainian"):
            return 3
        return 4

    def _sort_key(s: dict) -> tuple:
        name = (s.get("author") or s.get("title") or "").upper()
        return (_section_order(s), _lang_order(s), name)

    return sorted(legislation, key=_leg_order) + sorted(others, key=_sort_key)
