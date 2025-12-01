from src.core.celery_app import celery_app
from src.services.document_service import DocumentService


@celery_app.task(name="tasks.load_pdf", bind=True)
def load_pdf_task(self, pdf_path: str):
    try:
        documents = DocumentService.load_pdf(pdf_path)
        return {
            "status": "success",
            "message": f"Successfully loaded {len(documents)} pages",
            "documents": documents,
            "doc_count": len(documents),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error loading PDF: {str(e)}",
            "documents": [],
            "doc_count": 0,
        }


@celery_app.task(name="tasks.split_documents", bind=True)
def split_documents_task(
    self, documents: list, chunk_size: int = None, chunk_overlap: int = None
):
    try:
        chunks = DocumentService.split_documents(documents, chunk_size, chunk_overlap)
        return {
            "status": "success",
            "message": f"Successfully created {len(chunks)} chunks",
            "chunks": chunks,
            "chunk_count": len(chunks),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error splitting documents: {str(e)}",
            "chunks": [],
            "chunk_count": 0,
        }
