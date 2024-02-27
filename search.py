import argparse
import concurrent.futures
import datetime
import glob
import json
import os
import re
import threading
import traceback
from typing import List, Generator, Optional

import httpx
import leptonai
import requests
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from leptonai import Client
from leptonai.api.workspace import WorkspaceInfoLocalRecord
from leptonai.kv import KV
from leptonai.photon import Photon, StaticFiles
from leptonai.photon.types import to_bool
from leptonai.util import tool
from loguru import logger
from duckduckgo_search import DDGS

try:
    from typing import Annotated
except ImportError:
    # Python 3.8 compatibility, need `pip install typing-extensions`
    from typing_extensions import Annotated

################################################################################
# Constant values for the RAG model.
################################################################################

# Search engine related. You don't really need to change this.
BING_SEARCH_V7_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
BING_MKT = "en-US"
GOOGLE_SEARCH_ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"
SERPER_SEARCH_ENDPOINT = "https://google.serper.dev/search"
SEARCHAPI_SEARCH_ENDPOINT = "https://www.searchapi.io/api/v1/search"

# Specify the number of references from the search engine you want to use.
# 8 is usually a good number.
REFERENCE_COUNT = 8

# Specify the default timeout for the search engine. If the search engine
# does not respond within this time, we will return an error.
DEFAULT_SEARCH_ENGINE_TIMEOUT = 5

# If the user did not provide a query, we will use this default query.
_default_query = "Who said 'live long and prosper'?"

# A set of stop words to use - this is not a complete set, and you may want to
# add more given your observation.
lepton_stop_words = [
    "<|im_end|>",
    "[End]",
    "[end]",
    "\nReferences:\n",
    "\nSources:\n",
    "End.",
]

# This is really the most important part of the rag model. It gives instructions
# to the model on how to generate the answer. Of course, different models may
# behave differently, and we haven't tuned the prompt to make it optimal - this
# is left to you, application creators, as an open problem.
_rag_system_prompt = """You are a large language AI assistant. You are given a user question, and please write clean, concise and accurate answer to the question. You will be given a set of related contexts to the question, each starting with a reference number like [[citation:x]], where x is a number. Please use the context and cite the context at the end of each sentence if applicable.

Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. Please keep your answer within 1024 tokens. If the provided context does not offer enough information, please use your own knowledge to answer the user question.

Please cite the contexts with the reference numbers, in the format [citation:x]. If a sentence comes from multiple contexts, please list all applicable citations, like [citation:3][citation:5]. Other than code and specific names and citations, your answer must be written in the same language as the question.
"""

