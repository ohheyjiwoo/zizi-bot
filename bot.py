import os
import requests
from datetime import date
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
ALLOWED_CHAT_ID = int(os.environ.get("ALLOWED_CHAT_ID", "0"))

TASK_DB_ID = "3105795f-3e22-80ad-a8ad-da12c3616a29"

notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_tasks(brand: str = None, status_filter: str = "📋 할일"):
    filters = [
        {"property": "진행상태", "select": {"equals": status_filter}}
    ]
    if brand:
        filters.append({"property": "브랜드", "select": {"equals": brand}})

    body = {
        "page_size": 100,
        "filter": {"and": filters} if len(filters) > 1 else filters[0],
        "sorts": [{"property": "카테고리", "direction": "ascending"}]
    }
    res = requests.post(
        f"https://api.notion.com/v1/databases/{TASK_DB_ID}/query",
        headers=notion_headers,
        json=body
    )
    results = res.json().get("results", [])
    tasks = []
    for r in results:
        props = r["properties"]
        name = props.get("Content name", {}).get("title", [{}])
        name_str = name[0].get("plain_text", "") if name else ""
        cat = props.get("카테고리", {}).get("select", {})
        cat_str = cat.get("name", "") if cat else ""
        br = props.get("브랜드", {}).get("select", {})
        br_str = br.get("name", "") if br else ""
        if name_str:
            tasks.append({"name": name_str, "category": cat_str, "brand": br_str, "id": r["id"]})
    return tasks


def mark_done(page_id: str):
    requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=notion_headers,
        json={"properties": {"진행상태": {"select": {"name": "✅ 완료"}}}}
    )


def build_briefing(brand: str = None):
    tasks = get_tasks(brand)
    if not tasks:
        return "오늘 할일이 없어요! 🎉"

    from collections import defaultdict
    by_cat = defaultdict(list)
    for t in tasks:
        by_cat[t["category"]].append(t["name"])

    today = date.today().strftime("%Y년 %m월 %d일")
    brand_label = brand if brand else "전체"
    lines = [f"📋 *{today} {brand_label} 할일 브리핑*\n"]
    for cat, items in sorted(by_cat.items()):
        lines.append(f"*{cat}*")
        for item in items:
            lines.append(f"  • {item}")
        lines.append("")
    return "\n".join(lines)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if ALLOWED_CHAT_ID != 0 and chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text(f"인증 실패. 당신의 chat_id: {chat_id}")
        return
    await update.message.reply_text(
        "안녕하세요! 저는 Zizi예요 👋\n\n"
        "명령어:\n"
        "/briefing - 전체 할일 브리핑\n"
        "/bowtie - 보타이 할일\n"
        "/envyu - 엔비유 할일\n"
        "/crazypocah - 미친포차 할일\n"
        "/완료 [할일명] - 완료 처리\n"
        "또는 그냥 말 걸어도 돼요!"
    )


async def briefing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    msg = build_briefing()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def brand_briefing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    brand_map = {"/bowtie": "보타이", "/envyu": "엔비유", "/crazypocah": "미친포차"}
    brand = brand_map.get(update.message.text.split()[0], "보타이")
    msg = build_briefing(brand)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    user_msg = update.message.text
    tasks = get_tasks()
    task_summary = "\n".join([f"- [{t['brand']}][{t['category']}] {t['name']}" for t in tasks[:50]])

    system_prompt = f"""당신은 Zizi, 사용자의 개인 비서 AI입니다.
사용자는 SNS 자동화 에이전시를 운영하며 보타이, 엔비유, 미친포차 브랜드를 관리합니다.
친근하고 간결하게 한국어로 답변하세요.

현재 노션 할일 목록:
{task_summary}"""

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    )
    await update.message.reply_text(response.content[0].text)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("briefing", briefing))
    app.add_handler(CommandHandler("bowtie", brand_briefing))
    app.add_handler(CommandHandler("envyu", brand_briefing))
    app.add_handler(CommandHandler("crazypocah", brand_briefing))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Zizi 봇 시작!")
    app.run_polling()


if __name__ == "__main__":
    main()
