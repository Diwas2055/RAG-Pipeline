from src.core.celery_app import celery_app
from src.services.rag_service import RAGService


@celery_app.task(name="tasks.query_vectorstore", bind=True)
def query_vectorstore_task(
    self, question: str, persist_directory: str, top_k: int = None
):
    try:
        result = RAGService.query(question, persist_directory, top_k)
        return {"status": "success", "question": question, **result}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error querying vectorstore: {str(e)}",
            "answer": None,
            "retrieved_chunks": [],
            "sources": [],
        }