_rag_system_prompt_zh = """你是一个大型的语言AI助手。当用户提出问题时，请你写出清晰、简洁且准确的答案。我们会给你一组与问题相关的上下文，每个上下文都以类似[[citation:x]]这样的引用编号开始，其中x是一个数字。如果适用，请在每句话后面使用并引述该上下文。

你的答案必须正确、精确，并由专家以公正和专业的语气撰写。请将你的回答限制在1024个token内。如果所提供的上下文信息不足，可以使用自己知识来回答用户问题。

请按照[citation:x]格式引用带有参考编号的上下文。如果一句话来自多个上下文，请列出所有适用于此处引述，如[citation:3][citation:5]。除代码、特定名称和引述外，你必须使用与问题相同语言编写你的回答。
"""
_rag_qa_prompt = """Here are the set of contexts:

{context}
Current date: {current_date}

Please answer the question with contexts, but don't blindly repeat the contexts verbatim. Please cite the contexts with the reference numbers, in the format [citation:x]. And here is the user question:
"""
_rag_qa_prompt_zh = """以下是一组上下文：

{context}
当前日期: {current_date}

基于上下文回答问题，不要盲目地逐字重复上下文。请以[citation:x]的格式引用上下文。这是用户的问题：
"""
# This is the prompt that asks the model to generate related questions to the
# original question and the contexts.
# Ideally, one want to include both the original question and the answer from the
# model, but we are not doing that here: if we need to wait for the answer, then
# the generation of the related questions will usually have to start only after
# the whole answer is generated. This creates a noticeable delay in the response
# time. As a result, and as you will see in the code, we will be sending out two
# consecutive requests to the model: one for the answer, and one for the related
# questions. This is not ideal, but it is a good tradeoff between response time
# and quality.
_related_system_prompt = """You are a helpful assistant that helps the user to ask related questions, based on user's original question and the related contexts. Please identify worthwhile topics that can be follow-ups, and write questions no longer than 20 words each. 
Please make sure that specifics, like events, names, locations, are included in follow up questions so they can be asked standalone. Your related questions must be in the same language as the original question.

For example, if the original question asks about "the Manhattan project", in the follow up question, do not just say "the project", but use the full name "the Manhattan project". 
"""
_related_system_prompt_zh = """你是一个有用的助手，帮助用户根据他们的原始问题和相关背景提出相关问题。请确定值得跟进的主题，你给出的问题字数不超过20个token。请确保具体细节，如事件、名字、地点等都包含在后续问题中，这样它们可以单独被问到。你提出的相关问题必须与原始问题语言相同。
例如，如果原始问题询问“曼哈顿计划”，那么在后续问题中，请不要只说“该计划”，而应使用全称“曼哈顿计划”。
"""
_related_qa_prompt = """You assist users in posing relevant questions based on their original queries and related background. Please identify topics worth following up on, and write out questions that each do not exceed 20 tokens. You Can combine with historical messages. Here are the contexts of the question:

{context}

based on the original question and related contexts, suggest three such further questions. Do NOT repeat the original question. Each related question should be no longer than 20 words. Here is the original question:
"""
_related_qa_prompt_zh = """你帮助用户根据他们的原始问题和相关背景提出相关问题，可以结合历史消息。请确定值得跟进的主题，每个问题不超过20个token。以下是问题的上下文：

{context}

根据原始问题和相关上下文，提出三个相似的问题。不要重复原始问题。每个相关问题应不超过20个token。这是原始问题：
"""
# This is the prompt that asks the model to rewrite the question.
_rewrite_question_system_prompt = """Your task is to rewrite user questions. If the original question is unclear, please rewrite it to be more precise and concise (up to 20 tokens), this rewritten question will be used for information search; if the original question is very clear, there is no need to rewrite, just output the original question; if you are unsure how to rewrite, also do not need to rewrite, just output the original question.
Please rewrite the original question for Google search. Do not answer user questions.
"""
_rewrite_question_system_prompt_zh = """你的任务是改写用户问题。如果原始问题不清楚，请将其改写得更精确、简洁（最多20个token），这个改写后的问题将用于搜索信息；如果原始问题很清晰，则无需改写，直接输出原始问题；如果你不确定如何改写，也无需改写，直接输出原始问题。
你给出改写后的问题，用于谷歌搜索，不要回答用户问题。
"""

_rewrite_question_qa_prompt = """This is the original question:
"""

_rewrite_question_qa_prompt_zh = """这是原始问题：
"""

REDUCE_TOKEN_FACTOR = 0.5  # Reduce the token occupancy to less than the model upper tokens.
TOKEN_TO_CHAR_RATIO = 4  # The ratio of the number of tokens to the number of characters.
MODEL_TOKEN_LIMIT = {
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
    "gpt-3.5-turbo-1106": 16384,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-1106-preview": 128000,
    "gpt-4-vision-preview": 128000,
}


def is_chinese(uchar):
    """Check if the character is Chinese."""
    return '\u4e00' <= uchar <= '\u9fa5'


def contains_chinese(string):
    """Check if the string contains Chinese characters."""
    return any(is_chinese(c) for c in string)


def replace_today(prompt):
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    return prompt.replace("{current_date}", today)


def search_with_bing(query: str, subscription_key: str):
    """
    Search with bing and return the contexts.
    """
    params = {"q": query, "mkt": BING_MKT}
    response = requests.get(
        BING_SEARCH_V7_ENDPOINT,
        headers={"Ocp-Apim-Subscription-Key": subscription_key},
        params=params,
        timeout=DEFAULT_SEARCH_ENGINE_TIMEOUT,
    )
    if not response.ok:
        logger.error(f"{response.status_code} {response.text}")
        raise HTTPException(response.status_code, "Search engine error.")
    json_content = response.json()
    try:
        contexts = json_content["webPages"]["value"][:REFERENCE_COUNT]
    except KeyError:
        logger.error(f"Error encountered: {json_content}")
        return []
    return contexts


