from app.modules.documents.service import extract_text

def test_docx_extraction(tmp_path):
    from docx import Document
    p = tmp_path / "resume.docx"
    doc = Document(); doc.add_paragraph("React FastAPI PostgreSQL developer"); doc.save(p)
    text = extract_text(p.name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", p.read_bytes())
    assert "React" in text
