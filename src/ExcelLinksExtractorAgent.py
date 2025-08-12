import pandas as pd
from pathlib import Path
from typing import List, Optional

def get_links_list(data_path: Optional[str] = None) -> List[str]:
    """Return list of links from second column of first Excel file found."""
    if data_path is None:
        data_path = Path(r"..\data\input")
    else:
        data_path = Path(data_path)
    excel_files = []
    for ext in ['*.xlsx', '*.xls', '*.xlsm']:
        excel_files.extend(data_path.glob(ext))
    if not excel_files:
        print("Aucun fichier Excel trouvé dans le répertoire")
        return []
    file_path = excel_files[0]
    try:
        df = pd.read_excel(file_path)
        if df.shape[1] < 2:
            print("Le fichier ne contient pas au moins deux colonnes.")
            return []
        links = [str(v).strip() for v in df.iloc[:, 1].dropna().tolist() if str(v).strip().startswith('http')]
        return links
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel: {e}")
        return []

def extract_links_from_excel_column2(data_path=None):
    links = get_links_list(data_path)
    for link in links:
        print(link)

if __name__ == "__main__":
    extract_links_from_excel_column2()