def search_with_google(query: str, subscription_key: str, cx: str):
    """
    Search with google and return the contexts.
    """
    params = {
        "key": subscription_key,
        "cx": cx,
        "q": query,
        "num": REFERENCE_COUNT,
    }
    response = requests.get(
        GOOGLE_SEARCH_ENDPOINT, params=params, timeout=DEFAULT_SEARCH_ENGINE_TIMEOUT
    )
    if not response.ok:
        logger.error(f"{response.status_code} {response.text}")
        raise HTTPException(response.status_code, "Search engine error.")
    json_content = response.json()
    try:
        contexts = json_content["items"][:REFERENCE_COUNT]
    except KeyError:
        logger.error(f"Error encountered: {json_content}")
        return []
    return contexts

def ddg_search_text(query: str, max_results=5):
    reference_results = []
    search_results = []
    with DDGS() as ddgs:
        ddgs_gen = ddgs.text(query, backend="lite",timelimit="d, w, m, y")
        for r in islice(ddgs_gen, max_results):
            search_results.append(r)
    for idx, result in enumerate(search_results):
        logger.debug(f"搜索结果{idx + 1}：{result}")
        if result["body"] and result["href"]:
            reference_results.append({
                    "name": result["title"],
                    "url": result["href"],
                    "snippet": result["body"]

            })
    logger.info(f"ddgs search result:{reference_results}")
    return reference_results


