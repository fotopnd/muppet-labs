import httpx
import pytest
from pytest_httpserver import HTTPServer

from error_hide_seek.corpus.arxiv import fetch_abstracts

ATOM_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <title>Test Paper Title</title>
    <summary>This is the abstract of the test paper.</summary>
    <category term="cs.AI"/>
    <category term="cs.LG"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2401.00002v1</id>
    <title>Another Paper</title>
    <summary>Second abstract text here.</summary>
    <category term="cs.AI"/>
  </entry>
</feed>"""


@pytest.mark.asyncio
async def test_fetch_abstracts_parses_xml(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data(
        ATOM_RESPONSE, content_type="application/atom+xml"
    )
    async with httpx.AsyncClient(base_url=httpserver.url_for("/")) as client:
        # Monkey-patch BASE URL for this test
        import error_hide_seek.corpus.arxiv as arxiv_mod

        orig = arxiv_mod._BASE_URL
        arxiv_mod._BASE_URL = httpserver.url_for("/api/query")
        try:
            papers = await fetch_abstracts(client, limit=2)
        finally:
            arxiv_mod._BASE_URL = orig

    assert len(papers) == 2
    assert papers[0].arxiv_id == "2401.00001v1"
    assert papers[0].title == "Test Paper Title"
    assert papers[0].abstract == "This is the abstract of the test paper."
    assert papers[0].categories == "cs.AI,cs.LG"
    assert papers[1].arxiv_id == "2401.00002v1"


@pytest.mark.asyncio
async def test_fetch_abstracts_respects_limit(httpserver: HTTPServer):
    httpserver.expect_request("/api/query").respond_with_data(
        ATOM_RESPONSE, content_type="application/atom+xml"
    )
    import error_hide_seek.corpus.arxiv as arxiv_mod

    orig = arxiv_mod._BASE_URL
    arxiv_mod._BASE_URL = httpserver.url_for("/api/query")
    try:
        async with httpx.AsyncClient(base_url=httpserver.url_for("/")) as client:
            papers = await fetch_abstracts(client, limit=1)
    finally:
        arxiv_mod._BASE_URL = orig
    assert len(papers) == 1
