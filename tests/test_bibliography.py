import pytest
from formatters.bibliography import (
    format_legislation,
    format_book_1_to_3,
    format_book_4_plus,
    format_article,
    format_article_4_plus,
    format_internet,
    format_court,
    format_source,
    sort_bibliography,
)


def test_format_legislation():
    result = format_legislation(
        title="Sample Legislation Title",
        adopted_date="01.01.2020.",
        publication="Sample Official Publication",
        pub_ref="Nr. 1",
        pub_date="01.01.2020.",
    )
    assert result == "Sample Legislation Title (01.01.2020.)// Sample Official Publication, Nr. 1 (01.01.2020.)."


def test_format_legislation_no_adopted_date():
    result = format_legislation(
        title="Sample Regulation Title",
        adopted_date="",
        publication="Sample Official Journal",
        pub_ref="L 1/1",
        pub_date="01.01.2021.",
    )
    assert result == "Sample Regulation Title// Sample Official Journal, L 1/1 (01.01.2021.)."


def test_format_book_1_to_3():
    result = format_book_1_to_3(
        surname="Lastname", initial="A",
        title="Sample Book Title",
        city="Riga", publisher="Sample Publisher",
        year=2020, pages=559,
    )
    assert result == "Lastname A. Sample Book Title.– Riga: Sample Publisher, 2020, 559 lpp."


def test_format_book_1_to_3_custom_page_unit():
    result = format_book_1_to_3(
        surname="Smith", initial="J",
        title="Sample Book Title Two",
        city="London", publisher="Pub",
        year=2021, pages=300, page_unit="pp.",
    )
    assert result == "Smith J. Sample Book Title Two.– London: Pub, 2021, 300 pp."


def test_format_book_4_plus():
    result = format_book_4_plus(
        title="Sample Textbook",
        initial="P", surname="Lastname",
        city="London", publisher="Sample University Press",
        year=2019, pages=738,
    )
    assert result == "Sample Textbook/ Lastname P. u. c.– London: Sample University Press, 2019, 738 lpp."


def test_format_article():
    result = format_article(
        surname="Smith", initial="A",
        article_title="Sample Article Title",
        journal="Sample Journal",
        issue="Nr. 3", year=2022, pages="45.–67. lpp.",
    )
    assert result == "Smith A. Sample Article Title// Sample Journal, Nr. 3, 2022, 45.–67. lpp.."


def test_format_article_4_plus():
    result = format_article_4_plus(
        article_title="Sample Article Title",
        surname="Lastname", initial="A",
        journal="Sample Academic Journal",
        issue="Vol. 15", year=2024,
        pages="1.–50. lpp.",
    )
    assert result == (
        "Sample Article Title/ Lastname A. u. c.//"
        " Sample Academic Journal, Vol. 15, 2024, 1.–50. lpp.."
    )


def test_format_internet_with_author():
    result = format_internet(
        surname="Brown", initial="J",
        title="Sample Internet Article",
        url="https://example.com/article/",
        accessed="15.03.2026.",
    )
    assert result == (
        "Brown J. Sample Internet Article."
        "– https://example.com/article/."
        "– (Sk. 15.03.2026.)."
    )


def test_format_internet_without_author():
    result = format_internet(
        surname="", initial="",
        title="Sample Online Resource",
        url="https://example.com/resource",
        accessed="10.04.2026.",
    )
    assert result == "Sample Online Resource.– https://example.com/resource.– (Sk. 10.04.2026.)."


def test_format_court():
    result = format_court(
        case_title="Doe v. Company",
        date="12.01.2023.",
        court="Sample Court Department",
        case_no="PAC-123/2023",
        url="https://example.com/case/123",
        accessed="01.04.2026.",
    )
    assert result == (
        "Doe v. Company. 12.01.2023. Sample Court Department spriedums lietā Nr. PAC-123/2023."
        "– https://example.com/case/123.– (Sk. 01.04.2026.)."
    )


def test_sort_bibliography_legislation_first():
    sources = [
        {"type": "scientific", "author": "Zeta", "title": "Z Study", "year": 2020,
         "publisher": "J", "url": "https://z.com", "summary": "", "key_quotes": [],
         "source_subtype": "article"},
        {"type": "legal", "author": "", "title": "GDPR", "year": 2016,
         "publisher": "EU", "url": "https://gdpr.eu", "summary": "", "key_quotes": [],
         "source_subtype": "legislation"},
    ]
    sorted_sources = sort_bibliography(sources)
    assert sorted_sources[0]["source_subtype"] == "legislation"


def test_en_dash_in_separators():
    result = format_book_1_to_3("Smith", "A", "Title", "London", "Pub", 2020, 300)
    assert ".–" in result
    assert " - " not in result


def test_sort_bibliography_latvian_before_foreign():
    sources = [
        {"type": "scientific", "author": "Foreign", "title": "Sample Study",
         "source_subtype": "article", "language": "en"},
        {"type": "scientific", "author": "Local", "title": "Sample Pētījums",
         "source_subtype": "article", "language": "lv"},
    ]
    sorted_sources = sort_bibliography(sources)
    assert sorted_sources[0]["language"] == "lv"
    assert sorted_sources[1]["language"] == "en"
