import os
import random
import threading
import telebot
from groq import Groq
from flask import Flask

# === CONFIGURAZIONE ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# === FRASI RANDOM DEL TUO AMICO (Aggiornate: lui e la moglie sono chiropratici) ===
FRASI_AMICO = [
    # Classiche
    "Fidati.",

    # Chiropratica (Lui e la moglie sono chiropratici)
    "Oggi in studio ho aggiustato tre cervicale, sono distrutto ma soddisfatto.",
    "Mia moglie è più brava di me a scrocchicare le vertebre, ma non dirlo a nessuno o ti scrocchio il collo per bene.",
    "La chiropratica ti cambia la vita, non c'è niente di meglio.",
    "Se hai un problema posturale, portalo da noi che lo sistemiamo in due secondi.",
    "Sto studiando una nuova tecnica per la lombare, è pazzesca.",
    "Per la risposta che ti ho dato, applicando le stesse tariffe che uso a lavoro, sono circa... sì 45€.",
    "Molto interessante, però tenere tutto questo tempo il telefono in mano fa male ai polsi, fammi dare un'occhiata.",

    # Viaggi in moto
    "Appena posso prendo la moto e scappo, ho bisogno di aria.",
    "Dovresti venire con me in moto il prossimo weekend, che roba.",
    "Non c'è niente di meglio del vento in faccia sulla moto, te lo dico io.",
    "Sto già pensando al prossimo viaggio in moto, ho la testa lì.",
    "La moto è l'unica vera terapia, credimi.",

    # Estonia / Moglie estone
    "Sai com'è, mia moglie dice che in Estonia si fa così, e lei ha sempre ragione.",
    "Un giorno o l'altro ti porto in Estonia, vedrai che roba.",
    "Mia moglie mi guarda male se dico queste cose, ma vabbè.",
    "Sto imparando un po' di estone, ma è un casino giuro."
]

# === SYSTEM PROMPT: ISTRUISCE IL LLM A PARLARE COME FABRIZIO ===
SYSTEM_PROMPT = """Sei un chatbot che risponde come se fossi il mio amico Fabrizio.

Caratteristiche di Fabrizio:
- Rispondi in italiano informale, come se parlassi con un amico su WhatsApp.
- Usa un tono amichevole, diretto e a volte un po' sfottente ma affettuoso.
- Risposte brevi (1-3 frasi massimo).
- Sei un chiropratico (e anche tua moglie lo è), sei appassionato di viaggi in moto e tua moglie è estone (a volte fai riferimenti all'Estonia, a lei o al vostro studio).
- Usa qualche emoji ogni tanto, ma mai usando facce felici.
- Sii naturale, non sembrare un robot.
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
        # Se questo modello dà errore, vai su console.groq.com/playground e copia il nome esatto dal menu a tendina
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
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

        # COMBINA: La risposta dell'IA viene SEMPRE prima, la frase dell'amico SEMPRE dopo
        testo_finale = f"{risposta_llm}\n\n{frase_random}"

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