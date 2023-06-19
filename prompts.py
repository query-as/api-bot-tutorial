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