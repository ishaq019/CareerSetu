from app.ai.rag.ingestion import chunk_document
from app.ai.llm.schemas import GroundedAnswer

def test_page_aware_chunking_is_stable_shape():
    chunks = chunk_document("React interview questions and answers.", "guide.pdf", pages=[{"page": 3, "text": "React interview questions and answers."}])
    assert chunks[0].page == 3
    assert chunks[0].topic in {"interview", "general"}

def test_grounded_schema_requires_machine_readable_contract():
    result = GroundedAnswer(answer="Supported answer", confidence="high", citations=[1])
    assert result.citations == [1]
