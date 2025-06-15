import time
import requests
from bs4 import BeautifulSoup
import threading
import json

BOT_TOKEN = "TON_BOT_TOKEN_ICI"
CHAT_IDS = [5174161590]  # Tu peux ajouter d'autres ID ici

NITTER_MIRRORS = [
    "https://nitter.1d4.us",
    "https://nitter.moomoo.me",
    "https://nitter.privacydev.net",
    "https://nitter.nohost.network",
    "https://nitter.net"
]

seen_tweets = set()

def send_telegram_alert(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)

def get_working_mirror():
    for mirror in NITTER_MIRRORS:
        try:
            test = requests.get(f"{mirror}/elonmusk", timeout=8)
            if test.status_code == 200:
                return mirror
        except:
            continue
    return None

def extract_tweet_id(link):
    return link.rstrip("/").split("/")[-1]

def check_elon_tweets():
    global seen_tweets
    print("[🔍] Vérification des tweets...")

    mirror = get_working_mirror()
    if not mirror:
        print("[❌] Aucun miroir Nitter n'est accessible.")
        return

    try:
        url = f"{mirror}/elonmusk"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tweets = soup.find_all("div", class_="timeline-item")

        for tweet in tweets:
            tweet_id = tweet.get("data-id")
            if tweet_id in seen_tweets:
                continue

            content = tweet.find("div", class_="tweet-content")
            media = tweet.find("a", class_="still-image") or tweet.find("video")
            tweet_link = tweet.find("a", class_="tweet-link")["href"]
            text_content = content.text.strip() if content else ""

            if text_content == "" and media:
                tweet_id_clean = extract_tweet_id(tweet_link)
                twitter_link = f"https://twitter.com/elonmusk/status/{tweet_id_clean}"
                message = f"📸 Elon a posté un tweet sans texte :\n🔗 {twitter_link}"
                send_telegram_alert(message)
                print("[✅] Alerte envoyée :", twitter_link)

            seen_tweets.add(tweet_id)

    except Exception as e:
        print("[⚠️] Erreur :", e)

def listen_for_messages():
    last_update_id = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id + 1}"
            response = requests.get(url)
            updates = response.json()

            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message")
                if message and message.get("text"):
                    chat_id = message["chat"]["id"]
                    if message["text"].lower().strip() in ["bot", "ping", "actif", "/start"]:
                        reply_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        reply = {
                            "chat_id": chat_id,
                            "text": "🤖 Bot actif et en ligne ✅",
                            "parse_mode": "HTML"
                        }
                        requests.post(reply_url, data=reply)
        except Exception as e:
            print("[⚠️] Erreur dans le listener :", e)
        time.sleep(3)

# Démarrage
send_telegram_alert("🤖 Le bot Elon est en ligne sur Render et prêt à surveiller les tweets silencieux !")

# Démarrer l'écoute des messages en parallèle
threading.Thread(target=listen_for_messages, daemon=True).start()

# Boucle principale
while True:
    check_elon_tweets()
    time.sleep(60)
