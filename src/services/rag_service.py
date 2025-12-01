from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.services.vectorstore_service import VectorStoreService
from src.core.config import get_settings

settings = get_settings()


class RAGService:
    @staticmethod
    def query(question: str, persist_directory: str, top_k: int = None) -> Dict:
        top_k = top_k or settings.retrieval_top_k

        db = VectorStoreService.load_vectorstore(persist_directory)

        if db._collection.count() == 0:
            raise ValueError(f"Vectorstore at {persist_directory} is empty")

        retriever = db.as_retriever(search_kwargs={"k": top_k})
        retrieved_docs = retriever.get_relevant_documents(question)

        if not retrieved_docs:
            raise ValueError("No relevant documents found")

        llm = ChatOpenAI(model=settings.llm_model, temperature=settings.llm_temperature)

        prompt = ChatPromptTemplate.from_template(
            """
Answer the following question based on the provided context.
Think step by step before providing an answer. Just say "I don't know" 
if you're not sure of an answer.

<context>
{context}
</context>

Question: {question}
"""
        )

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        answer = rag_chain.invoke(question)

        retrieved_chunks = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in retrieved_docs
        ]

        sources = list(
            set(doc.metadata.get("source", "Unknown") for doc in retrieved_docs)
        )

        return {
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "sources": sources,
            "context_used": len(retrieved_docs),
        }
