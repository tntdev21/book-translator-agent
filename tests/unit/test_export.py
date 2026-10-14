"""Regression tests for unified export artifacts."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_proof_pdf_does_not_write_utility_debug_html(tmp_path, monkeypatch):
    import utils.export_pdf as export_pdf

    class FakeHTML:
        def __init__(self, string):
            self.string = string

        def write_pdf(self, output_path, **kwargs):
            Path(output_path).write_bytes(b"pdf")

    class FakeCSS:
        def __init__(self, string, font_config):
            pass

    class FakeFontConfiguration:
        pass

    monkeypatch.setattr(export_pdf, "markdown_to_html_with_dialogue", lambda *args, **kwargs: "<p>Proof</p>")
    monkeypatch.setitem(sys.modules, "weasyprint", type("WeasyPrint", (), {"HTML": FakeHTML, "CSS": FakeCSS})())
    monkeypatch.setitem(sys.modules, "weasyprint.text", type("Text", (), {})())
    monkeypatch.setitem(sys.modules, "weasyprint.text.fonts", type("Fonts", (), {"FontConfiguration": FakeFontConfiguration})())

    output = tmp_path / "document_proof_2026-10-03T143958_proof.pdf"
    assert export_pdf.create_pdf("# Proof", str(output), proof_mode=True)

    assert output.exists()
    assert not output.with_name("document_proof_2026-10-03T143958_proof_debug.html").exists()
