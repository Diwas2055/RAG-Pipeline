from typing import List, Dict
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from src.core.config import get_settings

settings = get_settings()


class VectorStoreService:
    @staticmethod
    def create_vectorstore(chunks: List[Dict], persist_directory: str) -> Dict:
        chunk_objects = [
            Document(page_content=chunk["page_content"], metadata=chunk["metadata"])
            for chunk in chunks
        ]

        embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        db = Chroma.from_documents(
            documents=chunk_objects,
            embedding=embeddings,
            persist_directory=persist_directory,
        )

        return {
            "collection_name": db._collection.name,
            "collection_id": db._collection.id,
            "chunk_count": len(chunks),
        }

    @staticmethod
    def load_vectorstore(persist_directory: str) -> Chroma:
        embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        return Chroma(
            persist_directory=persist_directory, embedding_function=embeddings
        )
