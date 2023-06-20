TRIVIA_PROMPT = """Consider the text of the following Wikipedia article:
Title: <title>{title}</title>
Content: <content>{article_text}</content>

Write 5 trivia questions about the contents of the article. 

Your response should be a list of JSON objects. The text should be formatted in Common Markdown. For example:
[
    {{
        "question": "Who wrote the book *Great Expectations*?",
        "answer": "Charles Dickens"
    }},
    ...
]"""

INTRO_MESSAGE = """
Welcome to TriviaBot!

To start out, please describe the topic you are interested in trivia about. Then I will ask you trivia questions about it!
"""

REQUEST_TOPIC = """\n\nThat's all the questions I had.\n\nWhat else would you like to hear trivia questions about?"""


GRADING_PROMPT = """Consider the following trivia question:

Question: <question>{question}</question>
Expected answer: <answer>{answer}</answer>

A person gave this answer to that question:
Answer: <answer>{user_answer}</answer>

Is that answer correct? Tell them (in the second person) why or why not. Be generous in your grading, not pedantic. Use a kind tone and keep your response relatively short."""