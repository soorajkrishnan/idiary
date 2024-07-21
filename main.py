import streamlit as st
import json
import uuid
from sqlalchemy import text, exc
from backend.src.genai.main import chat_with_memory, summaries_chat, get_model_info
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")

conn = st.connection("memory", type="sql", ttl=0)

st.markdown("""<style>
    
    .stChatMessage{
    border-radius:20px;
    backgound-color:rgba(38, 39, 48, 0.0) !important;
    
    }
    div[data-testid="stChatMessageContent"]{
        padding: 1em 1em 1em 2em;
        margin-top:.8em;
        border-radius: 0 18px 18px 18px ;
        line-height: 1.5;
        border: 1px solid aqua;
    
    }
    div[data-testid="chatAvatarIcon-assistant"]{
        backdrop-filter: blur(2px);
        height:2.5em;
        width:2.5em;
        border-radius: 24px;
        
    }
    div[data-testid="chatAvatarIcon-user"]{
        backdrop-filter: blur(2px);
        height:2.5em;
        width:2.5em;
        border-radius: 24px;
        
    }
    div[data-testid="stBottomBlockContainer"]{
        padding: .75em;
        
    }
    </style>""",unsafe_allow_html=True)

def load_chat_sessions():
    """
    Load all distinct chat session IDs from the message store.

    Returns:
        DataFrame: A DataFrame containing distinct session IDs.
    """
    return conn.query("SELECT DISTINCT session_id FROM message_store;")


def load_chat_messages(session_id):
    """
    Load all messages for a given chat session.

    Args:
        session_id (str): The ID of the chat session.

    Returns:
        DataFrame: A DataFrame containing messages for the specified session.
    """
    return conn.query(
        f"SELECT message FROM message_store WHERE session_id='{session_id}';"
    )


def display_chat(session_id):
    """
    Display the chat messages for a given session in the Streamlit app.

    Args:
        session_id (str): The ID of the chat session to display.
    """
    messages = load_chat_messages(session_id)
    for message in messages["message"].to_list():
        message = json.loads(message)
        if message:
            st.chat_message(message["type"]).write(message["data"]["content"])


def chat(session_id):
    """
    Handle user input and display chat messages. Also generates a response using the chat_with_memory function.

    Args:
        session_id (str): The ID of the chat session to associate with the user input.
    """
    st.session_state.selectbox_options = options.append(session_id)
    
    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("human").write(prompt)
        st.cache_data.clear()
        response = chat_with_memory(prompt, session_id)
        st.chat_message("ai").write(response)
    


def delete_chat():
    """
    Delete the current chat session from the message store.
    """
    session_id = st.session_state.current_session_id
    with conn.session as session:
        try:
            session.execute(
                text("DELETE FROM message_store WHERE session_id = :session_id"),
                {"session_id": session_id},
            )
            session.commit()
            st.toast("Chat deleted successfully")
            st.cache_data.clear()
            st.session_state.current_session_id = None
        except exc.OperationalError as e:
            st.error(f"Error deleting chat: {e}")


if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None


def on_session_select():
    """
    Handle session selection changes in the sidebar. Creates a new chat session if 'New Chat' is selected.
    """
    selected = st.session_state.session_selector
    if selected == "New Chat":
        new_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_id
        st.session_state.session_selector = new_id  # Update dropdown
    else:
        st.session_state.current_session_id = selected


st.sidebar.title("Chat Sessions")

session_ids = load_chat_sessions()
options = (
    ["New Chat"] + session_ids["session_id"].tolist()
    if not session_ids.empty
    else ["New Chat"]
)

if (
    st.session_state.current_session_id
    and st.session_state.current_session_id not in options
):
    options.append(st.session_state.current_session_id)

selected_session = st.sidebar.selectbox(
    "Select Chat",
    options=options,
    index=(
        options.index(st.session_state.current_session_id)
        if st.session_state.current_session_id in options
        else 0
    ),
    key="session_selector",
    placeholder="Choose a chat",
    on_change=on_session_select,
    help="Choose a chat, If not found click on refresh",
)

col1, col2 = st.sidebar.columns(2)

col1.button("Refresh", on_click=lambda: st.cache_data.clear(), use_container_width=True)
col2.button(
    "Delete",
    on_click=delete_chat,
    disabled=selected_session == "New Chat",
    use_container_width=True,
)

col3 = st.sidebar.columns(1, vertical_alignment="center")

def summaries_chat_ui():
    with st.sidebar.status(
        "Generating summary...",
    ):
        st.sidebar.write(
            f"## Summary \n{summaries_chat(st.session_state.current_session_id)}"
        )


col3[0].button(
    "Summaries Chat",
    on_click=summaries_chat_ui,
    disabled=selected_session == "New Chat",
    use_container_width=True,
)


@st.experimental_dialog("Model Info")
def info():
    with st.container(border=True):
        st.write(get_model_info())

if st.sidebar.button("🤖"):
        info()

if st.session_state.current_session_id:
    display_chat(st.session_state.current_session_id)

chat(st.session_state.current_session_id or str(uuid.uuid4()))
