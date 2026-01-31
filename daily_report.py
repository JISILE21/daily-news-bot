import requests
import json
import os
import datetime
from google import genai
from google.genai import types

# --- 1. 配置区 ---
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_URL')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def get_smart_content():
    """调用 Gemini API 搜索并生成当日深度早报"""
    if not GEMINI_API_KEY:
        return {"error": "缺少 GEMINI_API_KEY"}
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    prompt = f"""
    今天是{datetime.datetime.now().strftime('%Y-%m-%d')}。请搜罗{yesterday}全天AI圈和金融圈的新鲜事。
    要求：
    1. 文风参考“豆包的投资笔记”（洞察犀利、口语化但专业）。
    2. AI部分：关注GitHub趋势、技术突破（如Agent、推理模型）。
    3. 金融部分：复盘A股/港股/美股昨日涨幅榜前列的板块，分析逻辑（综合雪球/大V观点）。
    4. 增加‘对B端业务/券商Agent启示’版块。
    5. 返回格式必须是纯JSON，包含四个字段: ai, finance, b_side, summary。
    """
    
    try:
        # 切换到更稳定的 1.5-flash 模型
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}]
            )
        )
        
        # 清洗返回的 JSON 文本
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"❌ 生成失败，原因: {str(e)}")
        return {
            "summary": "内容生成暂时受限",
            "ai": f"API 报错: {str(e)}",
            "finance": "建议稍后手动重试",
            "b_side": "待更新"
        }

def send_to_feishu(data):
    """发送美化后的飞书卡片"""
    if not FEISHU_WEBHOOK_URL:
        print("❌ 缺少飞书链接")
        return

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 豆包的投资笔记 | {datetime.datetime.now().strftime('%m-%d')}"},
                "template": "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💡 今日摘要**\n{data.get('summary', '暂无内容')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🤖 AI 圈硬核动态**\n{data.get('ai', '暂无内容')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💰 金融全市场复盘**\n{data.get('finance', '暂无内容')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🏢 券商/B端启示**\n{data.get('b_side', '暂无内容')}"}},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "由 Gemini 2.0 AI 实时搜索生成"}]}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    content = get_smart_content()
    send_to_feishu(content)
