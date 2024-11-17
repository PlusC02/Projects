## Overview

RAG (Retrieval-Augmented Generation) is an AI technique that enhances large language models (LLM) by dynamically fetching relevant external information before generating a response. Instead of relying solely on pre-trained knowledge.

In this Project, a RAG Chatbot reads the pdf in the premade, dedicated directory and generate corresponding response based on user input and the stored 

## Hightlights

- **Streamlit**: The application is realised as an web application via Streamlit, providing an simple, neat, tidy interface for users
- **Chroma DataBase**: Chroma Database(DB) is used to store the vector embedding of the uploaded pdf for llm to retrieve the relevant content
- **Embedding models**: "nomic-embed-text" is a embedding model from llama to represent semantic meaning for a given sequence of text
- **Large Language Model**: Ollam3.2-3b is used as the Chatbot. Despite less parameter, the model is more friendly to computer with less resources
- **LangChain**: Langchain is a framework to build applications based on LLMs. RAG is realised based on Langchain.

## Pre-requisite

Some package would need to installed before running the script.

A requirement.txt would be provided soon.
