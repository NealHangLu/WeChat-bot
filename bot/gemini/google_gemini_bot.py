"""
Google gemini bot

@author zhayujie
@Date 2023/12/15
"""
# encoding:utf-8

from bot.bot import Bot
import google.generativeai as genai
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from google.generativeai.types import HarmCategory, HarmBlockThreshold


# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):

    def __init__(self):
        super().__init__()
        self.api_key = conf().get("gemini_api_key")
        # 复用chatGPT的token计算方式
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.model = conf().get("model") or "gemini-pro"
        logger.info(f"[Gemini] model={self.model}")
        if self.model == "gemini":
            self.model = "gemini-1.5-pro"
            #self.model = "gemini-1.5-flash"
        logger.info(f"[Gemini] model={self.model}")    
    def reply_backup(self, query, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            gemini_messages = self._convert_to_gemini_messages(self.filter_messages(session.messages))
            logger.debug(f"[Gemini] messages={gemini_messages}")
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                self.model,
                system_instruction="你的名字叫小米渣，男，20岁，理工科毕业，现在的任务是做技术支持客服，性格活泼热情，表情包多。\n下面是解决问题的方案，你需要一步一步的引导用户去解决问题。\n软件问题：\\\\nA1：按钮（红按钮）不能发射子弹问题\\\\n客户：打不出子弹\\\\n小米渣：绿按钮能不能切换武器？（第一个判断A：按钮坏了还是蓝牙问题）\\\\n情况A1客户：能！（按钮坏了）\\\\n小米渣：红按钮坏了，需要更换红按钮。（问题回答结束）\\\\n情况A2客户：也不行！（蓝牙问题）\\\\n小米渣：检查蓝牙是否正常连接？（第二个判断B：蓝牙有没有连接）\\\\n情况B1客户：怎么看有没有正常连接？\\\\n小米渣：方向盘下面的蓝色小灯是长亮就是正常连接，闪烁就是没连上。\\\\n情况B2客户：在闪烁就是没连上对吧？（说明没有连接，大概率是丢失配对）\\\\n小米渣：是的你需要重新做眼镜的蓝牙配对。（如果客户会连，问题就结束了）\\\\n情况B2客户：怎么配对？（跳转怎么配对的回答）\\\\n情况B3：正常连接。（说明蓝牙死机）\\\\n小米渣：蓝牙死机，关闭车电源再重开，检查是否恢复？（第三个判断C：蓝牙是死机还是丢失配对）\\\\n情况C1客户：好了！（说明是蓝牙死机）\\\\n小米渣：OK！\\\\n情况C2客户：还是不行！（说明是蓝牙丢失配对）\\\\n小米渣：蓝牙丢失配对，需要重新配！ \\\\n客户问：怎么配对？\\\\n答：同时按下红绿按钮和方向盘下面的蓝牙按钮，按住不放直到蓝灯狂闪，方向盘蓝牙就解除和之前设备的绑定了。你试一下！\\\\n客户问：好了！\\\\n小米渣：进入头显，找到左侧的外设选项，先把已经存在的外设删除，然后按加号，选择自定义设备，看到头显在搜索设备的时候，再同时按下方向盘红绿按钮和蓝牙按钮，按住不放，直到蓝灯稳定常亮，头显显示配对成功，就可以了。\\\\n客户问：好了！\\\\n小米渣：OK！\\\\n*超出回复能力的需要@Griffin：搞不定，来看一下！\\\\n\\\\nA2平板电脑登陆失败\\\\n客户问：平板登不上！\\\\n小米渣：平板有没有连接Wifi？WIFI有没有接通外网？（第一个判断A）\\\\n情况A1客户问： 刚才没连，现在好了！\\\\n小米渣：OK\\\\n情况A2客户问：连好的呀！有外网！\\\\n小米渣：登陆码填对没有？有没有其他设备在用这个码登录？（第二个判断B）\\\\n情况B1客户问：哦哦写错了。\\\\n小米渣：（狗头）\\\\n情况B2客户问：写对了，登不上。\\\\n小米渣：@ Griffin：搞不定，来看一下！\\\\n\\\\nA3转播电脑没有画面\\\\n客户问：转播电脑（白电脑、一体机）没有画面！\\\\n小米渣：没有游戏画面还是没有实拍画面？（第一个判断A） \\\\n情况A1客户问：没有游戏画面，有实拍画面。\\\\n小米渣：电脑没连上WIFI哈！\\\\n情况A2客户问：有实拍画面，没有游戏画面（没有动物金币）。\\\\n小米渣：你先用q键切换摄像头，看看有画面了没？（第二个判断B） \\\\n情况B1客户问：有了！\\\\n小米渣：打开左上角的设置菜单，把不存在的摄像头删除了。（问题回答结束）\\\\n情况B2客户问：还是没有！\\\\n小米渣：@ Griffin：搞不定，来看一下！\\\\nB1头显不能开机\\\\n客户问：头显开不了机！\\\\n小米渣：需要长按5秒直到橙色图标出现。\\\\n客户问：按了5秒，不行。\\\\n小米渣：电池没电了，从车子上拿下来，用黑色方头原配充电器来充。\\\\n客户问：车子不能充？\\\\n小米渣：电量掉到0车子充不进了哈，要换原配的来充！下次注意下不要让头显掉到0。\\\\n\\\\nB2头显里看不到画面\\\\n客户问：眼镜里啥也看不见了！\\\\n小米渣：你戴着眼镜去看一下红外定位灯，看得到上面的绿色坐标不？（第一个判断A）\\\\n情况A1客户问：看不到！\\\\n小米渣：头显死机了哈，重启一下！\\\\n情况A2客户问：能看到坐标！\\\\n小米渣：@ Griffin：搞不定，来看一下！\\\\n\",\n",
                )
            
            # 添加安全设置
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # 生成回复，包含安全设置
            response = model.generate_content(
                gemini_messages,
                safety_settings=safety_settings
            )

            if response.candidates and response.candidates[0].content:
                reply_text = response.candidates[0].content.parts[0].text
                logger.info(f"[Gemini] reply={reply_text}")
                self.sessions.session_reply(reply_text, session_id)
                return Reply(ReplyType.TEXT, reply_text)
            else:
                # 没有有效响应内容，可能内容被屏蔽，输出安全评分
                logger.warning("[Gemini] No valid response generated. Checking safety ratings.")
                if hasattr(response, 'candidates') and response.candidates:
                    for rating in response.candidates[0].safety_ratings:
                        logger.warning(f"Safety rating: {rating.category} - {rating.probability}")
                error_message = "No valid response generated due to safety constraints."
                self.sessions.session_reply(error_message, session_id)
                return Reply(ReplyType.ERROR, error_message)
                    
        except Exception as e:
            logger.error(f"[Gemini] Error generating response: {str(e)}", exc_info=True)
            error_message = "Failed to invoke [Gemini] api!"
            self.sessions.session_reply(error_message, session_id)
            return Reply(ReplyType.ERROR, error_message)

    def reply(self, query, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            query_withcontext = query_with_context(query)
            if query_withcontext["error"]=="None":
                question = query
                qcontext = query_withcontext["context"]
                llm_prompt_template = f"""你是问答任务的助手。\n根据上下文给的逻辑回复一步一步的引导客人解决问题。\n如果上下文中没有答案，就回复'我需要找我老大来一起看看这个问题。' \n上下文: {qcontext}\n问题: {question} \n\n答案: """
                query = llm_prompt_template
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            gemini_messages = self._convert_to_gemini_messages(self.filter_messages(session.messages))
            logger.debug(f"[Gemini] messages={gemini_messages}")
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                self.model,
                system_instruction="你的名字叫小米渣，男，20岁，理工科毕业，现在的任务是做技术支持客服，性格稳重，回复简洁清晰。\n根据上下文给的逻辑回复一步一步的引导客人解决问题。\n如果上下文中没有答案，就回复'我需要找我老大来一起看看这个问题。'",
                )
            
            # 添加安全设置
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # 生成回复，包含安全设置
            response = model.generate_content(
                gemini_messages,
                safety_settings=safety_settings
            )
            #logger.info(f"[Gemini] response={response}")
            if response.candidates and response.candidates[0].content:
                reply_text = response.candidates[0].content.parts[0].text
                logger.info(f"[Gemini] reply={reply_text}")
                self.sessions.session_reply(reply_text, session_id)
                return Reply(ReplyType.TEXT, reply_text)
            else:
                # 没有有效响应内容，可能内容被屏蔽，输出安全评分
                logger.warning("[Gemini] No valid response generated. Checking safety ratings.")
                if hasattr(response, 'candidates') and response.candidates:
                    for rating in response.candidates[0].safety_ratings:
                        logger.warning(f"Safety rating: {rating.category} - {rating.probability}")
                error_message = "No valid response generated due to safety constraints."
                self.sessions.session_reply(error_message, session_id)
                return Reply(ReplyType.ERROR, error_message)
                    
        except Exception as e:
            logger.error(f"[Gemini] Error generating response: {str(e)}", exc_info=True)
            error_message = "Failed to invoke [Gemini] api!"
            self.sessions.session_reply(error_message, session_id)
            return Reply(ReplyType.ERROR, error_message)

    def _convert_to_gemini_messages(self, messages: list):
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model"
            elif msg.get("role") == "system":
                role = "user"
            else:
                continue
            res.append({
                "role": role,
                "parts": [{"text": msg.get("content")}]
            })
        #print("_convert_to_gemini_messages",res)
        return res

    @staticmethod
    def filter_messages(messages: list):
        res = []
        turn = "user"
        if not messages:
            return res
        for i in range(len(messages) - 1, -1, -1):
            message = messages[i]
            role = message.get("role")
            if role == "system":
                res.insert(0, message)
                continue
            if role != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        #print("messages:",messages)
        #print("filter_messages",res)        
        return res

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
