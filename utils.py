import tiktoken


enc = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def truncate_tokens(text: str) -> str:
    return enc.decode(enc.encode(text)[:limit])



import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()


# Add user 
def add_user(user_id):
    c.execute('INSERT INTO user VALUES (?)', (user_id,))
    conn.commit()

# Add conversation
def add_conversation(conversation_id, user_id):
    c.execute('INSERT INTO conversations VALUES (?, ?, 0)', 
              (conversation_id, user_id))
    conn.commit()


# Get past convos by user
def get_conversations(user_id):
    c.execute('SELECT * FROM conversations WHERE user_id=?', (user_id,))
    return c.fetchall()  
    

# Check if this is a new convo
def is_new_conversation(conversation_id):
    c.execute('SELECT * FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    return len(result) == 0


def increment_message_counter(conversation_id):
    c.execute('UPDATE conversations SET message_count = message_count + 1 WHERE conversation_id=?', (conversation_id,))
    conn.commit()


def get_message_counter(conversation_id):
    c.execute('SELECT message_count FROM conversations WHERE conversation_id=?', (conversation_id,))
    result = c.fetchall()
    return result[0][0]  # Return the first (only) result