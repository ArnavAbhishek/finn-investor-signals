import fitz
import pytest
from app.services.research import ResearchStore, validate_ticker, fetch_public_pdf


def sample_pdf():
    doc=fitz.open()
    page=doc.new_page()
    page.insert_text((40,70),'EXAMPLE - FICTIONAL COMPANY SOURCE DOCUMENT')
    page.insert_text((40,100),'Management expects revenue growth of 18 to 20 percent in FY2026.')
    page.insert_text((40,130),'Free cash flow declined as inventory rose despite higher profit.')
    data=doc.tobytes()
    doc.close()
    return data


def test_index_retrieve_and_deduplicate(tmp_path,monkeypatch):
    store=ResearchStore(tmp_path)
    data=sample_pdf()
    d=store.add_pdf('DEMOCO','training.pdf','annual_report',data)
    assert d['pages']==1
    assert store.add_pdf('DEMOCO','training.pdf','annual_report',data)['id']==d['id']
    docs=store.list_docs('DEMOCO')
    assert len(docs)==1
    findings=store.evidence('DEMOCO','What does management expect for revenue growth?')
    assert findings and findings[0]['page']==1
    assert findings[0]['document_id']==d['id']
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    answer=store.analyze('DEMOCO','What does management expect for revenue growth?')
    assert answer['mode']=='extractive'
    assert len(answer['evidence'])>0
    assert 'No AI-synthesised answer' in answer['answer']


def test_rejects_invalid_pdfs(tmp_path):
    store=ResearchStore(tmp_path)
    with pytest.raises(ValueError):
        store.add_pdf('TEST','abc.pdf','annual_report',b'Not a PDF')
    with pytest.raises(ValueError):
        store.add_pdf('TEST','abc.pdf','untrusted_report',sample_pdf())
    with pytest.raises(ValueError):
        validate_ticker('../etc')
    with pytest.raises(ValueError):
        fetch_public_pdf('http://127.0.0.1/report.pdf')
