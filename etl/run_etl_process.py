import subprocess


# Couleurs ANSI pour la sortie console
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def run_script(script_name):
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Colors.FAIL}Erreur lors de l'exécution de {script_name} : {result.stderr}{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}Exécution réussie de {script_name} : {result.stdout.strip()}{Colors.ENDC}")


def main():
    print(f"{Colors.HEADER}{Colors.BOLD}Démarrage du processus ETL GTFS...{Colors.ENDC}")

    # Étape 1 : Téléchargement des données GTFS statiques
    print(f"(1/3) {Colors.OKBLUE}Téléchargement des données GTFS statiques...{Colors.ENDC}")
    run_script("etl/gtfs_static_download.py")

    # Étape 2 : Téléchargement des données GTFS en temps réel
    print(f"(2/3) {Colors.OKCYAN}Téléchargement des données GTFS en temps réel...{Colors.ENDC}")
    run_script("etl/gtfs_rt_download.py")

    # Étape 3 : Extraction et chargement des données GTFS dans MongoDB
    print(f"(3/3) {Colors.OKBLUE}Chargement des données GTFS dans MongoDB...{Colors.ENDC}")
    run_script("etl/load_gtfs_data.py")

    print(f"{Colors.OKGREEN}{Colors.BOLD}Processus ETL terminé.{Colors.ENDC}")


if __name__ == "__main__":
    main()
