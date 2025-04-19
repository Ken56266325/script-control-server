import json
import os
import subprocess
from datetime import datetime, timedelta

# Fonctions d'affichage de couleurs et d'emoji
def print_banner():
    os.system('clear')
    print("\033[1;36m=================================\033[0m")
    print("\033[1;33m  Script Control Manager\033[0m")
    print("\033[1;36m=================================\033[0m")
    print("\033[1;32m 1️⃣ Ajouter une nouvelle ID\033[0m")
    print("\033[1;32m 2️⃣ Gérer les IDs existants\033[0m")
    print("\033[1;34m 4️⃣ Voir les références\033[0m")
    print("\033[1;35m 5️⃣ Ajouter/Modifier une annonce\033[0m")  # Nouvelle option
    print("\033[1;31m 3️⃣ Quitter\033[0m")
    print("\033[1;36m=================================\033[0m")

def print_submenu():
    print("\033[1;35m=================================\033[0m")
    print("\033[1;34m 1️⃣ Activer/Désactiver\033[0m")
    print("\033[1;33m 2️⃣ Retour\033[0m")
    print("\033[1;31m 3️⃣ Supprimer l'ID\033[0m")
    print("\033[1;36m 4️⃣ Ajouter/Modifier Android ID\033[0m")  # Nouvelle option
    print("\033[1;35m=================================\033[0m")

def print_modify_android_id_options():
    print("\033[1;35m=================================\033[0m")
    print("\033[1;32m 1️⃣ Modifier l'Android ID\033[0m")
    print("\033[1;33m 2️⃣ Retour au menu précédent\033[0m")
    print("\033[1;35m=================================\033[0m")

# Charger les données du fichier status1.json
def load_status():
    with open('status1.json', 'r') as f:
        return json.load(f)

# Sauvegarder les données dans status1.json
def save_status(data):
    with open('status1.json', 'w') as f:
        json.dump(data, f, indent=4)
    push_to_github()  # Pousser les modifications sur GitHub

