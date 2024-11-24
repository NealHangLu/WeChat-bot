import os
import dashscope

query = f'''
你是问答任务的助手。
根据上下文给的问题解决逻辑一步一步的引导客人解决问题。每次回复都引导用户做下一步操作或者询问，根据用户的反馈判断问题并且按照给定的逻辑推理指导用户下一步。
如果上下文中没有答案，就回复'@苏★：搞不定，来看一下！' 
上下文: Q1:按钮（红按钮）不能发射子弹问题 客户：打不出子弹 你需要问用户：绿按钮能不能切换武器？ 如果用户回答：能！说明是 按钮坏了 红按钮坏了，需要更换红按钮 如果用户回答：也不行！说明是 蓝牙问题 继续问用户：检查蓝牙是否正常连接？ 如果用户回复：怎么看有没有正常连接？ 你可以回复：方向盘下面的蓝色小灯是长亮就是正常连接，闪烁就是没连上。 如果用户回复：在闪烁就是没连上对吧？ 说明没有连接，大概率是丢失配对。你回复客人：是的你需要重新做眼镜的蓝牙配对。 如果客人回复：正常连接。 说明蓝牙死机，回复客人：蓝牙死机，关闭车电源再重开，检查是否恢复？ 如果客户继续问：怎么配对？（跳转怎么配对的回答） 如果客人回复：好了！ 说明是蓝牙死机 如果客人回复：还是不行！ 说明是蓝牙丢失配对。回复客人：蓝牙丢失配对，需要重新配！  如果客户继续问：怎么配对？ 回复客户：同时按下红绿按钮和方向盘下面的蓝牙按钮，按住不放直到蓝灯狂闪，方向盘蓝牙就解除和之前设备的绑定了。你试一下！ 如果客户问：好了！ 你可以继续回复：进入头显，找到左侧的外设选项，先把已经存在的外设删除，然后按加号，选择自定义设备，看到头显在搜索设备的时候，再同时按下方向盘红绿按钮和蓝牙按钮，按住不放，直到蓝灯稳定常亮，头显显示配对成功，就可以了。 客户问：好了！ 说明用户已经解决问题了。 如果客户还是没有解决问题。 可以让@Griffin：搞不定，来看一下
问题: 红色按钮打不出子弹 

答案: 
'''


messages = [
    {'role': 'system', 'content': '你的名字叫小米渣，男，20岁，理工科毕业，现在的任务是做技术支持客服，性格稳重，回复简洁清晰。\n根据上下文给的逻辑回复一步一步的引导客人解决问题。\n如果上下文中没有答案，就回复 我需要找我老大来一起看看这个问题。'},
    {'role': 'user', 'content': query}
    ]
response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key='sk-3ca2dc6930dd4b77aaa9bc7675fac7b8',
    model="qwen-turbo-1101", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message'
    )
print(response.output.choices[0].message.content)

def custom_reply(messages):
    response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key='sk-3ca2dc6930dd4b77aaa9bc7675fac7b8',
    model="qwen-turbo-1101", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message'
    )

    return response