from dotenv import load_dotenv

load_dotenv()

from langchain_community.llms.ollama import Ollama
from langchain_community.
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate


def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, "sqlite:///memory.db")

llm = Ollama(model="llama3",temperature=0)
llm.bind()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You're an intelligent assistant",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

runnable = prompt | llm


def chat_with_memory(message, session):

    runnable_with_history = RunnableWithMessageHistory(
        runnable,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    return runnable_with_history.invoke(
        {"input": message},
        config={"configurable": {"session_id": session}},
    )


def get_model_info():
    return vars(llm)


def summaries_chat(session_id):
    docs = get_session_history(session_id).get_messages()
    prompt_template = """Write a concise summary in under 50 words of the following chat, Just keep the summary:
    "{text}"
    CHAT SUMMARY:"""
    prompt = PromptTemplate.from_template(prompt_template)
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    result = llm_chain.invoke({"text": docs})["text"]
    return result
