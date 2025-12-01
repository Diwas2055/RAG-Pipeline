from fastapi import APIRouter, HTTPException
from src.api.schemas import (
    TaskResponse,
    QueryRequest,
    QueryResponse,
    RAGPipelineRequest,
    RAGPipelineResponse,
)
from src.tasks.document_tasks import load_pdf_task, split_documents_task
from src.tasks.vectorstore_tasks import create_vectorstore_task
from src.tasks.rag_tasks import query_vectorstore_task
from src.core.queues import get_queue_for_task

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])


@router.post("/pipeline", response_model=RAGPipelineResponse)
async def run_rag_pipeline(request: RAGPipelineRequest):
    try:
        # Load PDF
        pdf_queue = get_queue_for_task("tasks.load_pdf")
        pdf_task = load_pdf_task.apply_async(args=[request.pdf_path], queue=pdf_queue)
        pdf_result = pdf_task.get()

        if pdf_result["status"] == "error":
            raise HTTPException(status_code=400, detail=pdf_result["message"])

        # Split documents
        split_queue = get_queue_for_task("tasks.split_documents")
        transform_task = split_documents_task.apply_async(
            args=[pdf_result["documents"], request.chunk_size, request.chunk_overlap],
            queue=split_queue,
        )
        transform_result = transform_task.get()

        if transform_result["status"] == "error":
            raise HTTPException(status_code=400, detail=transform_result["message"])

        # Create vectorstore
        vectorstore_queue = get_queue_for_task("tasks.create_vectorstore")
        vectorstore_task = create_vectorstore_task.apply_async(
            args=[transform_result["chunks"], request.persist_directory],
            queue=vectorstore_queue,
        )

        return RAGPipelineResponse(
            status="vectorstore_task_running",
            message="PDF and transform tasks completed. Vectorstore creation in progress.",
            task_ids={
                "pdf_task_id": pdf_task.id,
                "transform_task_id": transform_task.id,
                "vectorstore_task_id": vectorstore_task.id,
            },
            pipeline_config=request.dict(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.post("/query", response_model=TaskResponse)
async def query_vectorstore(request: QueryRequest):
    query_queue = get_queue_for_task("tasks.query_vectorstore")
    query_task = query_vectorstore_task.apply_async(
        kwargs=request.dict(), queue=query_queue
    )
    return TaskResponse(
        task_id=query_task.id,
        status="started",
        message="Query task started. Use /tasks/status/{task_id} to check progress.",
    )


@router.post("/query/sync", response_model=QueryResponse)
async def query_vectorstore_sync(request: QueryRequest):
    query_queue = get_queue_for_task("tasks.query_vectorstore")
    query_task = query_vectorstore_task.apply_async(
        kwargs=request.dict(), queue=query_queue
    )
    result = query_task.get()

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return QueryResponse(**result)
