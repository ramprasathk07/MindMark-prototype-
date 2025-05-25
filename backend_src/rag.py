import json
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.runnables import RunnablePassthrough
import sqlite3

from logger_config import logging

def initialize_RAG(documents,question):
    logging.info(f"Starting RAG setup")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model="nomic-embed-text:latest"),
        collection_name="local-rag"
    )

    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI assistant tasked with analyzing a student's performance in competitive exams, specifically JEE-based assessments. 
        Given the provided student data, generate five insightful queries that focus on the following aspects of the student's performance:
        - Identification of weak areas in Chemistry,Physics and Mathematics.
        - Strengths across all subjects.
        - Actionable recommendations for improvement in Mathematics.
        - Effective time management strategies.
        - Analysis of common mistakes and suggestions to mitigate them.

        Student data: {question}

        Please provide the queries in a clear, concise format, separated by newlines.
        """
    )

    # Create retriever using MultiQueryRetriever
    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(search_kwargs={"k": 30}),  # Retrieve top 30 documents
        llm=ChatOllama(model="qwen2.5:7b"),
        prompt=QUERY_PROMPT
    )

    response_template = """Answer the question based ONLY on the following context:
    {context}
    Question: {question}
    """
    response_prompt = ChatPromptTemplate.from_template(response_template)

    # Set up chain for retrieval and LLM interaction
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | response_prompt
        | ChatOllama(model="qwen2.5:7b")
        | StrOutputParser()
    )

    results = chain.invoke(question)

    return results 

def start_RAG(json_file:str,
              question:str):
    with open(json_file, 'r') as f:
        data = json.load(f)

    documents = [
        Document(
            page_content=f"Question: {item.get('Question', 'NA')}\n"
                        f"Explanation: {item.get('Explanation', 'NA')}\n"
                        f"Explanation for the option choosed: {item.get('Explanation for the option choosed', 'NA')}"
                        f"Feedback: {item.get('Common Misconceptions', item.get('Positive_Performance_Highlights', 'NA'))}",
            metadata={
                "Question Number": item.get("Question Number", "NA"),
                "Subject": item.get("Subject", "NA"),
                "Topic": item.get("Topic", "NA"),
                "Taxonomy": item.get("Taxonomy", "NA"),
                "Difficulty": item.get("Difficulty", "NA")
            }
        )
        for item in data
    ]
    logging.info(f"Initializing RAG setup")
    answer = initialize_RAG(documents=documents,
                        question=question)

    return answer