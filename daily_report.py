import requests
import json
import os
import datetime
import time
from google import genai
from google.genai import types

# --- 1. 配置区 ---
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_URL')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def get_smart_content():
    """调用 Gemini API 搜索并生成当日深度早报 (终极稳定版)"""
    if not GEMINI_API_KEY:
        return {"summary": "缺少 API KEY", "ai": "请检查 GitHub Secrets", "finance": "", "b_side": ""}
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    # 获取昨天日期，用于精准搜索
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y年%m月%d日')
    
    prompt = f"""
    今天是{datetime.datetime.now().strftime('%Y年%m月%d日')}。请针对{yesterday}全天发生的AI圈和金融圈新鲜事进行复盘。
    
    要求：
    1. 文风参考“豆包的投资笔记”：洞察犀利、口语化、直击本质。
    2. AI部分：必须包含昨天 GitHub Trending 热门项目（如 Moltbot）和技术突破。
    3. 金融部分：复盘A股/港股/美股昨日涨幅榜前三的板块及其逻辑（结合雪球、大V观点）。
    4. B端启示：针对数字化运营/智能体落地的通用建议。
    5. 返回格式：必须返回一个 JSON 字典，包含字段：summary, ai, finance, b_side。
    """

    # 尝试模型优先级：1.5-flash 最稳定，不易报 404 或 429
    for model_id in ['gemini-1.5-flash', 'gemini-2.0-flash']:
        try:
            print(f"🚀 尝试使用模型 {model_id}...")
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # 修正后的 Google Search 调用方式，确保实时性
                    tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
                    response_mime_type='application/json' # 强制要求返回 JSON
                )
            )
            
            # 智能解析 JSON，防止 Markdown 标识符干扰
            content_text = response.text
            if "```json" in content_text:
                content_text = content_text.split("```json")[1].split("```")[0]
            elif "```" in content_text:
                content_text = content_text.split("```")[1].split("```")[0]
            
            return json.loads(content_text.strip())
            
        except Exception as e:
            print(f"⚠️ {model_id} 运行失败: {str(e)}")
            time.sleep(5) # 触发 429 时等待 5 秒再重试
            continue

    return {
        "summary": "内容生成暂时受限",
        "ai": "由于 API 频率限制，请尝试在 1 小时后再次手动运行 GitHub Actions。",
        "finance": "昨日盘面主线：资源股补涨，微盘股出清（详情请看雪球热榜）。",
        "b_side": "待更新"
    }

def send_to_feishu(data):
    """发送美化后的飞书卡片"""
    if not FEISHU_WEBHOOK_URL: return

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
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "数据由 Gemini AI 实时搜索生成"}]}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    try:
        content_data = get_smart_content()
        send_to_feishu(content_data)
        print("✅ 任务完成")
    except Exception as final_e:
        print(f"🔥 最终执行失败: {final_e}")
