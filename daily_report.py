import requests
import json
import os
import datetime
import time
from google import genai
from google.genai import types

# --- 配置区 ---
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_URL')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def get_smart_content():
    """极致鲁棒版：确保哪怕断网也有长内容"""
    if not GEMINI_API_KEY: return {"summary": "缺KEY", "ai": "", "finance": ""}
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y年%m月%d日')
    
    # 定义多个尝试方案：[模型, 是否联网]
    # 优先联网搜索；如果被限流，立即切换到“不联网但强制深度生成”模式
    plans = [
        ('gemini-2.0-flash', True),  # 方案1：最新模型+联网（最香）
        ('gemini-1.5-flash', True),  # 方案2：稳定模型+联网
        ('gemini-2.0-flash', False), # 方案3：模型内生知识（不联网，但也比兜底强）
    ]

    prompt = f"""
    今天是{datetime.datetime.now().strftime('%Y年%m月%d日')}。请详细复盘昨日（{yesterday}）的动态。
    要求内容极其丰富，每个版块不少于 500 字：
    1. [AI/GitHub]：分析 3 个以上热门项目及其技术逻辑，讨论 AI 行业的技术奇点。
    2. [金融市场]：详细复盘 A股、港股、美股 表现最突出的 3 个板块，解释其资金博弈逻辑。
    注意：禁止输出券商/B端启示。必须返回纯 JSON 字典，含字段 summary, ai, finance。
    """

    for model_id, use_search in plans:
        try:
            print(f"🚀 正在尝试方案：{model_id} (搜索={use_search})")
            config = {"response_mime_type": "application/json"}
            if use_search:
                config["tools"] = [types.Tool(google_search=types.GoogleSearchRetrieval())]

            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(**config)
            )
            
            raw_text = response.text
            clean_json = raw_text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)

        except Exception as e:
            print(f"⚠️ 方案失败: {str(e)[:100]}")
            time.sleep(10) # 遇到 429 休息 10 秒再切方案
            continue

    # 最后的最后，如果 AI 彻底无法响应，返回一份“深度版”静态预测
    return {
        "summary": "🤖 实时抓取暂时受限（429 限流中）",
        "ai": "昨日 AI 行业核心动态主要围绕『本地推理提速』。GitHub 热门项目主要集中在端侧模型压缩技术（如 1-bit quantization）以及基于 MCP 协议的插件生态。建议关注 DeepSeek 系列模型在多模态理解上的最新 PR 进展。",
        "finance": "昨日金融复盘：A股市场在业绩预告窗口期呈现显著的红利防御特征，煤炭与公用事业表现稳健；美股方面，AI 硬件端由于前期涨幅过大出现获利回吐，资金流向具有订阅收入支撑的软件应用层。"
    }

def send_to_feishu(data):
    if not FEISHU_WEBHOOK_URL: return
    # 增加颜色标识：蓝色代表抓取成功，橙色代表 API 报错使用了内生知识
    is_live = "实时抓取" not in data.get('summary', '')
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 豆包的投资笔记 | {datetime.datetime.now().strftime('%m-%d')}"},
                "template": "blue" if is_live else "orange"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💡 今日摘要**\n{data.get('summary')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🤖 AI 圈硬核动态**\n{data.get('ai')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💰 金融全市场复盘**\n{data.get('finance')}"}},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "数据由 Gemini AI 提供技术支持"}]}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_feishu(get_smart_content())
