"""

Bot for generating trivia questions from Wikipedia articles.

"""
from __future__ import annotations

from typing import AsyncIterable
import json
from fastapi_poe import PoeBot, run
from fastapi_poe.client import MetaMessage, stream_request
from fastapi_poe.types import QueryRequest, ProtocolMessage
from sse_starlette.sse import ServerSentEvent
import requests
from utils import is_new_conversation, add_conversation, increment_message_counter, get_message_counter
from prompts import TRIVIA_PROMPT, INTRO_MESSAGE

def get_article(title: str) -> str:
    """Get the plaintext content of the Wikipedia article with this title."""
    try:
        response = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts',
                'explaintext': True,
            }
        ).json()
        page = next(iter(response['query']['pages'].values()))
        return page['extract']
    except Exception as e:
        print(e)
        return "Error"


class TriviaBot(PoeBot):
    async def get_response(self, query: QueryRequest) -> AsyncIterable[ServerSentEvent]:
        if is_new_conversation(query.conversation_id):
            add_conversation(query.conversation_id, query.user_id)
            increment_message_counter(query.conversation_id)
            yield self.text_event(INTRO_MESSAGE)
        else:
            increment_message_counter(query.conversation_id)

            if get_message_counter(query.conversation_id) == 2:
                # user is setting up game
                response = await self.create_trivia(query)
                yield self.text_event(response)
            else:
                # user is playing game
                yield self.text_event(str(get_message_counter(query.conversation_id)))
                


    async def get_wiki_link(self, query: QueryRequest) -> AsyncIterable[ServerSentEvent]:
        """returns wiki link

        as an example, the query 'The website created by Adam D'Angelo' returns https://en.wikipedia.org/wiki/Quora
        """

        last_message = query.query[-1]
        content = last_message.content
        last_message.content = f"Return the link of the Wikipedia page for the query. Don't include any additional text: {content}"

        query.query = [last_message]

        wiki_link = ""
        async for msg in stream_request(query, "sage", query.api_key):
            wiki_link += msg.text
        
        wiki_title = wiki_link.split("/")[-1]
        
        return wiki_title


    async def create_trivia(self, query: QueryRequest) -> AsyncIterable[ServerSentEvent]:
        title = await self.get_wiki_link(query)
        article_text = get_article(title)
        
        prompt = TRIVIA_PROMPT.format(
            title = title,
            article_text = article_text[:4000]
        )
        last_message = query.query[-1]
        last_message.content = prompt

        query.query = [last_message]

        trivia_questions = ""
        async for msg in stream_request(query, "sage", query.api_key):
            trivia_questions += msg.text
        trivia_questions = json.loads(trivia_questions)
        
        response_str = ""
        for i, question in enumerate(trivia_questions):
            response_str += f"Question {str(i+1)}. {question['question']}\n"
            response_str += f"Answer {str(i+1)}. {question['answer']}\n\n"
        
        return response_str.strip()
        


if __name__ == "__main__":
    run(TriviaBot())
