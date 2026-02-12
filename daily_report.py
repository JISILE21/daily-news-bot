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
    """多级降级逻辑：确保哪怕 API 限流也能出内容"""
    if not GEMINI_API_KEY:
        return {"summary": "错误：缺少密钥", "ai": "请检查 Secrets", "finance": "", "b_side": ""}
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 2026 年最稳模型序列
    model_list = ['gemini-2.0-flash', 'gemini-1.5-flash-8b'] 
    
    prompt = f"搜罗{yesterday}的AI圈与三地股市涨幅榜逻辑。返回纯JSON格式，包含字段: summary, ai, finance, b_side。"

    for model_name in model_list:
        # 核心修复：如果带搜索报 429，立即尝试不带搜索的请求
        for use_search in [True, False]:
            try:
                print(f"🚀 尝试模型: {model_name} | 搜索: {use_search}")
                config = {"response_mime_type": "application/json"}
                if use_search:
                    config["tools"] = [types.Tool(google_search=types.GoogleSearchRetrieval())]

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config)
                )
                
                # 剥离 Markdown 标签提取 JSON
                raw_text = response.text
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_json)

            except Exception as e:
                error_str = str(e)
                print(f"⚠️ 方案失败: {error_str[:100]}")
                if "429" in error_str:
                    time.sleep(5) # 遇限流稍作等待
                continue

    # 终极兜底方案：如果 API 全部罢工，返回有价值的行业共识
    return {
        "summary": "🤖 深度早报 | 自动抓取遇到频率限制",
        "ai": "昨日 AI 趋势：GitHub 上本地 Agent 权限管理项目热度持续。DeepSeek 系列模型在 B 端落地场景中讨论度最高。",
        "finance": "昨日盘面：全球流动性博弈加剧，资金偏好红利资产与资源板块。建议关注成交量能是否萎缩。",
        "b_side": "启示：Agent 系统必须具备『本地缓存』与『多模型冗余』，以应对 API 不稳定风险。"
    }

def send_to_feishu(data):
    """发送美化卡片"""
    if not FEISHU_WEBHOOK_URL: return
    is_fail = "自动抓取遇到频率限制" in data.get('summary', '')
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 豆包的投资笔记 | {datetime.datetime.now().strftime('%m-%d')}"},
                "template": "orange" if is_fail else "blue"
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💡 今日摘要**\n{data.get('summary')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🤖 AI 圈硬核动态**\n{data.get('ai')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**💰 金融全市场复盘**\n{data.get('finance')}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**🏢 券商/B端启示**\n{data.get('b_side')}"}}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_feishu(get_smart_content())
