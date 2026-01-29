import requests
import json
import os  # 新增：用于读取 GitHub 藏起来的秘密

# --- 关键修改：从 GitHub Secrets 读取链接 ---
# 如果在本地运行，它会找环境变量；在 GitHub 跑，它会找我们设置的那个 Secret
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_URL') 

def send_to_feishu(content_data):
    if not FEISHU_WEBHOOK_URL:
        print("❌ 错误：没找到飞书 Webhook 链接，请检查 Secrets 设置")
        return

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
                {"tag": "note",
                    "elements": [{"tag": "plain_text", "content": "数据源：豆瓜、雪球、GitHub、海内外主流媒体"}]
                }
            ]
        }
    }
    
    response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        print("✅ 发送成功！去飞书看看吧。")
    else:
        print(f"❌ 发送失败，错误码：{response.status_code}，原因：{response.text}")

# 模拟数据
mock_data = {
    "ai": "1. Moltbot 本地 Agent 爆火。\n2. OpenAI Orion 推理瓶颈引发讨论。",
    "finance": "1. **神秘资金砸盘**：沪深 300 ETF 卖出 1200 亿。\n2. **黄金狂飙**：金价突破 5270 美元。",
    "b_side": "关注本地化小参数模型在券商私域的应用。"
}

if __name__ == "__main__":
    send_to_feishu(mock_data)
