from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.core.config import get_settings

settings = get_settings()


class DocumentService:
    @staticmethod
    def load_pdf(pdf_path: str) -> List[Dict]:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        return [
            {"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs
        ]

    @staticmethod
    def split_documents(
        documents: List[Dict], chunk_size: int = None, chunk_overlap: int = None
    ) -> List[Dict]:
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap

        doc_objects = [
            Document(page_content=doc["page_content"], metadata=doc["metadata"])
            for doc in documents
        ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(doc_objects)

        return [
            {"page_content": chunk.page_content, "metadata": chunk.metadata}
            for chunk in chunks
        ]
