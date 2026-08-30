import os
import random
import threading
import telebot
from groq import Groq
from flask import Flask

# === CONFIGURAZIONE ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# === FRASI RANDOM DEL TUO AMICO ===
FRASI_AMICO = [
    "No vabbè, ma ti rendi conto?",
    "Bro, cioè, non ci posso credere",
    "Giuro su Dio, è così",
    "Fra, ma tipo, pensaci un attimo",
    "Oh raga, ma che stai dicendo?",
    "Nel senso, è palese no?",
    "Praticamente, manco a farlo apposta",
    "Cioè, ma sei serio?",
    "No perché tipo, io la vedo così",
    "Ma che ne so, chiedilo a qualcun altro lol",
    "Vabbè dai, non esagerare",
    "Te lo giuro, è la verità",
    "Ma tipo, davvero?",
    "Oh, bella questa",
    "Senti, io parlo per esperienza"
]

# === SYSTEM PROMPT: ISTRUISCE IL LLM A PARLARE COME LUI ===
SYSTEM_PROMPT = """Sei un chatbot che risponde come se fossi Fabrizio.

Caratteristiche:
- Rispondi in italiano informale
- Usa un tono amichevole e diretto
- Risposte brevi (1-3 frasi)
- Non essere troppo formale
- Usa qualche emoji ogni tanto
- Non ripetere sempre le stesse cose
- Sii naturale, non forzare lo stile
"""

# === INIZIALIZZAZIONE ===
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Aggiunto per evitare conflitti (Error 409) su Render
bot.remove_webhook()

# === SERVER FINTO PER RENDER (soddisfa il controllo della porta) ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot attivo"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === GESTIONE MESSAGGI ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_msg = message.text
    try:
        # Chiedi a Groq una risposta sensata
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # modello gratis e veloce
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=150,
            temperature=0.8
        )

        risposta_llm = response.choices[0].message.content.strip()

        # Aggiungi 1 frase random dell'amico
        frase_random = random.choice(FRASI_AMICO)

        # Combina (a volte prima, a volte dopo)
        if random.random() > 0.5:
            testo_finale = f"{risposta_llm}\n\n{frase_random}"
        else:
            testo_finale = f"{frase_random}\n\n{risposta_llm}"

        bot.reply_to(message, testo_finale)

    except Exception as e:
        # 'flush=True' forza la stampa immediata nei log di Render
        print(f"ERRORE GRAVE: {e}", flush=True)

        # Invia l'errore tecnico direttamente a te su Telegram per debug
        messaggio_errore = f"Bro, ho un attimo di crisi, riprova 😅\n\n🔍 Errore tecnico: {e}"
        bot.reply_to(message, messaggio_errore)

# === AVVIO ===
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("Bot avviato!")
    bot.infinity_polling()