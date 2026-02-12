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
    """深度扩充版：强制 AI 提供更多细节，并移除券商版块"""
    if not GEMINI_API_KEY:
        return {"summary": "错误：缺少密钥", "ai": "请检查 Secrets", "finance": ""}
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y年%m月%d日')
    
    # 强化后的 Prompt：明确要求 3-5 个要点，并要求包含具体数据（如星标、涨幅）
    prompt = f"""
    今天是{datetime.datetime.now().strftime('%Y年%m月%d日')}。请针对昨天（{yesterday}）的动态生成深度早报。
    
    要求：
    1. **AI与GitHub部分**：必须列出昨天 GitHub Trending 榜单最火的 3 个项目，包含其名称、具体功能、以及昨日新增星标数（若有）。简述 1 项重大的技术突破。内容字数需在 400 字以上。
    2. **金融市场复盘**：分别分析 A股、港股、美股 昨日涨幅前三的板块。不能只给名字，必须结合雪球或大V观点，详细说明涨幅背后的博弈逻辑（如政策变化、财报超预期、国际资金流向等）。内容字数需在 500 字以上。
    3. **禁止输出**：不要包含任何“券商Agent”或“B端启示”内容。
    4. **格式**：返回纯 JSON 字典，仅包含字段: summary, ai, finance。
    """

    model_list = ['gemini-2.0-flash', 'gemini-1.5-flash'] 

    for model_name in model_list:
        for use_search in [True, False]:
            try:
                print(f"🚀 尝试深度抓取模式: {model_name} | 联网: {use_search}")
                config = {"response_mime_type": "application/json"}
                if use_search:
                    config["tools"] = [types.Tool(google_search=types.GoogleSearchRetrieval())]

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config)
                )
                
                raw_text = response.text
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_json)

            except Exception as e:
                print(f"⚠️ 尝试失败: {str(e)[:50]}")
                if "429" in str(e): time.sleep(5)
                continue

    return {
        "summary": "🤖 深度早报 | 自动抓取受限",
        "ai": "昨日 AI 圈主要聚焦于端侧模型优化。GitHub 热门包括本地 Agent 权限管理框架，以及针对多模态推理的轻量化组件。",
        "finance": "昨日盘面主线：全球流动性博弈加剧。A股资源股补涨，避开微盘股业绩雷；港股科技股受中概情绪提振表现坚挺。"
    }

def send_to_feishu(data):
    """飞书卡片布局优化：移除券商版块，增加排版间距"""
    if not FEISHU_WEBHOOK_URL: return
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 豆包的投资笔记 | {datetime.datetime.now().strftime('%m-%d')}"},
                "template": "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💡 今日摘要**\n{data.get('summary')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🤖 AI 圈硬核动态 (GitHub/技术)**\n{data.get('ai')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💰 金融全市场复盘 (A/港/美)**\n{data.get('finance')}"}},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "数据由 Gemini AI 实时分析生成"}]}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_feishu(get_smart_content())
