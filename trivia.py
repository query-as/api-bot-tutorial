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
from utils import (
    is_new_conversation, add_conversation, get_state, update_state, State, add_article, add_trivia,
    get_trivia, get_current_title, get_state_idx, increment_state_idx, query_llm)
from prompts import TRIVIA_PROMPT, INTRO_MESSAGE, REQUEST_TOPIC, GRADING_PROMPT

QUESTION_COUNT = 5

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
            yield self.text_event(INTRO_MESSAGE)
        else:
            if get_state(query.conversation_id) == State.requesting_topic:
                # user is setting up game
                title = await self.get_wiki_link(query)
                update_state(query.conversation_id, State.asking_questions, title)
                yield self.text_event(f"Sure! I'll ask you questions about {title}. Give me a moment while I check Wikipedia...")
                await self.create_trivia(query, title)
                
                # ask their first question
                yield self.text_event(f"\n\nOkay! I have {QUESTION_COUNT} questions for you. Let's begin.\n\n")
                question, _ = self.get_nth_trivia(query.conversation_id, 0)
                increment_state_idx(query.conversation_id)
                yield self.text_event(question)
            else:
                # grade their response to the last question
                idx = get_state_idx(query.conversation_id)

                grade = await self.grade_answer(query, idx)
                yield self.text_event(grade)

                if idx >= QUESTION_COUNT:
                    update_state(query.conversation_id, State.requesting_topic)
                    yield self.text_event(REQUEST_TOPIC)

                else:
                    # ask a new question
                    question, _ = self.get_nth_trivia(query.conversation_id, idx)

                    increment_state_idx(query.conversation_id)
                    yield self.text_event(response)


    async def grade_answer(self, query, idx):
        return "grade answer\n\n"
        user_answer = query.query[-1].content
        question, answer = get_single_trivia(query.conversation_id, idx)

        prompt = GRADING_PROMPT.format(
            question = question,
            answer = answer,
            user_answer = user_answer,
        )

        last_message = query.query[-1]
        last_message.content = prompt

        query.query = [last_message]

        response = ""
        async for msg in stream_request(query, "sage", query.api_key):
            response += msg.text

        return response + "\n\n"


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


    async def create_trivia(self, query: QueryRequest, title: str) -> AsyncIterable[ServerSentEvent]:
        add_article(title+"_"+query.conversation_id)
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
        
        article_key = title + "_" + query.conversation_id
        for trivia in trivia_questions:
            add_trivia(article_key, trivia['question'], trivia['answer'])
        

    def get_nth_trivia(self, conversation_id, n):
        title = get_current_title(conversation_id)
        all_trivia = get_trivia(title+"_"+conversation_id)
        return all_trivia[n].question, all_trivia[n].answer


if __name__ == "__main__":
    run(TriviaBot())
