# encoding:utf-8

from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from .dashscope_session import DashscopeSession
import os
import dashscope
from http import HTTPStatus



dashscope_models = {
    "qwen-turbo": dashscope.Generation.Models.qwen_turbo,
    "qwen-plus": dashscope.Generation.Models.qwen_plus,
    "qwen-max": dashscope.Generation.Models.qwen_max,
    "qwen-bailian-v1": dashscope.Generation.Models.bailian_v1,
    "qwen-max-latest":dashscope.Generation.Models.qwen_max,
    "qwen-turbo-1101":dashscope.Generation.Models.qwen_turbo
}
# ZhipuAI对话模型API
class DashscopeBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(DashscopeSession, model=conf().get("model") or "qwen-plus")
        self.model_name = conf().get("model") or "qwen-plus"
        print('debug model_name:',self.model_name)
        self.api_key = conf().get("dashscope_api_key")
        os.environ["DASHSCOPE_API_KEY"] = self.api_key
        self.client = dashscope.Generation

    def reply_backup(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[DASHSCOPE] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[DASHSCOPE] session query={}".format(session.messages))

            reply_content = self.reply_text(session)
            logger.debug(
                "[DASHSCOPE] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[DASHSCOPE] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply(self, query, context=None):
        # acquire reply content
        query_withcontext = query_with_context(query)
        if query_withcontext["error"]=="None":
            question = query
            qcontext = query_withcontext["context"]
            llm_prompt_template = f"""你是技术客服。\n根据上下文给的问题解决逻辑一步一步的引导客人解决问题。每次回复都引导用户做下一步操作或者询问，每次只可以引导一步，回复的输出要求简洁清楚，然后根据用户的反馈判断问题，按照给定的逻辑推理指导用户下一步。\n如果上下文中没有答案，就回复'@苏★：搞不定，来看一下！' \n上下文: {qcontext}\n问题: {question} \n答案: """
            query = llm_prompt_template
        if context.type == ContextType.TEXT:
            logger.info("[DASHSCOPE] query={}".format(query))
            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[DASHSCOPE] session query={}".format(session.messages))

            reply_content = self.reply_text(session)
            logger.debug(
                "[DASHSCOPE] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[DASHSCOPE] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply
        

    def reply_text(self, session: DashscopeSession, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            #print('debug',session.messages)
            dashscope.api_key = self.api_key
            response = self.client.call(
                #dashscope_models[self.model_name],
                model = "qwen-turbo-1101",
                messages=session.messages,
                result_format="message"
            )
            print('debug response:',response)
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]["message"]["content"]
                return {
                    "total_tokens": response.usage["total_tokens"],
                    "completion_tokens": response.usage["output_tokens"],
                    "content": content,
                }
            else:
                logger.error('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                    response.request_id, response.status_code,
                    response.code, response.message
                ))
                result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
                need_retry = retry_count < 2
                result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
                if need_retry:
                    return self.reply_text(session, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, retry_count + 1)
            else:
                return result

import requests
import json

def query_with_context(query):
    """
    Queries the Flask app for a given query and returns the result with context.
    Args:
        query: The query string.
    Returns:
        A dictionary containing the query and the context, or an error message if 
        there was an issue with the request or the Flask app returned an error.
    """
    try:
        url = "http://kb:5601/query?text=" + query  # Adjust URL if needed
        #url = "http://127.0.0.1:5601/query?text=" + query
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        if 'error' in data:
            return {"query": query, "context": "None","error": data['error']}
        return {"query": query, "context": data['result'],"error": "None"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the Flask app: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"Error decoding JSON response: {e}"}
    except KeyError as e:
        return {"error": f"Unexpected response format from Flask app: Missing key {e}"}