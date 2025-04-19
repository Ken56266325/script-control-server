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

def load_status():
    with open('status2.json', 'r') as f:
        return json.load(f)

def save_status(data):
    with open('status2.json', 'w') as f:
        json.dump(data, f, indent=4)
    push_to_github()

def push_to_github():
    try:
        subprocess.run(['git', 'add', 'status2.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Mise à jour de status2.json'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Modifications poussées vers GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du push vers GitHub : {e}")

def load_user_data():
    if not os.path.exists('user_data.json'):
        with open('user_data.json', 'w') as f:
            json.dump({}, f)
    with open('user_data.json', 'r') as f:
        return json.load(f)

def save_user_data(data):
    with open('user_data.json', 'w') as f:
        json.dump(data, f, indent=4)

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
            await check_user_registration(update, context)
        else:
            await update.message.reply_text("❌ Code incorrect. Veuillez réessayer :")
    else:
        await handle_choice(update, context)

async def check_user_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_data = load_user_data()

    if str(user_id) in user_data:
        await show_main_menu(update)
    else:
        await update.message.reply_text("⚠️ ATTENTION : Veuillez entrer votre ID unique. Cette action est irréversible. Vérifiez bien votre ID avant de soumettre.")
        context.user_data['waiting_for_id'] = True

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
        await show_user_info(update, user_id)

    elif text == "🔄 Renouveler un abonnement":
        keyboard = [["💼 Plan Basique (7 000 AR)", "🌟 Plan VIP (14 000 AR)"], ["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("💡 Choisissez un plan d'abonnement :", reply_markup=reply_markup)

    elif text in ["💼 Plan Basique (7 000 AR)", "🌟 Plan VIP (14 000 AR)"]:
        plan = "Basique" if "Basique" in text else "VIP"
        user_choices[user_id] = {"plan": plan}
        await process_subscription(update, user_id, plan)

    elif text == "📞 Contacter le service client":
        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "📞 Pour contacter le service client, vous pouvez envoyer un message à @kenny56266 ou appeler l'un des numéros suivants : 0339248918 ou 0389561802.\n\n"
            "⏰ Les horaires de disponibilité sont :\n"
            "🕖 Matin : 7h00 à 11h00\n"
            "🕑 Après-midi : 14h00 à 19h00\n\n"
            "⚠️ Nous ne recevons pas d'appels après 20h00. Si vous nous contactez en dehors de ces heures, nous vous remercions pour votre patience. "
            "Soyez assuré que nous reviendrons vers vous dès que nous serons à nouveau disponibles.\n\n"
            "Merci de votre compréhension et de votre patience.",
            reply_markup=reply_markup
        )

    elif text == "⬅️ Retour au menu principal":
        await show_main_menu(update)

    elif context.user_data.get('waiting_for_id'):
        await register_user(update, context, text)
        context.user_data['waiting_for_id'] = False

    elif text == "✅ Activer mon ID":
        await confirm_payment(update, context)

    elif text == "✅ Activer un autre ID":
        await activate_another_id(update, context)

    elif text == "❌ Annuler":
        await show_main_menu(update)

    elif context.user_data.get('waiting_for_another_id'):
        await handle_another_id(update, context, text)
        context.user_data['waiting_for_another_id'] = False

    elif text == "✅ Confirmer le paiement":
        if "another_id" in user_choices[user_id]:
            await confirm_another_payment(update, context)
        else:
            await confirm_payment(update, context)

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE, unique_id: str):
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_data = load_user_data()
    status_data = load_status()

    if unique_id in [user["id"] for user in status_data["scripts"]]:
        if unique_id in user_data.values():
            await update.message.reply_text("❌ Cet ID est déjà associé à un autre utilisateur. Veuillez entrer votre propre ID.")
        else:
            user_data[str(user_id)] = unique_id
            save_user_data(user_data)
            await update.message.reply_text("✅ Votre ID a été enregistré avec succès !")
            await show_main_menu(update)
    else:
        await update.message.reply_text("❌ ID introuvable. Veuillez vérifier et réessayer.")

async def show_user_info(update: Update, user_id: int):
    user_data = load_user_data()
    unique_id = user_data.get(str(user_id))
    status_data = load_status()
    user_info = next((user for user in status_data["scripts"] if user["id"] == unique_id), None)

    if user_info:
        affiliate_balance = user_info.get("affiliation_balance", 0)
        countdown_start_time = user_info.get("countdown_start_time")

        if countdown_start_time:
            end_time = datetime.fromisoformat(countdown_start_time)
            remaining_time = end_time - datetime.now()
            days, hours, minutes = remaining_time.days, (remaining_time.seconds // 3600) % 24, (remaining_time.seconds // 60) % 60
            countdown = f"{days} jours, {hours} heures, {minutes} minutes"
        else:
            countdown = "Non défini"

        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"📌 **Informations de votre compte**\n\n"
            f"🆔 **ID** : `{unique_id}`\n"
            f"💰 **Solde d'affiliation** : `{affiliate_balance} AR`\n"
            f"⏳ **Temps restant** : `{countdown}`\n\n"
            "Merci d'utiliser Affiliation Bot !",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ ID introuvable.", reply_markup=reply_markup)

async def process_subscription(update: Update, user_id: int, plan: str):
    user_data = load_user_data()
    unique_id = user_data.get(str(user_id))
    status_data = load_status()
    user_info = next((user for user in status_data["scripts"] if user["id"] == unique_id), None)

    if user_info:
        price = 7000 if plan == "Basique" else 14000
        balance = user_info.get("affiliation_balance", 0)

        if balance >= price:
            remaining_balance = balance - price
            user_choices[user_id] = {"plan": plan, "price": price, "remaining_balance": remaining_balance, "user_id": unique_id}

            keyboard = [["✅ Activer mon ID", "✅ Activer un autre ID"], ["❌ Annuler"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🆔 **ID** : `{unique_id}`\n"
                f"💰 **Solde actuel** : `{balance} AR`\n"
                f"📜 **Plan sélectionné** : {plan}\n"
                f"💸 **Montant à déduire** : `{price} AR`\n"
                f"💰 **Solde après activation** : `{remaining_balance} AR`\n\n"
                "Choisissez une option ci-dessous :",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            keyboard = [["⬅️ Retour au menu principal"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"❌ Solde insuffisant !\n"
                f"🆔 **ID** : `{unique_id}`\n"
                f"💰 **Solde actuel** : `{balance} AR`\n\n"
                "Veuillez contacter le service client.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ ID introuvable.", reply_markup=reply_markup)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    unique_id = user_choices[user_id]["user_id"]
    plan = user_choices[user_id]["plan"]
    price = user_choices[user_id]["price"]
    remaining_balance = user_choices[user_id]["remaining_balance"]

    status_data = load_status()
    for user in status_data["scripts"]:
        if user["id"] == unique_id:
            # Mise à jour du countdown
            current_time = datetime.now()
            new_time = current_time + timedelta(days=7)
            user["countdown_start_time"] = new_time.isoformat()

            # Mise à jour du solde et du plan
            user["affiliation_balance"] = remaining_balance
            user["plan"] = plan

            # Sauvegarde des modifications
            save_status(status_data)

            # Affichage du ticket de confirmation
            expiration_date = new_time.strftime("%d/%m/%Y %H:%M")
            keyboard = [["⬅️ Retour au menu principal"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🎉 **Activation réussie !**\n\n"
                f"🆔 **ID** : `{unique_id}`\n"
                f"📜 **Plan activé** : {plan}\n"
                f"📅 **Date d'expiration** : {expiration_date}\n"
                f"💰 **Solde restant** : `{remaining_balance} AR`\n\n"
                "Merci d'utiliser Affiliation Bot !",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            break

async def activate_another_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 Veuillez entrer l'ID unique de la personne à activer :")
    context.user_data['waiting_for_another_id'] = True

async def handle_another_id(update: Update, context: ContextTypes.DEFAULT_TYPE, another_id: str):
    user_id = update.effective_user.id
    status_data = load_status()
    user_info = next((user for user in status_data["scripts"] if user["id"] == another_id), None)

    if user_info:
        plan = user_choices[user_id]["plan"]
        price = user_choices[user_id]["price"]
        remaining_balance = user_choices[user_id]["remaining_balance"]

        if remaining_balance >= price:
            user_choices[user_id]["another_id"] = another_id

            keyboard = [["✅ Confirmer le paiement"], ["❌ Annuler"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🆔 **ID à activer** : `{another_id}`\n"
                f"📜 **Plan sélectionné** : {plan}\n"
                f"💸 **Montant à déduire** : `{price} AR`\n"
                f"💰 **Solde après activation** : `{remaining_balance} AR`\n\n"
                "✅ Confirmez le paiement pour activer l'abonnement.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            keyboard = [["⬅️ Retour au menu principal"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"❌ Solde insuffisant !\n"
                f"🆔 **ID** : `{user_id}`\n"
                f"💰 **Solde actuel** : `{remaining_balance} AR`\n\n"
                "Veuillez contacter le service client.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ ID introuvable.", reply_markup=reply_markup)

async def confirm_another_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    unique_id = user_choices[user_id]["another_id"]
    plan = user_choices[user_id]["plan"]
    price = user_choices[user_id]["price"]
    remaining_balance = user_choices[user_id]["remaining_balance"]

    status_data = load_status()
    for user in status_data["scripts"]:
        if user["id"] == unique_id:
            # Mise à jour du countdown pour l'ID activé
            current_time = datetime.now()
            new_time = current_time + timedelta(days=7)
            user["countdown_start_time"] = new_time.isoformat()
            user["plan"] = plan

            # Mise à jour du solde de l'ID qui a effectué le paiement
            payer_id = user_choices[user_id]["user_id"]
            for payer in status_data["scripts"]:
                if payer["id"] == payer_id:
                    payer["affiliation_balance"] = remaining_balance
                    break

            # Sauvegarde des modifications
            save_status(status_data)

            # Affichage du ticket de confirmation
            expiration_date = new_time.strftime("%d/%m/%Y %H:%M")
            keyboard = [["⬅️ Retour au menu principal"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🎉 **Activation réussie !**\n\n"
                f"🆔 **ID activé** : `{unique_id}`\n"
                f"📜 **Plan activé** : {plan}\n"
                f"📅 **Date d'expiration** : {expiration_date}\n"
                f"💰 **Solde restant** : `{remaining_balance} AR`\n\n"
                "Merci d'utiliser Affiliation Bot !",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
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
