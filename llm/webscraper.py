import feedparser
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChannel
import re
from datetime import datetime, timedelta
import requests

keywords = [
    "flood", "flooding", "flash flood", "overflow", "rain", "heavy rain",
    "thunderstorm", "rainfall", "monsoon", "showers", "waterlogging",
    "wet weather", "cloudburst"
]

api_id = 26400986     
api_hash = 'dbf835dfc90d04484be6274b8490bf65'  
msg_entries = []

with TelegramClient('nea_session', api_id, api_hash) as client:
    channel = client.get_entity('https://t.me/PUBFloodAlerts')  
    messages = list(client.iter_messages(channel, limit=5)) 

    for message in messages:
        text = message.text.lower() if message.text else ""
        if any(keyword in text for keyword in keywords):
            print(f"⚠️ Alert: {message.text[:200]}")
            print(f"⚠️ At: {(message.date + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')}") 
            msg_entries.append(message)

    if not msg_entries:
        print("✅ No flood or rain-related news found in the PUB telegram channel.")

news_channel = [
    "https://www.channelnewsasia.com/rssfeeds/8395986", 
    "https://www.straitstimes.com/news/singapore/rss.xml", 
    "https://feeds.singaporenews.net/rss/a677a0718b69db72"
]
news_entries = []

for news in news_channel:
    rss = feedparser.parse(news)
    for entry in rss.entries:
        title = entry.title.lower()
        summary = entry.get("summary", "").lower()
        combined_text = title + " " + summary

        if any(re.search(rf'\b{re.escape(keyword)}\b', combined_text) for keyword in keywords):
            news_entries.append(entry)

    if news_entries:
        print("[!] Weather-Related Alerts Found:\n")
        for i, entry in enumerate(news_entries, 1):
            print(f"{i}. {entry.title}")
            print(f"   Link: {entry.link}")
            print(f"   Summary: {entry.get('summary', 'No summary available.')}\n")
    else:
        print("✅ No flood or rain-related news found in the latest feed.")

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

telegram_text = ""
if msg_entries:
    telegram_text = "\n".join([
        f"- {msg.text[:200]}\n  Sent: {(msg.date + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')}"
        for msg in msg_entries if msg.text
    ])
else:
    telegram_text = "No flood or rain-related messages found in the PUB Telegram channel."

rss_text = ""
if news_entries:
    rss_text = "\n".join([
        f"- {entry.title}\n"
        f"  Published: {entry.get('published', 'No date provided')}\n"
        f"  Link: {entry.link}\n"
        f"  Summary: {entry.get('summary', 'No summary available.')}\n"
        for entry in news_entries
    ])
else:
    rss_text = "No weather-related news found in Singapore news channels."

# 🧠 The prompt stays the same
prompt = f"""You are a concise assistant supporting a bus operator in Singapore.

It is currently {now}.

Based strictly on the following weather alerts, identify whether any *heavy rain or flooding* occurred in the **past 7 days**.

Do not speculate. Only summarize what is explicitly mentioned.

Separate each point that you make with bullet points for readability.

---

📢 Telegram PUB Flood Alerts:
{telegram_text}

📰 News Headlines (RSS Feeds):
{rss_text}

---

Your response must:
- State if rain or flood is confirmed today and within the past 7 days
- Mention affected areas or dates if known
- Advise whether buses should be rerouted
- Be short, informative, and no more than **3 bullet points**"""

# Call LLM
url = "http://localhost:11434/api/generate"
payload = {
    "model": "phi3:3.8b",  # This is your installed Phi 3.8B model
    "prompt": prompt,
    "stream": False
}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        print("✅ Summary generated:")
        print(result["response"])

        # Save to file so your dashboard reads it
        with open("deepseek.txt", "w", encoding="utf-8") as f:
            f.write(result["response"])
        print("✅ Summary saved to deepseek.txt")
    else:
        print(f"❌ Ollama error: {response.status_code} — {response.text}")
except Exception as e:
    print(f"❌ Failed to connect to Ollama: {str(e)}")