def search_with_serper(query: str, subscription_key: str):
    """
    Search with serper and return the contexts.
    """
    payload = json.dumps({
        "q": query,
        "num": (
            REFERENCE_COUNT
            if REFERENCE_COUNT % 10 == 0
            else (REFERENCE_COUNT // 10 + 1) * 10
        ),
    })
    headers = {"X-API-KEY": subscription_key, "Content-Type": "application/json"}
    logger.info(
        f"{payload} {headers} {subscription_key} {query} {SERPER_SEARCH_ENDPOINT}"
    )
    response = requests.post(
        SERPER_SEARCH_ENDPOINT,
        headers=headers,
        data=payload,
        timeout=DEFAULT_SEARCH_ENGINE_TIMEOUT,
    )
    if not response.ok:
        logger.error(f"{response.status_code} {response.text}")
        raise HTTPException(response.status_code, "Search engine error.")
    json_content = response.json()
    try:
        # convert to the same format as bing/google
        contexts = []
        if json_content.get("knowledgeGraph"):
            url = json_content["knowledgeGraph"].get("descriptionUrl") or json_content["knowledgeGraph"].get("website")
            snippet = json_content["knowledgeGraph"].get("description")
            if url and snippet:
                contexts.append({
                    "name": json_content["knowledgeGraph"].get("title", ""),
                    "url": url,
                    "snippet": snippet
                })
        if json_content.get("answerBox"):
            url = json_content["answerBox"].get("url")
            snippet = json_content["answerBox"].get("snippet") or json_content["answerBox"].get("answer")
            if url and snippet:
                contexts.append({
                    "name": json_content["answerBox"].get("title", ""),
                    "url": url,
                    "snippet": snippet
                })
        contexts += [
            {"name": c["title"], "url": c["link"], "snippet": c.get("snippet", "")}
            for c in json_content["organic"]
        ]
        return contexts[:REFERENCE_COUNT]
    except KeyError:
        logger.error(f"Error encountered: {json_content}")
        return []


def search_with_searchapi(query: str, subscription_key: str):
    """
    Search with SearchApi.io and return the contexts.
    """
    payload = {
        "q": query,
        "engine": "google",
        "num": (
            REFERENCE_COUNT
            if REFERENCE_COUNT % 10 == 0
            else (REFERENCE_COUNT // 10 + 1) * 10
        ),
    }
    headers = {"Authorization": f"Bearer {subscription_key}", "Content-Type": "application/json"}
    logger.info(
        f"{payload} {headers} {subscription_key} {query} {SEARCHAPI_SEARCH_ENDPOINT}"
    )
    response = requests.get(
        SEARCHAPI_SEARCH_ENDPOINT,
        headers=headers,
        params=payload,
        timeout=30,
    )
    if not response.ok:
        logger.error(f"{response.status_code} {response.text}")
        raise HTTPException(response.status_code, "Search engine error.")
    json_content = response.json()
    try:
        # convert to the same format as bing/google
        contexts = []

        if json_content.get("answer_box"):
            if json_content["answer_box"].get("organic_result"):
                title = json_content["answer_box"].get("organic_result").get("title", "")
                url = json_content["answer_box"].get("organic_result").get("link", "")
            if json_content["answer_box"].get("type") == "population_graph":
                title = json_content["answer_box"].get("place", "")
                url = json_content["answer_box"].get("explore_more_link", "")

            title = json_content["answer_box"].get("title", "")
            url = json_content["answer_box"].get("link")
            snippet = json_content["answer_box"].get("answer") or json_content["answer_box"].get("snippet")

            if url and snippet:
                contexts.append({
                    "name": title,
                    "url": url,
                    "snippet": snippet
                })

        if json_content.get("knowledge_graph"):
            if json_content["knowledge_graph"].get("source"):
                url = json_content["knowledge_graph"].get("source").get("link", "")

            url = json_content["knowledge_graph"].get("website", "")
            snippet = json_content["knowledge_graph"].get("description")

            if url and snippet:
                contexts.append({
                    "name": json_content["knowledge_graph"].get("title", ""),
                    "url": url,
                    "snippet": snippet
                })

        contexts += [
            {"name": c["title"], "url": c["link"], "snippet": c.get("snippet", "")}
            for c in json_content["organic_results"]
        ]

        if json_content.get("related_questions"):
            for question in json_content["related_questions"]:
                if question.get("source"):
                    url = question.get("source").get("link", "")
                else:
                    url = ""

                snippet = question.get("answer", "")

                if url and snippet:
                    contexts.append({
                        "name": question.get("question", ""),
                        "url": url,
                        "snippet": snippet
                    })

        return contexts[:REFERENCE_COUNT]
    except KeyError:
        logger.error(f"Error encountered: {json_content}")
        return []


class RAG(Photon):
    """
    Retrieval-Augmented Generation Demo from Lepton AI.

    This is a minimal example to show how to build a RAG engine with Lepton AI.
    It uses search engine to obtain results based on user queries, and then uses
    LLM models to generate the answer as well as related questions. The results
    are then stored in a KV so that it can be retrieved later.
    """

    requirement_dependency = [
        "openai",  # for openai client usage.
    ]

    extra_files = glob.glob("ui/**/*", recursive=True)

    deployment_template = {
        # All actual computations are carried out via remote apis, so
        # we will use a cpu.small instance which is already enough for most of
        # the work.
        "resource_shape": "cpu.small",
        # You most likely don't need to change this.
        "env": {
            # Choose the backend. Currently, we support BING and GOOGLE. For
            # simplicity, in this demo, if you specify the backend as LEPTON,
            # we will use the hosted serverless version of lepton search api
            # at https://search-api.lepton.run/ to do the search and RAG, which
            # runs the same code (slightly modified and might contain improvements)
            # as this demo.
            "BACKEND": "LEPTON",
            # If you are using google, specify the search cx and GOOGLE_SEARCH_API_KEY
            "GOOGLE_SEARCH_CX": "",
            # Specify the LLM model you are going to use. can be `LEPTON`, `OPENAI`
            "LLM_TYPE": "LEPTON",
            "LLM_MODEL": "mixtral-8x7b",
            # For all the search queries and results, we will use the Lepton KV to
            # store them so that we can retrieve them later. Specify the name of the
            # KV here.
            "KV_NAME": "smart-search",
            # If set to true, will generate related questions. Otherwise, will not.
            "RELATED_QUESTIONS": "true",
            # if set to true, will rewrite user question. Otherwise, will not.
            "REWRITE_QUESTION": "false",
            # On the lepton platform, allow web access when you are logged in.
            "LEPTON_ENABLE_AUTH_BY_COOKIE": "true",
            # If you want to enable history, set this to true. Otherwise, set it to false.
            "ENABLE_HISTORY": "false",
            # If you are using openai, specify the base url, e.g. https://api.openai.com/v1
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
        },
        # Secrets you need to have: search api subscription key, and lepton
        # workspace token to query lepton's llama models.
        "secret": [
            # If you use BING, you need to specify the subscription key. Otherwise
            # it is not needed.
            "BING_SEARCH_V7_SUBSCRIPTION_KEY",
            # If you use GOOGLE, you need to specify the search api key. Note that
            # you should also specify the cx in the env.
            "GOOGLE_SEARCH_API_KEY",
            # If you use Serper, you need to specify the search api key.
            "SERPER_SEARCH_API_KEY",
            # If you use SearchApi, you need to specify the search api key.
            "SEARCHAPI_API_KEY",
            # You need to specify the workspace token to query lepton's LLM models.
            "LEPTON_WORKSPACE_TOKEN",
            # OpenAI key
            "OPENAI_API_KEY",
        ],
    }

    # It's just a bunch of api calls, so our own deployment can be made massively
    # concurrent.
    handler_max_concurrency = 16

    def local_client(self):
        """
        Gets a thread-local client, so in case openai clients are not thread safe,
        each thread will have its own client.
        """
        import openai

        thread_local = threading.local()
        try:
            return thread_local.client
        except AttributeError:
            if self.llm_type == "LEPTON":
                base_url = f"https://{self.model}.lepton.run/api/v1/"
                api_key = os.environ.get(
                    "LEPTON_WORKSPACE_TOKEN") or WorkspaceInfoLocalRecord.get_current_workspace_token()
            else:
                base_url = os.environ.get("OPENAI_BASE_URL")
                api_key = os.environ.get("OPENAI_API_KEY")
            thread_local.client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key,
                # We will set the connect timeout to be 10 seconds, and read/write
                # timeout to be 120 seconds, in case the inference server is
                # overloaded.
                timeout=httpx.Timeout(connect=10, read=120, write=120, pool=10),
            )
            return thread_local.client

    def init(self):
        """
        Initializes photon configs.
        """
        # First, log in to the workspace.
        leptonai.api.workspace.login()
        self.backend = os.environ["BACKEND"].upper()
        if self.backend == "LEPTON":
            self.leptonsearch_client = Client(
                "https://search-api.lepton.run/",
                token=os.environ.get(
                    "LEPTON_WORKSPACE_TOKEN") or WorkspaceInfoLocalRecord.get_current_workspace_token(),
                stream=True,
                timeout=httpx.Timeout(connect=10, read=120, write=120, pool=10),
            )
        elif self.backend == "BING":
            self.search_api_key = os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]
            self.search_function = lambda query: search_with_bing(
                query,
                self.search_api_key,
            )
        elif self.backend == "GOOGLE":
            self.search_api_key = os.environ["GOOGLE_SEARCH_API_KEY"]
            self.search_function = lambda query: search_with_google(
                query,
                self.search_api_key,
                os.environ["GOOGLE_SEARCH_CX"],
            )
        elif self.backend == "SERPER":
            self.search_api_key = os.environ["SERPER_SEARCH_API_KEY"]
            self.search_function = lambda query: search_with_serper(
                query,
                self.search_api_key,
            )
        elif self.backend == "SEARCHAPI":
            self.search_api_key = os.environ["SEARCHAPI_API_KEY"]
            self.search_function = lambda query: search_with_searchapi(
                query,
                self.search_api_key,
            )
        elif self.backend == "DDGSAPI":
            self.search_function = lambda query: ddg_search_text(
                query,
                max_results=10
            )
        else:
            raise RuntimeError("Backend must be LEPTON, BING, GOOGLE, SERPER or SEARCHAPI.")
        logger.info(f"Using Search API backend: {self.backend}")
        self.llm_type = os.environ["LLM_TYPE"].upper()
        logger.info(f"Using LLM type: {self.llm_type}")
        self.model = os.environ["LLM_MODEL"]
        logger.info(f"Using LLM model: {self.model}")
        # An executor to carry out async tasks, such as uploading to KV.
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.handler_max_concurrency * 2
        )
        # Create the KV to store the search results.
        logger.info("Creating KV. May take a while for the first time.")
        self.kv = KV(os.environ["KV_NAME"], create_if_not_exists=True, error_if_exists=False)
        # whether we should generate related questions.
        self.should_do_related_questions = to_bool(os.environ["RELATED_QUESTIONS"])
        # A history of all the queries and responses.
        self.history = []
        # A history of all the related questions.
        self.related_history = []
        # A history of all the rewritten questions.
        self.question_history = []
        self.token_upper_limit = MODEL_TOKEN_LIMIT.get(self.model, 4096)
        # whether we should rewrite user question
        self.should_do_rewrite_question = to_bool(os.environ["REWRITE_QUESTION"])
        # whether we should enable history
        self.enable_history = to_bool(os.environ["ENABLE_HISTORY"])

    def get_related_questions(self, query, contexts):
        """
        Gets related questions based on the query and context.
        """

        def ask_related_questions(
                questions: Annotated[
                    List[str], [(
                            "question",
                            Annotated[
                                str, "related question to the original question and context."
                            ],
                    )],
                ]
        ):
            """
            ask further questions that are related to the input and output.
            """
            pass

        try:
            prompt = _related_qa_prompt_zh if contains_chinese(query) else _related_qa_prompt
            qa_prompt = prompt.format(
                context="\n\n".join([c["snippet"] for c in contexts])
            )
            user_prompt = f"{qa_prompt}\n\n{query}"
            logger.debug(f"related prompt: {user_prompt}")
            response = self.local_client().chat.completions.create(
                model=self.model,
                messages=self.related_history + [{"role": "user", "content": user_prompt}],
                tools=[{
                    "type": "function",
                    "function": tool.get_tools_spec(ask_related_questions),
                }],
                max_tokens=512,
            )
            self.related_history = self.reduce_tokens(self.related_history)
            # Append the user question to the related history.
            self.related_history.append({"role": "user", "content": query})

            related = response.choices[0].message.tool_calls[0].function.arguments
            if isinstance(related, str):
                related = json.loads(related)
            logger.debug(f"Related questions result: {related}")
            return related["questions"][:5]
        except Exception as e:
            # For any exceptions, we will just return an empty list.
            logger.error(
                "encountered error while generating related questions:"
                f" {e}\n{traceback.format_exc()}"
            )
            return []

    def get_rewrite_question(self, query):
        """
        Gets rewrite question based on the query and response. send rewrite question to the search engine.
        """

        try:
            prompt = _rewrite_question_qa_prompt_zh if contains_chinese(query) else _rewrite_question_qa_prompt
            user_prompt = f"{prompt}\n\n{query}"
            logger.debug(f"rewrite_question prompt: {user_prompt}")
            response = self.local_client().chat.completions.create(
                model=self.model,
                messages=self.question_history + [{"role": "user", "content": user_prompt}],
                max_tokens=512,
            )
            self.question_history = self.reduce_tokens(self.question_history)
            # Append the user question to the rewrite question history.
            self.question_history.append({"role": "user", "content": user_prompt})

            new_question = response.choices[0].message.content
            logger.debug(f"question rewrite result: {new_question}")
            return new_question
        except Exception as e:
            # For any exceptions, we will just return an empty list.
            logger.error(
                "encountered error while generating rewrite question:"
                f" {e}\n{traceback.format_exc()}"
            )
            return query

    def reduce_tokens(self, history: List[dict]):
        """If the token occupancy is too high, we will remove the early history."""
        history_content_lens = [len(i.get("content", "").replace(" ", "")) for i in history if i]
        if len(history) > 5 and sum(history_content_lens) / TOKEN_TO_CHAR_RATIO > self.token_upper_limit:
            count = 0
            while (
                    sum(history_content_lens) / TOKEN_TO_CHAR_RATIO >
                    self.token_upper_limit * REDUCE_TOKEN_FACTOR
                    and sum(history_content_lens) > 0
            ):
                count += 1
                del history[1:3]
                history_content_lens = [len(i.get("content", "").replace(" ", "")) for i in history if i]
            logger.warning(f"To prevent token over-limit, model forgotten the early {count} turns history.")
        return history

    def _raw_stream_response(
            self, contexts, llm_response, related_questions_future
    ) -> Generator[str, None, None]:
        """
        A generator that yields the raw stream response. You do not need to call
        this directly. Instead, use the stream_and_upload_to_kv which will also
        upload the response to KV.
        """
        # First, yield the contexts.
        yield json.dumps(contexts)
        yield "\n\n__LLM_RESPONSE__\n\n"
        # Second, yield the llm response.
        if not contexts:
            # Prepend a warning to the user
            yield (
                "(The search engine returned nothing for this query. Please take the"
                " answer with a grain of salt.)\n\n"
            )
        llm_response_text = ""
        for chunk in llm_response:
            if chunk.choices:
                part_text = chunk.choices[0].delta.content or ""
                llm_response_text += part_text
                yield part_text
        if llm_response_text:
            self.history.append({"role": "assistant", "content": llm_response_text})
            logger.debug(f"history: {self.history}")

        # Third, yield the related questions. If any error happens, we will just
        # return an empty list.
        if related_questions_future is not None:
            related_questions = related_questions_future.result()
            try:
                result = json.dumps(related_questions, ensure_ascii=False)
                if result:
                    self.related_history.append({"role": "assistant", "content": result})
                    logger.debug(f"related history: {self.related_history}")
            except Exception as e:
                logger.error(f"encountered error: {e}\n{traceback.format_exc()}")
                result = "[]"
            yield "\n\n__RELATED_QUESTIONS__\n\n"
            yield result

    def stream_and_upload_to_kv(
            self, contexts, llm_response, related_questions_future, search_uuid
    ):
        """
        Streams the result and uploads to KV.
        """
        # First, stream and yield the results.
        all_yielded_results = []
        for result in self._raw_stream_response(
                contexts, llm_response, related_questions_future
        ):
            all_yielded_results.append(result)
            yield result
        # Second, upload to KV. Note that if uploading to KV fails, we will silently
        # ignore it, because we don't want to affect the user experience.
        _ = self.executor.submit(self.kv.put, search_uuid, "".join(all_yielded_results))

    @Photon.handler(method="POST", path="/query")
    def query_function(
            self,
            query: str,
            search_uuid: str,
            generate_related_questions: Optional[bool] = True,
    ) -> StreamingResponse:
        """
        Query the search engine and returns the response.

        The query can have the following fields:
            - query: the user query.
            - search_uuid: a uuid that is used to store or retrieve the search result. If
                the uuid does not exist, generate and write to the kv. If the kv
                fails, we generate regardless, in favor of availability. If the uuid
                exists, return the stored result.
            - generate_related_questions: if set to false, will not generate related
                questions. Otherwise, will depend on the environment variable
                RELATED_QUESTIONS. Default: true.
        """
        # Note that, if uuid exists, we don't check if the stored query is the same
        # as the current query, and simply return the stored result. This is to enable
        # the user to share a searched link to others and have others see the same result.
        if search_uuid:
            try:
                if not search_uuid.endswith("_again"):
                    # Update search uuid: query + backend + llm
                    search_uuid = "_".join([
                        query,
                        self.backend,
                        self.llm_type,
                        self.model,
                        os.environ.get("KV_NAME", ""),
                        str(self.should_do_rewrite_question),
                        str(self.enable_history)
                    ])
                result = self.kv.get(search_uuid)

                def str_to_generator(result: str) -> Generator[str, None, None]:
                    yield result

                return StreamingResponse(str_to_generator(result))
            except KeyError:
                logger.debug(f"Search api key {search_uuid} not found, add to KV.")
            except Exception as e:
                logger.error(
                    f"KV error: {e}\n{traceback.format_exc()}, will generate again."
                )
        else:
            raise HTTPException(status_code=400, detail="search_uuid must be provided.")

        if self.backend == "LEPTON":
            # delegate to the lepton search api.
            result = self.leptonsearch_client.query(
                query=query,
                search_uuid=search_uuid,
                generate_related_questions=generate_related_questions,
            )
            return StreamingResponse(content=result, media_type="text/html")

        # First, do a search query.
        query = query or _default_query
        # Basic attack protection: remove "[INST]" or "[/INST]" from the query
        query = re.sub(r"\[/?INST\]", "", query)
        if not self.enable_history:
            self.history = []
            self.related_history = []
            self.question_history = []

        try:
            client = self.local_client()
            # Rewrite query if needed, seed new query to search engine.
            if self.should_do_rewrite_question:
                if not self.question_history:
                    # Append the system prompt to the history, for multi turn chat.
                    content = _rewrite_question_system_prompt_zh if contains_chinese(
                        query) else _rewrite_question_system_prompt
                    self.question_history.append({"role": "system", "content": content})
                new_question_future = self.executor.submit(self.get_rewrite_question, query)
            else:
                new_question_future = None

            # Determine the question to search for based on the result of 'new_question_future'
            question_to_search = query
            if new_question_future is not None:
                new_question = new_question_future.result()
                if new_question and new_question != query:
                    question_to_search = new_question
                if self.should_do_rewrite_question:
                    self.question_history.append({"role": "assistant", "content": question_to_search})
                    logger.debug(f"rewrite question history: {self.question_history}")
            # Search contexts based on the determined question
            contexts = self.search_function(question_to_search)
            logger.debug(f"query: {query}, search api results num: {len(contexts)}")
            if not self.history:
                # Append the system prompt to the history, for multi turn chat.
                content = _rag_system_prompt_zh if contains_chinese(query) else _rag_system_prompt
                self.history.append({"role": "system", "content": content})
            prompt = _rag_qa_prompt_zh if contains_chinese(query) else _rag_qa_prompt
            prompt = replace_today(prompt)
            qa_prompt = prompt.format(
                context="\n\n".join(
                    [f"[[citation:{i + 1}]] {c['snippet']}" for i, c in enumerate(contexts)]
                )
            )
            user_prompt = f"{qa_prompt}\n\n{query}"
            logger.debug(f"prompt: {user_prompt}")
            llm_response = client.chat.completions.create(
                model=self.model,
                messages=self.history + [{"role": "user", "content": user_prompt}],
                max_tokens=1024,
                stop=lepton_stop_words if self.llm_type == "LEPTON" else None,
                stream=True,
                temperature=0.9,
            )
            self.history = self.reduce_tokens(self.history)

            # Append the user question to the history.
            self.history.append({"role": "user", "content": query})
            if self.should_do_related_questions and generate_related_questions:
                if not self.related_history:
                    # Append the system prompt to the history, for multi turn chat.
                    content = _related_system_prompt_zh if contains_chinese(query) else _related_system_prompt
                    self.related_history.append({"role": "system", "content": content})
                # While the answer is being generated, we can start generating
                # related questions as a future.
                related_questions_future = self.executor.submit(self.get_related_questions, query, contexts)
            else:
                related_questions_future = None
        except Exception as e:
            logger.error(f"encountered error: {e}\n{traceback.format_exc()}")
            return HTMLResponse("Internal server error.", 503)

        return StreamingResponse(
            self.stream_and_upload_to_kv(
                contexts, llm_response, related_questions_future, search_uuid
            ),
            media_type="text/html",
        )

    @Photon.handler(mount=True)
    def ui(self):
        return StaticFiles(directory="ui")

    @Photon.handler(method="GET", path="/")
    def index(self) -> RedirectResponse:
        """
        Redirects "/" to the ui page.
        """
        return RedirectResponse(url="/ui/index.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Photon")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the photon.")
    parser.add_argument("--port", type=int, default=8081, help="Port to run the photon.")
    args = parser.parse_args()
    rag = RAG()
    rag.launch(host=args.host, port=args.port)
