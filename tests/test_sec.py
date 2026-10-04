# tests/test_sec.py
from ai_debt_bubble_analysis.sources.sec import html_to_text, scan_filing_text


def test_html_to_text_removes_scripts():
    html = "<html><script>ignore me</script><body>Hello <b>world</b>.</body></html>"
    assert html_to_text(html) == "Hello world."


def test_scan_finds_structural_financing_evidence():
    text = """
    The company entered into a joint venture with a variable interest entity.
    The arrangement includes a residual value guarantee and minimum lease payments.
    Total commitments are US$27 billion.
    """
    evidence = scan_filing_text(text)
    assert evidence.mentions >= 3
    assert evidence.score > 20
    assert any("27 billion" in item["display"] for item in evidence.money_candidates)
