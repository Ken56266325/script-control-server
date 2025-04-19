from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import time
import os
import json
import subprocess
from datetime import datetime, timedelta

TOKEN = "7827269976:AAGoFcXb5Nu1tthnCmKmGtSZjFoRdE3Dn8Q"

ACCESS_CODE = "562663261106"

authorized_users = set()
user_choices = {}

# Chargement des données du fichier status2.json
def load_status():
    with open('status2.json', 'r') as f:
        return json.load(f)

# Sauvegarde des données dans status2.json et push vers GitHub
def save_status(data):
    with open('status2.json', 'w') as f:
        json.dump(data, f, indent=4)
    push_to_github()

# Push vers GitHub
def push_to_github():
    try:
        subprocess.run(['git', 'add', 'status2.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Mise à jour de status2.json'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Modifications poussées vers GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du push vers GitHub : {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in authorized_users:
        await show_main_menu(update)
    else:
        await update.message.reply_text("🔒 Veuillez entrer le code d'accès pour utiliser ce bot :")

async def handle_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in authorized_users:
        if text == ACCESS_CODE:
            authorized_users.add(user_id)
            await update.message.reply_text("✅ Accès accordé !")
            await show_main_menu(update)
        else:
            await update.message.reply_text("❌ Code incorrect. Veuillez réessayer :")
    else:
        await handle_choice(update, context)

async def show_main_menu(update: Update):
    keyboard = [
        ["👤 Voir mes informations", "🔄 Renouveler un abonnement"],
        ["📞 Contacter le service client"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 Bienvenue sur *Affiliation Bot* !\n\n"
        "Choisissez une option ci-dessous :",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "👤 Voir mes informations":
        await update.message.reply_text("🔑 Veuillez entrer votre ID unique :")
        context.user_data['waiting_for_id'] = True

    elif text == "🔄 Renouveler un abonnement":
        keyboard = [["💼 Plan Basique (7 000 AR)", "🌟 Plan VIP (14 000 AR)"], ["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("💡 Choisissez un plan d'abonnement :", reply_markup=reply_markup)

    elif text in ["💼 Plan Basique (7 000 AR)", "🌟 Plan VIP (14 000 AR)"]:
        plan = "Basique" if "Basique" in text else "VIP"
        user_choices[user_id] = {"plan": plan}
        await update.message.reply_text("🔑 Veuillez entrer votre ID unique pour valider l'abonnement :")
        context.user_data['waiting_for_payment_id'] = True

    elif context.user_data.get('waiting_for_id'):
        await check_user_info(update, text)
        context.user_data['waiting_for_id'] = False

    elif context.user_data.get('waiting_for_payment_id'):
        await process_subscription(update, text, user_choices[user_id]["plan"])
        context.user_data['waiting_for_payment_id'] = False

    elif text == "✅ Confirmer le paiement":
        await update_subscription(update)

async def check_user_info(update: Update, user_id):
    status_data = load_status()
    user_info = next((user for user in status_data["scripts"] if user["id"] == user_id), None)

    if user_info:
        affiliate_balance = user_info.get("affiliation_balance", 0)
        countdown_start_time = user_info.get("countdown_start_time")

        if countdown_start_time:
            end_time = datetime.fromisoformat(countdown_start_time)
            countdown = end_time.strftime("%d/%m/%Y %H:%M")
        else:
            countdown = "Non défini"

        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"📌 **Informations de votre compte**\n\n"
            f"🆔 **ID** : `{user_id}`\n"
            f"💰 **Solde d'affiliation** : `{affiliate_balance} AR`\n"
            f"⏳ **Temps restant** : `{countdown}`\n\n"
            "Merci d'utiliser Affiliation Bot !",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ ID introuvable.")

async def process_subscription(update: Update, user_id, plan):
    status_data = load_status()
    user_info = next((user for user in status_data["scripts"] if user["id"] == user_id), None)

    if user_info:
        price = 7000 if plan == "Basique" else 14000
        balance = user_info.get("affiliation_balance", 0)

        if balance >= price:
            remaining_balance = balance - price
            user_choices[user_id] = {"user_id": user_id, "plan": plan, "price": price, "remaining_balance": remaining_balance}

            keyboard = [["✅ Confirmer le paiement"], ["⬅️ Annuler"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🆔 **ID** : `{user_id}`\n"
                f"💰 **Solde actuel** : `{balance} AR`\n"
                f"📜 **Plan sélectionné** : {plan}\n"
                f"💸 **Montant déduit** : `{price} AR`\n"
                f"💰 **Solde après activation** : `{remaining_balance} AR`\n\n"
                "✅ Confirmez le paiement pour activer l'abonnement.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"❌ Solde insuffisant !\n"
                f"🆔 **ID** : `{user_id}`\n"
                f"💰 **Solde actuel** : `{balance} AR`\n\n"
                "Veuillez contacter le service client.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text("❌ ID introuvable.")

async def update_subscription(update: Update):
    user_id = update.effective_user.id
    unique_id = user_choices[user_id]["user_id"]
    plan = user_choices[user_id]["plan"]

    status_data = load_status()

    for user in status_data["scripts"]:
        if user["id"] == unique_id:
            user["countdown_start_time"] = (datetime.now() + timedelta(days=7)).isoformat()
            user["affiliation_balance"] = user_choices[user_id]["remaining_balance"]
            user["plan"] = plan
            save_status(status_data)

            expiration_date = datetime.fromisoformat(user["countdown_start_time"]).strftime("%d/%m/%Y %H:%M")

            await update.message.reply_text(
                f"✅ **Activation réussie !**\n\n"
                f"🆔 **ID** : `{unique_id}`\n"
                f"📅 **Date d'expiration** : `{expiration_date}`\n"
                f"💰 **Solde restant** : `{user['affiliation_balance']} AR`\n\n"
                "🙏 Merci pour votre confiance !",
                parse_mode="Markdown"
            )
            await show_main_menu(update)
            break

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))
    print("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
