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
        #print('dashscope bot context:',context)
        
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
            
            #query = query_add_context(query)
            
            session = self.sessions.session_query(query, session_id)
            logger.debug("[DASHSCOPE] session query={}".format(session.messages))

            print('debug in function reply session.messages:',session.messages)
            #print('debug in function reply session.messages:',session.messages[-1]['content'])
            #session.messages[-1]['content'] = "test"
            #print('debug in function reply session.messages:',session.messages[-1]['content'])
            user_history = extract_user_utterances(session.messages)
            print('user_history:\n',user_history)
            reply_content = {}
            reply_content["content"] = ""
            reply_content["completion_tokens"] = 0
            if is_need_answer(session.messages):
                if 'Yes' in isabletoanswer(user_history):
                    query = query_add_context(query)
                    session.messages[-1]['content'] = query
                    reply_content = self.reply_text(session)
                else:
                    reply_content["content"] = ""
                    reply_content["completion_tokens"] = 0
            else:
                query = query_add_context(query)
                session.messages[-1]['content'] = query
                reply_content = self.reply_text(session)

            #reply_content = self.reply_text(session)
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
            #print('debug in function reply_text session.messages',session.messages)
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
import os
kburl = os.environ.get("kburl", "http://kb:5601")  # Default value if not set
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
        #url = "http://kb:5601/query?text=" + query  # Adjust URL if needed
        url = "http://127.0.0.1:5680/query?text=" + query
        url = kburl+"/query?text=" + query
        print('debug kbsearch url:',url)
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        print("kb search result: ",data)
        if 'error' in data:
            return {"query": query, "context": "None","error": data['error']}
        return {"query": query, "context": data['result'],"error": "None"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error connecting to the Flask app: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"Error decoding JSON response: {e}"}
    except KeyError as e:
        return {"error": f"Unexpected response format from Flask app: Missing key {e}"}

def query_add_context(query):
    query_withcontext = query_with_context(query)
    if query_withcontext["error"]=="None":
        question = query
        qcontext = query_withcontext["context"]
        llm_prompt_template = f"""你是真人技术客服。\n根据上下文给的问题解决逻辑一步一步的引导客人解决问题。每次回复都引导用户做下一步操作或者询问，每次只可以引导一步，回复的输出要求简洁清楚，然后根据用户的反馈判断问题，按照给定的逻辑推理指导用户下一步。\n如果上下文中没有答案，就回复'@Griffin：搞不定，来看一下！' \n上下文: {qcontext}\n问题: {question} \n答案: """
        query = llm_prompt_template 
    return query   

def extract_user_utterances(chat_log):
    """
    Extracts user utterances from a chat log (list of dictionaries).

    Args:
        chat_log: A list of dictionaries, where each dictionary represents a turn in the conversation 
                  and has a 'role' and 'content' key.

    Returns:
        A string containing all user utterances, separated by newline characters.  Returns an empty 
        string if no user utterances are found.  Handles potential errors gracefully.
    """

    try:
        user_utterances = []
        for turn in chat_log:
            if isinstance(turn, dict) and turn.get('role') == 'user':
                user_utterances.append(turn.get('content', ''))  #Handle missing 'content' key
        return user_utterances
    except (TypeError, AttributeError) as e:
        print(f"Error processing chat log: {e}")
        return user_utterances

def isabletoanswer(user_history):
    user_history_str = '对话：\n'+'\n客人：'.join(user_history)
    prompt = '''
    判断用户的提问是否需要机器人回复。
    需要回复的情况一：用户的问题是和按钮（红按钮）不能发射子弹问题，平板电脑登陆失败，转播电脑没有画面，头显不能开机，头显里看不到画面。
    如果用户的提问不在上述情况中，不需要回复用户，比如一些打招呼等。你的输出必须是Yes 或者No 二者之一。
    如果需要回复用户输出：Yes
    如果不需要回复用户输出：No
    如果无法判断输出：Yes
    '''

    messages = [
    {'role': 'system', 'content': prompt},
    {'role': 'user', 'content': user_history_str}
    ]

    response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key='sk-3ca2dc6930dd4b77aaa9bc7675fac7b8',
    model="qwen-turbo-1101", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message'
    )
    print('isabletoanswer:',response.output.choices[0].message.content)
    return response.output.choices[0].message.content   

def is_need_answer(session_messages):
    """
    判断是否需要调用 isabletoanswer 函数。

    Args:
        session_messages:  包含对话信息的列表，每个元素是一个字典，包含 'role' 和 'content' 键。

    Returns:
        True 如果需要调用 isabletoanswer，否则返回 False。
    """

    assistant_messages = [msg['content'] for msg in session_messages if msg['role'] == 'assistant']
    if not assistant_messages:
        return True  # 没有 assistant 回复，需要调用

    # 检查倒数第 2, 4, 6, 8, 10 个消息是否都是 assistant 的回复
    if len(session_messages) >= 10:  # 确保至少有 10 条消息
        indices = [i for i in range(len(session_messages) - 2, len(session_messages) - 12, -2)]
        if all(session_messages[i]['role'] == 'assistant' for i in indices):
           return True

    if len(session_messages) >= 2 and session_messages[-2]['role'] == 'user':
        return True

    return False