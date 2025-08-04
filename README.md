# Microsoft Forms AI - Web Scraper

Un script Python silencieux pour extraire automatiquement les questions des formulaires Microsoft Forms et les sauvegarder au format JSON.

## 🚀 Fonctionnalités

- **Extraction automatique** des questions depuis Microsoft Forms
- **Sauvegarde JSON** avec horodatage automatique  
- **Exécution silencieuse** sans affichage console
- **Gestion robuste des erreurs** et fermeture propre du navigateur
- **Compatible Windows** avec gestion avancée des processus Chrome

## 📋 Prérequis

- Python 3.7+
- Google Chrome installé sur le système
- Connexion Internet

## 🛠️ Installation

1. **Cloner le projet :**
```bash
git clone git@github.com:ISSAM-SALMI/Microsoft-forms-AI.git
cd Microsoft-forms-AI
```

2. **Créer un environnement virtuel :**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances :**
```bash
pip install -r requirements.txt
```

## 📖 Utilisation

### Utilisation de base

```bash
python scraping.py
```

Le script va :
1. Ouvrir automatiquement Chrome en mode furtif
2. Naviguer vers le formulaire Microsoft Forms configuré
3. Extraire toutes les questions du formulaire
4. Sauvegarder les données dans `output/microsoft_forms_data_YYYYMMDD_HHMMSS.json`
5. Fermer le navigateur proprement

### Configuration de l'URL

Pour changer l'URL du formulaire à scraper, modifiez la variable `url` dans le fichier `scraping.py` :

```python
url = "VOTRE_URL_MICROSOFT_FORMS_ICI"
```

## 📁 Structure du projet

```
Microsoft-forms-AI/
├── scraping.py          # Script principal de scraping
├── requirements.txt     # Dépendances Python
├── README.md           # Documentation
├── config.py           # (Optionnel) Configuration
├── example.py          # (Optionnel) Exemple d'usage
└── output/             # Dossier de sortie des fichiers JSON
    └── microsoft_forms_data_*.json
```

## 📊 Format de sortie JSON

Les données extraites sont sauvegardées au format JSON avec la structure suivante :

```json
{
  "url": "http://forms.office.com/pages/...",
  "scraping_date": "2025-08-04T15:42:51.618342",
  "questions": [
    {
      "question_number": 1,
      "question_text": "What is your gender?",
      "scraped_at": "2025-08-04T15:42:55.624753"
    },
    {
      "question_number": 2,
      "question_text": "Do you think AI is helpful in everyday life?",
      "scraped_at": "2025-08-04T15:42:55.639586"
    }
  ]
}
```

## ⚙️ Configuration avancée

### Options Chrome

Le script utilise les options Chrome suivantes pour une extraction optimale :

- `--no-sandbox` : Désactive le sandbox pour éviter les restrictions
- `--disable-dev-shm-usage` : Optimise l'usage mémoire
- `--disable-gpu` : Désactive l'accélération GPU
- `--disable-web-security` : Permet l'accès aux formulaires
- `--allow-running-insecure-content` : Autorise le contenu non sécurisé

### Gestion des erreurs

Le script inclut une gestion robuste des erreurs :

- **Retry automatique** en cas d'échec de connexion
- **Fermeture forcée** des processus Chrome orphelins
- **Suppression des messages d'erreur** pour une exécution silencieuse
- **Sauvegarde des erreurs** dans le fichier JSON de sortie

## 🔧 Dépannage

### Chrome ne se lance pas

```bash
# Vérifier l'installation de Chrome
chrome --version

# Réinstaller undetected-chromedriver
pip uninstall undetected-chromedriver
pip install undetected-chromedriver
```

### Erreurs de permissions

- Exécuter en tant qu'administrateur sur Windows
- Vérifier les permissions du dossier `output/`

### Formulaire non accessible

- Vérifier que l'URL du formulaire est publique
- Contrôler la connexion Internet
- S'assurer que le formulaire Microsoft Forms est actif

## 📝 Développement

### Structure de classe

```python
class MicrosoftFormsScraper:
    def __init__(self, url)              # Initialisation
    def _init_driver(self)               # Configuration Chrome  
    def _close_driver_safely(self)       # Fermeture sécurisée
    def run(self)                        # Extraction principale
    def save_to_json(self, filename)     # Sauvegarde JSON
```

### Ajout de nouvelles fonctionnalités

Pour extraire d'autres éléments du formulaire, modifier la méthode `run()` :

```python
# Exemple : extraire les options de réponse
options = item.find_elements(By.CLASS_NAME, "response-option")
question_data["options"] = [opt.text for opt in options]
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ⚠️ Avertissement

Ce script est destiné à des fins éducatives et de recherche. Respectez les conditions d'utilisation de Microsoft Forms et n'utilisez ce script que sur des formulaires dont vous avez l'autorisation d'extraire les données.

## 📞 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la documentation Microsoft Forms
- Vérifier les logs dans le dossier `output/`