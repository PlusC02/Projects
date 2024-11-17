from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever,create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import convert_to_messages
import streamlit as st
import os

st.title("RAG Chatbot Chem v2")

def createVectorDB(folder_path):
    # Load all pdf from the folder path
    loaders = [PyPDFLoader(os.path.join(folder_path,file)) for file in os.listdir(folder_path) if file.endswith(".pdf")]
    
    # Loead each pdf
    # Split each pdf
    # Concatenate to one list
    # Embed to VectorDB
    all_documents = []

    for loader in loaders:
        # load each pdf
        raw_document = loader.load()

        # Splitter for chunks
        text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

        # Splitted document and concatenate them
        documents = text_splitter.split_documents(raw_document)
        all_documents.extend(documents)

    # Embedding model
    local_embeddings = OllamaEmbeddings(model="nomic-embed-text")

    if not os.path.exists(os.path.join(os.path.dirname(__file__),"/vectordb1")):
        os.makedirs(os.path.join(os.path.dirname(__file__),"/vectordb1"))

    # Resulting vectorDB
    vectorstore = Chroma.from_documents(
        documents=all_documents, 
        embedding=local_embeddings, 
        persist_directory=os.path.join(os.path.dirname(__file__),"/vectordb1"),
        collection_name='v_db')
    return vectorstore.as_retriever(search_kwargs={"k":3})

#if "vector_db" not in st.session_state:
#    st.session_state.vector_db = createVectorDB(os.path.join(os.getcwd(),"LLMenv/resources"))
#    print("Finish for DB")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "retriever" not in st.session_state: 
    st.session_state.retriever = createVectorDB(os.path.join(os.path.dirname(__file__),"/resources"))


def RAG_Stream(prompt):

    #vector_db = st.session_state.vector_db
    #vector_db = createVectorDB(os.path.join(os.getcwd(),"LLMenv/resources"))
    messages = st.session_state.messages

    llm = ChatOllama(model="llama3.2")
    
    retriever = st.session_state.retriever
    #print(retriever.invoke("Organic"))
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

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    ### Answer question ###
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)


    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


    if messages == []:
        chat_history = []
    else:
        chat_history = [tuple(x.values()) for x in messages]
        #return(messages)
        chat_history = convert_to_messages(chat_history)

    def get_answer_from_stream():
        for chunk in rag_chain.stream({"input": prompt , "chat_history": chat_history}):
                if answer_chunk := chunk.get("answer"):
                    yield answer_chunk

    response= st.chat_message("assistant").write_stream(get_answer_from_stream())
    #print(response)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if __name__ == "__main__":
    if prompt:= st.chat_input():
        st.chat_message("user").write(prompt)
        RAG_Stream(prompt)