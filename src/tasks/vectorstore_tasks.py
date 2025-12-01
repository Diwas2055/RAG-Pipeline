from src.core.celery_app import celery_app
from src.services.vectorstore_service import VectorStoreService


@celery_app.task(name="tasks.create_vectorstore", bind=True)
def create_vectorstore_task(self, chunks: list, persist_directory: str):
    try:
        result = VectorStoreService.create_vectorstore(chunks, persist_directory)
        return {
            "status": "success",
            "message": f"Successfully created vectorstore with {result['chunk_count']} chunks",
            "vectorstore_path": persist_directory,
            **result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating vectorstore: {str(e)}",
            "vectorstore_path": None,
            "chunk_count": 0,
        }
