import requests
import json

# --- 只需要修改这里 ---
FEISHU_WEBHOOK_URL = "这里粘贴你刚才复制的Webhook链接"
# ----------------------

def send_to_feishu(content_data):
    # 构建飞书美化卡片
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "📅 豆包的投资笔记 · 深度早报"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**🤖 AI 圈动态**\n{content_data['ai']}"}
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**💰 金融全市场分析**\n{content_data['finance']}"}
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**💡 B 端业务启示**\n{content_data['b_side']}"}
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "数据源：豆瓜、雪球、GitHub、海内外主流媒体"}]
                }
            ]
        }
    }
    
    response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        print("发送成功！去飞书看看吧。")
    else:
        print(f"发送失败，错误码：{response.status_code}")

# 模拟今天的内容（之后可以对接 API 自动生成）
mock_data = {
    "ai": "1. Moltbot 本地 Agent 爆火，GitHub 星标破 5k。\n2. OpenAI Orion 推理能力瓶颈引发讨论。",
    "finance": "1. **神秘资金砸盘**：沪深 300 ETF 卖出 1200 亿，筹码减持约 50%。\n2. **黄金狂飙**：Tether 囤金 140 吨，金价突破 5270 美元。",
    "b_side": "关注本地化小参数模型在券商私域的应用，降低合规压力。"
}

if __name__ == "__main__":
    send_to_feishu(mock_data)