import os
from typing import List, Tuple
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain.retrievers import EnsembleRetriever
from .vector_store import get_vector_store

def get_llm():
    """
    Initializes the Groq LLM via the OpenAI client (free tier).
    Requires GROQ_API_KEY environment variable.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    return ChatOpenAI(
        model="llama3-8b-8192", # Groq's stable Llama 3 8B model
        openai_api_key=api_key,
        openai_api_base="https://api.groq.com/openai/v1",
        temperature=0.3
    )

def get_retriever():
    """
    Returns the ensemble retriever (vector store + tavily).
    """
    vector_store = get_vector_store()
    vs_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    try:
        tavily_retriever = TavilySearchAPIRetriever(k=3)
        ensemble_retriever = EnsembleRetriever(
            retrievers=[vs_retriever, tavily_retriever],
            weights=[0.5, 0.5]
        )
        return ensemble_retriever
    except Exception as e:
        print(f"Warning: Failed to initialize Tavily retriever (check TAVILY_API_KEY): {e}")
        return vs_retriever

def create_rag_chain():
    """
    Creates the history-aware RAG pipeline chain using standard LCEL.
    """
    llm = get_llm()
    retriever = get_retriever()
    
    # Contextualize question prompt
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # Create the history-aware retriever
    history_aware_retriever = (
        RunnablePassthrough.assign(
            contextualized_input=contextualize_q_prompt | llm | StrOutputParser()
        )
        | (lambda x: retriever.invoke(x.get("contextualized_input", x["input"])))
    )
    
    # Answer question prompt
    qa_system_prompt = (
        "You are an expert AI assistant tasked with answering questions based on the provided context.\n"
        "Use the following pieces of retrieved context to answer the question.\n"
        "If you don't know the answer based on the context, just say that you don't know. "
        "Do not make up information.\n"
        "Provide detailed, structured, and clear answers.\n\n"
        "Context:\n{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    def get_context(inputs):
        # We invoke the retriever and keep the docs to return them alongside the answer
        docs = history_aware_retriever.invoke(inputs)
        return docs
    
    # The final RAG chain using LCEL
    rag_chain = RunnablePassthrough.assign(context=get_context).assign(
        answer=(
            RunnablePassthrough.assign(
                context=lambda x: format_docs(x["context"])
            )
            | qa_prompt
            | llm
            | StrOutputParser()
        )
    )
    
    return rag_chain

def format_chat_history(history: List[Tuple[str, str]]) -> List:
    """
    Formats the history into LangChain message objects.
    history is a list of tuples: (human_message, ai_message)
    """
    formatted_history = []
    for human, ai in history:
        formatted_history.append(HumanMessage(content=human))
        formatted_history.append(AIMessage(content=ai))
    return formatted_history