# Push vers GitHub
def push_to_github():
    try:
        subprocess.run(['git', 'add', 'status1.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Mise à jour de status1.json'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("\033[1;32mModifications poussées vers GitHub.\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31mErreur lors du push vers GitHub : {e}\033[0m")

# Voir les références (format corrigé avec solde d'affiliation)
def view_references():
    data = load_status()
    print("\033[1;34m=== Références ===\033[0m")
    any_references = False

    for script in data['scripts']:
        referred_to = script.get('referred_to', [])
        if referred_to:
            any_references = True
            print(f"\033[1;33m- L'ID qui a référé : {script['id']} | Solde d'affiliation: {script.get('affiliation_balance', 0)} Ar\033[0m")
            for ref_id in referred_to:
                # Trouver les détails de l'ID référée
                ref_script = next((s for s in data['scripts'] if s['id'] == ref_id), None)
                if ref_script:
                    # Calculer le compte à rebours, en le réinitialisant si l'ID est inactive
                    if ref_script['status'] == 'inactive':
                        days, hours, minutes = 0, 0, 0
                    else:
                        countdown_end = datetime.fromisoformat(ref_script['countdown_start_time'])
                        remaining_time = countdown_end - datetime.now()
                        days, seconds = remaining_time.days, remaining_time.seconds
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                    print(f"  ↪ {ref_script['id']} | Statut: {ref_script['status']} | Compte à rebours: {days}j {hours}h {minutes}m")

    if not any_references:
        print("\033[1;31mAucune ID n'a référé d'autres IDs.\033[0m")
    else:
        print("\033[1;34mOptions supplémentaires : \033[0m")
        print("\033[1;32m1️⃣ Modifier le solde d'affiliation d'une ID qui a référé\033[0m")
        print("\033[1;33m2️⃣ Retour\033[0m")
        sub_choice = int(input("\033[1;36mEntrez votre choix: \033[0m"))

        if sub_choice == 1:
            modify_affiliation_balance(data)

    print("\033[1;33mAppuyez sur Entrée pour revenir au menu principal...\033[0m")
    input()

# Modifier le solde d'affiliation d'une ID
def modify_affiliation_balance(data):
    print("\033[1;34mEntrez l'ID qui a référé (pseudo): \033[0m")
    referer_id = input("\033[1;36mID: \033[0m")

    referer_script = next((script for script in data['scripts'] if script['id'] == referer_id and script.get('referred_to')), None)
    if not referer_script:
        print("\033[1;31mCet ID n'a référé personne. Action invalide.\033[0m")
        return

    print(f"\033[1;33mSolde actuel d'affiliation de {referer_id}: {referer_script.get('affiliation_balance', 0)} Ar\033[0m")
    print("\033[1;34mEntrez le nouveau solde d'affiliation (en Ariary): \033[0m")
    new_balance = int(input("\033[1;36mSolde: \033[0m"))

    referer_script['affiliation_balance'] = new_balance
    save_status(data)
    print(f"\033[1;32mLe solde d'affiliation de {referer_id} a été modifié avec succès à {new_balance} Ar.\033[0m")

# Ajouter une nouvelle ID
def add_new_id():
    data = load_status()
    print("\033[1;34mEntrez une nouvelle ID : \033[0m")
    new_id = input("\033[1;36mID: \033[0m")

    # Vérifier si l'ID existe déjà
    if any(script['id'] == new_id for script in data['scripts']):
        print(f"\033[1;31mL'ID {new_id} existe déjà. Veuillez en saisir une autre.\033[0m")
        return

    print("\033[1;34mEntrez l'Android ID de cette ID (ID unique de l'appareil) : \033[0m")
    android_id = input("\033[1;36mAndroid ID: \033[0m")

    print("\033[1;34mEntrez l'ID qui a référé cette ID (laissez vide si aucune) : \033[0m")
    referred_by = input("\033[1;36mRéféré par: \033[0m")

    print("\033[1;34mChoisissez le statut de l'ID : \033[0m")
    print("\033[1;32m1️⃣ Active\033[0m")
    print("\033[1;31m2️⃣ Inactive\033[0m")
    status_choice = input("\033[1;36mVotre choix: \033[0m")

    status = "active" if status_choice == '1' else "inactive"

    countdown_duration = timedelta(days=7)
    countdown_start_time = datetime.now() + countdown_duration

    new_entry = {
        'id': new_id,
        'android_id': android_id,
        'referred_by': referred_by if referred_by else None,
        'referred_to': [],
        'status': status,
        'countdown_start_time': countdown_start_time.isoformat(),
        'affiliation_balance': 0  # Solde d'affiliation initialisé à 0
    }
    data['scripts'].append(new_entry)

    if referred_by:
        for script in data['scripts']:
            if script['id'] == referred_by:
                script.setdefault('referred_to', []).append(new_id)
                break

    save_status(data)
    print(f"\033[1;32mID {new_id} ajoutée avec succès.\033[0m")

# Ajouter ou modifier une annonce
def add_or_modify_announcement(data):
    if 'announcement' in data:
        print(f"\033[1;33mAnnonce existante : {data['announcement']}\033[0m")
        print("\033[1;34mVoulez-vous la modifier? (oui/non): \033[0m")
        modify_choice = input("\033[1;36mVotre choix: \033[0m")

        if modify_choice.lower() == 'oui':
            print("\033[1;34mEntrez la nouvelle annonce: \033[0m")
            announcement = input("\033[1;36mAnnonce: \033[0m")
            data['announcement'] = announcement
            save_status(data)
            print(f"\033[1;32mAnnonce modifiée avec succès.\033[0m")
        else:
            print("\033[1;31mAucune modification effectuée.\033[0m")
    else:
        print("\033[1;34mEntrez une annonce à ajouter: \033[0m")
        announcement = input("\033[1;36mAnnonce: \033[0m")
        data['announcement'] = announcement
        save_status(data)
        print(f"\033[1;32mAnnonce ajoutée avec succès.\033[0m")

# Gérer les IDs existants
def manage_existing_ids():
    data = load_status()
    print("\033[1;34mGérer les IDs existants\033[0m")
    for i, script in enumerate(data['scripts']):
        # Calcul du compte à rebours pour chaque ID
        if script['status'] == 'inactive':
            days, hours, minutes = 0, 0, 0
        else:
            countdown_end = datetime.fromisoformat(script['countdown_start_time'])
            remaining_time = countdown_end - datetime.now()
            days, seconds = remaining_time.days, remaining_time.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
        
        print(f"{i+1}. ID: {script['id']} | Statut: {script['status']} | Compte à rebours: {days}j {hours}h {minutes}m")

    print("\033[1;36mChoisissez une ID à gérer (numéro) ou 0 pour revenir : \033[0m")
    choice = int(input("\033[1;36mEntrez votre choix: \033[0m"))

    if choice == 0:
        return

    selected_script = data['scripts'][choice - 1]
    print(f"\033[1;34mL'ID choisie est: {selected_script['id']}\033[0m")
    print_submenu()

    sub_choice = int(input("\033[1;36mEntrez votre choix: \033[0m"))

    if sub_choice == 1:
        if selected_script['status'] == 'inactive':
            print(f"\033[1;34mL'ID {selected_script['id']} sera maintenant activée.\033[0m")
            selected_script['status'] = 'active'
            selected_script['countdown_start_time'] = (datetime.now() + timedelta(days=7)).isoformat()
            save_status(data)
            print(f"\033[1;32mID {selected_script['id']} activée avec succès.\033[0m")
        else:
            print(f"\033[1;34mL'ID {selected_script['id']} sera maintenant désactivée.\033[0m")
            selected_script['status'] = 'inactive'
            save_status(data)
            print(f"\033[1;32mID {selected_script['id']} désactivée avec succès.\033[0m")

    elif sub_choice == 2:
        return
    elif sub_choice == 3:
        print(f"\033[1;31mL'ID {selected_script['id']} a été supprimée.\033[0m")
        data['scripts'].remove(selected_script)
        save_status(data)

    elif sub_choice == 4:
        if 'android_id' in selected_script:
            print(f"\033[1;31mL'Android ID de {selected_script['id']} existe déjà: {selected_script['android_id']}\033[0m")
            print_modify_android_id_options()
            modify_choice = int(input("\033[1;36mEntrez votre choix: \033[0m"))

            if modify_choice == 1:
                print("\033[1;34mEntrez le nouvel Android ID : \033[0m")
                android_id = input("\033[1;36mAndroid ID: \033[0m")
                selected_script['android_id'] = android_id
                save_status(data)
                print(f"\033[1;32mL'Android ID de {selected_script['id']} a été modifié avec succès.\033[0m")
            elif modify_choice == 2:
                return
        else:
            print("\033[1;34mEntrez l'Android ID de cette ID: \033[0m")
            android_id = input("\033[1;36mAndroid ID: \033[0m")
            selected_script['android_id'] = android_id
            save_status(data)
            print(f"\033[1;32mL'Android ID de {selected_script['id']} a été ajouté avec succès.\033[0m")

# Fonction principale du script
def main():
    while True:
        print_banner()
        choice = int(input("\033[1;36mVotre choix: \033[0m"))
        if choice == 1:
            add_new_id()
        elif choice == 2:
            manage_existing_ids()
        elif choice == 4:
            view_references()
        elif choice == 5:
            data = load_status()
            add_or_modify_announcement(data)  # Nouvelle option pour modifier l'annonce
        elif choice == 3:
            print("\033[1;31mAu revoir!\033[0m")
            break
        else:
            print("\033[1;31mChoix invalide. Essayez de nouveau.\033[0m")

if __name__ == '__main__':
    main()
