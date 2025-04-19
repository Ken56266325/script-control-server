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
        await confirm_payment(update, context)

    elif text in ["Mvola", "AirtelMoney"]:
        await handle_payment(update, context, text)

    elif text == "⬅️ Annuler":
        await show_main_menu(update)

    elif context.user_data.get('waiting_for_transaction_id'):
        await handle_transaction_id(update, context, text)

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
            missing_amount = price - balance
            user_choices[user_id] = {"plan": plan, "price": price, "missing_amount": missing_amount, "user_id": unique_id}

            keyboard = [["Mvola", "AirtelMoney"], ["⬅️ Annuler"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"❌ Solde insuffisant !\n"
                f"🆔 **ID** : `{unique_id}`\n"
                f"📜 **Plan sélectionné** : {plan}\n"
                f"💰 **Solde actuel** : `{balance} AR`\n"
                f"💸 **Montant manquant** : `{missing_amount} AR`\n\n"
                "💳 Choisissez une méthode de paiement pour compléter le montant manquant :",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        keyboard = [["⬅️ Retour au menu principal"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("❌ ID introuvable.", reply_markup=reply_markup)

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str):
    user_id = update.effective_user.id
    user_choices[user_id]["payment_method"] = method
    missing_amount = user_choices[user_id]["missing_amount"]

    if method == "Mvola":
        await update.message.reply_text(
            f"📱 **Mvola**\n\n"
            f"Numéro : 0389561802\n"
            f"Nom du destinataire : Ravonindratefy Todisoa Fitahina\n"
            f"Montant : {missing_amount} AR\n\n"
            "📌 Après avoir effectué le paiement, cliquez sur **Confirmer le paiement** ou **Annuler**.",
            reply_markup=ReplyKeyboardMarkup([["Confirmer le paiement", "⬅️ Annuler"]], resize_keyboard=True)
        )
    elif method == "AirtelMoney":
        await update.message.reply_text(
            f"📱 **AirtelMoney**\n\n"
            f"Numéro : 0339248918\n"
            f"Nom du destinataire : Ravonindratefy Todisoa Fitahina\n"
            f"Montant : {missing_amount} AR\n\n"
            "📌 Après avoir effectué le paiement, cliquez sur **Confirmer le paiement** ou **Annuler**.",
            reply_markup=ReplyKeyboardMarkup([["Confirmer le paiement", "⬅️ Annuler"]], resize_keyboard=True)
        )

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['waiting_for_transaction_id'] = True
    await request_transaction_id(update, context, user_choices[user_id]["payment_method"])

async def request_transaction_id(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str):
    await update.message.reply_text(
        f"🔢 Veuillez fournir l'ID de la transaction ({method}) comme indiqué dans l'image ci-dessous :",
        reply_markup=ReplyKeyboardMarkup([["⬅️ Retour"]], resize_keyboard=True)
    )
    await update.message.reply_text("\u26D4ILAY TRANS ID/REF/REFERENCE OHATRA NY VOASIROTRA @SARY IO IHANY NO HOMENA TOMPOKO,TSY ASINA ZAVATRA HAFA MIARAKA AMINY,ARY HAMARINO TSARA VAO ALEFA,RAH SANATRIA KA DISO,DIA MIVEREINA ANY @ 'MENU PRINCIPALE'")
    await update.message.reply_photo("AgACAgQAAxkBAAIVEGeSjpRlV3OgawcDu6A5DYSWgM3PAAJoxzEbAWaZUNcuknIHlLimAQADAgADeQADNgQ")

async def handle_transaction_id(update: Update, context: ContextTypes.DEFAULT_TYPE, transaction_id: str):
    user_id = update.effective_user.id
    user_choices[user_id]["transaction_id"] = transaction_id
    context.user_data['waiting_for_transaction_id'] = False

    if await verify_payment(update):
        await update.message.reply_text("✅ Paiement confirmé !")
        await activate_subscription(update, context)
    else:
        await update.message.reply_text("❌ Paiement non trouvé. Veuillez réessayer ou contacter le service client.")

async def verify_payment(update: Update):
    user_id = update.effective_user.id
    transaction_id = user_choices[user_id].get("transaction_id")
    payment_method = user_choices[user_id].get("payment_method")
    missing_amount = user_choices[user_id].get("missing_amount")

    file_path = "/data/data/com.termux/files/home/sms_filtered.txt"
    used_file_path = "/data/data/com.termux/files/home/used_transactions1.txt"

    # Vérifier si la transaction existe déjà dans le fichier used_transactions.txt
    if os.path.exists(used_file_path):
        with open(used_file_path, 'r') as used_file:
            used_transactions = used_file.readlines()
            for line in used_transactions:
                if transaction_id in line:
                    return False  # Refuser l'activation si le trans_id/ref est déjà utilisé

    # Si pas trouvé dans used_transactions.txt, vérifier dans sms_filtered.txt
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        for line in lines:
            # Recherche si le Trans ID et le montant sont présents dans la ligne
            if payment_method == "AirtelMoney" and f"Trans ID: {transaction_id}" in line:
                # Extraire le montant depuis la ligne
                try:
                    montant = int(line.split("Montant:")[1].split(" Ar")[0].strip())
                    # Vérifier si le montant est supérieur ou égal à celui requis
                    if montant >= missing_amount:
                        # Supprimer l'entrée du fichier après activation
                        remove_transaction_from_file(file_path, transaction_id, used_file_path)
                        return True
                except ValueError:
                    continue  # Si le montant n'est pas un nombre, passer à la ligne suivante

            elif payment_method == "Mvola" and f"Ref ID: {transaction_id}" in line:
                try:
                    montant = int(line.split("Montant:")[1].split(" Ar")[0].strip())
                    if montant >= missing_amount:
                        # Supprimer l'entrée du fichier après activation
                        remove_transaction_from_file(file_path, transaction_id, used_file_path)
                        return True
                except ValueError:
                    continue

    return False

def remove_transaction_from_file(file_path, transaction_id, used_file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if transaction_id not in line:
                file.write(line)

    # Enregistrer la transaction dans le fichier des transactions utilisées
    with open(used_file_path, 'a') as used_file:
        used_file.write(f"{transaction_id}\n")

async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    unique_id = user_choices[user_id]["user_id"]
    plan = user_choices[user_id]["plan"]
    price = user_choices[user_id]["price"]
    missing_amount = user_choices[user_id]["missing_amount"]

    status_data = load_status()
    for user in status_data["scripts"]:
        if user["id"] == unique_id:
            # Mise à jour du countdown
            current_time = datetime.now()
            new_time = current_time + timedelta(days=7)
            user["countdown_start_time"] = new_time.isoformat()

            # Mise à jour du solde et du plan
            user["affiliation_balance"] = 0
            user["plan"] = plan

            # Sauvegarde des modifications
            save_status(status_data)

            # Affichage du ticket de confirmation
            expiration_date = new_time.strftime("%d/%m/%Y %H:%M")
            keyboard = [["✅ Activer mon ID", "✅ Activer un autre ID"], ["⬅️ Retour au menu principal"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🎉 **Activation réussie !**\n\n"
                f"🆔 **ID** : `{unique_id}`\n"
                f"📜 **Plan activé** : {plan}\n"
                f"📅 **Date d'expiration** : {expiration_date}\n"
                f"💰 **Solde restant** : `0 AR`\n\n"
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
