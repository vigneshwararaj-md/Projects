import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS


def clean_text(text):
    """Remove problematic unicode characters"""
    text = re.sub(r'[\ud800-\udfff]', '', text)
    return text.encode('ascii', 'ignore').decode('ascii')


class RAGTutor:
    def __init__(self):
        print("Connecting to Ollama...")
        # nomic-embed-text for embeddings (purpose-built for this)
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        # llama3.2 for generating answers
        self.llm = ChatOllama(model="llama3.2:1b", temperature=0.7)
        self.vectorstore = None
        print("RAGTutor ready!")

    def process_pdf(self, pdf_file_path):
        print(f"Loading PDF: {pdf_file_path}")
        loader = PyPDFLoader(pdf_file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages")

        for doc in documents:
            doc.page_content = clean_text(doc.page_content)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
        )
        texts = text_splitter.split_documents(documents)
        print(f"Created {len(texts)} chunks")

        self.vectorstore = FAISS.from_documents(texts, self.embeddings)
        print("PDF processing done!")
        return len(texts)

    def ask_question(self, question):
        if not self.vectorstore:
            return "No document loaded."
        
        try:
            docs = self.vectorstore.similarity_search(question, k=3)
            context = "\n\n".join([d.page_content for d in docs])

            prompt = f"""Answer based ONLY on this context. If not found, say so.

Context:
{context}

Question: {question}

Answer:"""

            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"