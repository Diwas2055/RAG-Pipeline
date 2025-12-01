from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None


class ProcessDataRequest(BaseModel):
    data: str = Field(..., description="Data to process")


class AddNumbersRequest(BaseModel):
    x: int = Field(..., description="First number")
    y: int = Field(..., description="Second number")


class DivideNumbersRequest(BaseModel):
    dividend: int = Field(..., description="Number to be divided")
    divisor: int = Field(..., description="Number to divide by")


class ChainCalculationRequest(BaseModel):
    x: int = Field(..., description="First number for addition")
    y: int = Field(..., description="Second number for addition")
    divisor: int = Field(..., description="Number to divide the sum by")


class ParallelCalculationRequest(BaseModel):
    x: int = Field(..., description="First number")
    y: int = Field(..., description="Second number")
    z: int = Field(..., description="Third number")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask about the document")
    persist_directory: str = Field(
        default="./storage/vectorstores/default", description="Vectorstore directory"
    )
    top_k: int = Field(
        default=3, ge=1, le=10, description="Number of chunks to retrieve"
    )


class QueryResponse(BaseModel):
    status: str
    question: str
    answer: Optional[str] = None
    retrieved_chunks: List[Dict] = []
    sources: List[str] = []
    context_used: Optional[int] = None


class RAGPipelineRequest(BaseModel):
    pdf_path: str = Field(..., description="Path to PDF file")
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    persist_directory: str = Field(default="./storage/vectorstores/default")


class RAGPipelineResponse(BaseModel):
    status: str
    message: str
    task_ids: Dict[str, Optional[str]]
    pipeline_config: Dict[str, Any]
