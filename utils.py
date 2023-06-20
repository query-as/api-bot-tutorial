import tiktoken
import time
from fastapi_poe.types import QueryRequest, ProtocolMessage
from fastapi_poe.client import MetaMessage, stream_request

enc = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def truncate_tokens(text: str, limit: int) -> str:
    return enc.decode(enc.encode(text)[:limit])


async def query_llm(query, prompt):
    message = ProtocolMessage(
        role="user",
        content=prompt,
        version = query.version, 
        type=query.type,
    )

    query = QueryRequest(
        query = [message],
        user_id = query.user_id,
        conversation_id = query.conversation_id,
        message_id = query.message_id,
        api_key = query.api_key,
        version = query.version, 
        type=query.type
    )

    try:
        response = ""
        async for msg in stream_request(query, "sage", query.api_key):
            response += msg.text
    # one retry
    except Exception as e:
        time.sleep(1)
        response = ""
        async for msg in stream_request(query, "sage", query.api_key):
            response += msg.text
    
    return response



import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

from enum import Enum

class State(Enum):
    requesting_topic = 0
    asking_questions = 1

from collections import namedtuple
Trivia = namedtuple('Trivia', ['id', 'article', 'question', 'answer'])


# Add user 
def add_user(user_id):
    c.execute('INSERT INTO user VALUES (?)', (user_id,))
    conn.commit()

# Add conversation
def add_conversation(conversation_id, user_id):
    c.execute('INSERT INTO conversations VALUES (?, ?, 0, 0, NULL)', 
              (conversation_id, user_id))
    conn.commit()
    

# Check if this is a new convo
def is_new_conversation(conversation_id):
    c.execute('SELECT * FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    return len(result) == 0

# Update state
def update_state(conversation_id, state, article=None):
    c.execute('UPDATE conversations SET state=? WHERE conversation_id=?', 
              (state.value, conversation_id))
    c.execute('UPDATE conversations SET state_idx = 0 WHERE conversation_id=?', (conversation_id,))
    if article is not None:
        c.execute('UPDATE conversations SET article=? WHERE conversation_id=?', 
              (article, conversation_id))
    conn.commit()

def get_state(conversation_id):
    c.execute('SELECT state FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    state_int = result[0][0]  # Get state integer from result
    
    # Map state int to State Enum member and return 
    return State(state_int)


def get_state_idx(conversation_id):
    c.execute('SELECT state_idx FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    return result[0][0]  # Get state integer from result


def add_article(title):
    try:
        c.execute('INSERT INTO article (title) VALUES (?)', (title,))
        conn.commit()
    except Exception as e:
        print(e)


def add_trivia(article, question, answer):
    c.execute('INSERT INTO trivia (article, question, answer) VALUES (?, ?, ?)', 
              (article, question, answer))
    conn.commit()


def get_trivia(key):
    c.execute('SELECT * FROM trivia WHERE article=?', (key,))
    result = c.fetchall()
    return [Trivia(*row) for row in result]
    

def get_current_title(conversation_id):
    c.execute('SELECT article FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    return result[0][0]

def increment_state_idx(conversation_id):
    c.execute('UPDATE conversations SET state_idx = state_idx + 1 WHERE conversation_id=?', (conversation_id,))
