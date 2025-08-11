import pandas as pd
from pathlib import Path

def extract_links_from_excel_column2(data_path=None):
    if data_path is None:
        data_path = Path(r"..\data\input")
    else:
        data_path = Path(data_path)
    excel_files = []
    for ext in ['*.xlsx', '*.xls', '*.xlsm']:
        excel_files.extend(data_path.glob(ext))
    if not excel_files:
        print("Aucun fichier Excel trouvé dans le répertoire")
        return

    file_path = excel_files[0]
    try:
        df = pd.read_excel(file_path)
        if df.shape[1] < 2:
            print("Le fichier ne contient pas au moins deux colonnes.")
            return
        links = df.iloc[:, 1].dropna().tolist()
        for link in links:
            print(link)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")

if __name__ == "__main__":
    extract_links_from_excel_column2()
