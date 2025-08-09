import os
import pandas as pd
from pathlib import Path

class ExcelReaderAgent:
    def __init__(self, data_path=None):
        if data_path is None:
            self.data_path = Path(r"C:\Users\abdel\OneDrive\Bureau\Microsoft-forms-AI\data\input")
        else:
            self.data_path = Path(data_path)
        
        self.current_file = None
        self.current_data = None
        print(f"ExcelReaderAgent initialisé avec le chemin: {self.data_path}")
    
    def list_excel_files(self):
        if not self.data_path.exists():
            print(f"Le chemin {self.data_path} n'existe pas")
            return []
        
        excel_files = []
        for ext in ['*.xlsx', '*.xls', '*.xlsm']:
            excel_files.extend(self.data_path.glob(ext))
        
        print(f"Fichiers Excel trouvés: {len(excel_files)}")
        for i, file in enumerate(excel_files):
            print(f"  {i+1}. {file.name}")
        
        return excel_files
    
    def load_excel_file(self, filename=None, sheet_name=0):
        if filename is None:
            excel_files = self.list_excel_files()
            if not excel_files:
                print("Aucun fichier Excel trouvé")
                return False
            
            filename = excel_files[0].name
            print(f"Chargement automatique du premier fichier: {filename}")
        
        file_path = self.data_path / filename
        
        if not file_path.exists():
            print(f"Fichier non trouvé: {file_path}")
            return False
        
        try:
            self.current_data = pd.read_excel(file_path, sheet_name=sheet_name)
            self.current_file = filename
            print(f"Fichier chargé avec succès: {filename}")
            print(f"Dimensions: {self.current_data.shape[0]} lignes, {self.current_data.shape[1]} colonnes")
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du fichier: {e}")
            return False
    
    def get_columns_info(self):
        if self.current_data is None:
            print("Aucun fichier chargé")
            return None
        
        columns_info = []
        for i, col in enumerate(self.current_data.columns):
            col_info = {
                'index': i,
                'name': col,
                'dtype': str(self.current_data[col].dtype),
                'non_null_count': self.current_data[col].count(),
                'null_count': self.current_data[col].isnull().sum()
            }
            columns_info.append(col_info)
        
        print("Informations des colonnes:")
        for info in columns_info:
            print(f"  {info['index']}: {info['name']} ({info['dtype']}) - {info['non_null_count']} valeurs")
        
        return columns_info
    
    def read_columns(self, column1, column2=None):
        if self.current_data is None:
            print("Aucun fichier chargé")
            return None
        
        try:
            if column2 is None:
                result = self.current_data[column1].tolist()
                print(f"Données extraites de la colonne '{column1}': {len(result)} valeurs")
                return {
                    'column': column1,
                    'data': result,
                    'count': len(result)
                }
            else:
                data1 = self.current_data[column1].tolist()
                data2 = self.current_data[column2].tolist()
                
                result = []
                for i in range(len(data1)):
                    row_data = {
                        column1: data1[i] if i < len(data1) else None,
                        column2: data2[i] if i < len(data2) else None
                    }
                    result.append(row_data)
                
                print(f"Données extraites des colonnes '{column1}' et '{column2}': {len(result)} lignes")
                return {
                    'columns': [column1, column2],
                    'data': result,
                    'count': len(result)
                }
                
        except KeyError as e:
            print(f"Colonne non trouvée: {e}")
            return None
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return None
    
    def read_columns_by_index(self, index1, index2=None):
        if self.current_data is None:
            print("Aucun fichier chargé")
            return None
        
        try:
            columns = list(self.current_data.columns)
            
            if index1 >= len(columns):
                print(f"Index {index1} hors limite (max: {len(columns)-1})")
                return None
            
            column1_name = columns[index1]
            
            if index2 is None:
                return self.read_columns(column1_name)
            else:
                if index2 >= len(columns):
                    print(f"Index {index2} hors limite (max: {len(columns)-1})")
                    return None
                
                column2_name = columns[index2]
                return self.read_columns(column1_name, column2_name)
                
        except Exception as e:
            print(f"Erreur lors de l'extraction par index: {e}")
            return None
    
    def preview_data(self, rows=5):
        if self.current_data is None:
            print("Aucun fichier chargé")
            return None
        
        print(f"Aperçu des {rows} premières lignes:")
        print(self.current_data.head(rows))
        return self.current_data.head(rows)
    
    def search_columns(self, keyword):
        if self.current_data is None:
            print("Aucun fichier chargé")
            return []
        
        matching_columns = []
        for col in self.current_data.columns:
            if keyword.lower() in col.lower():
                matching_columns.append(col)
        
        print(f"Colonnes contenant '{keyword}': {matching_columns}")
        return matching_columns
    
    def export_data(self, data, output_filename):
        if data is None:
            print("Aucune donnée à exporter")
            return False
        
        try:
            output_path = self.data_path / output_filename
            
            if 'columns' in data and len(data['columns']) == 2:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame({data['column']: data['data']})
            
            df.to_excel(output_path, index=False)
            print(f"Données exportées vers: {output_path}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'export: {e}")
            return False

def main():
    reader = ExcelReaderAgent()
    
    excel_files = reader.list_excel_files()
    
    if excel_files:
        if reader.load_excel_file():
            reader.get_columns_info()
            reader.preview_data()
            
            data = reader.read_columns_by_index(0, 1)
            if data:
                print(f"\nDonnées extraites: {data['count']} lignes")
                print("Exemple des 3 premières lignes:")
                for i, row in enumerate(data['data'][:3]):
                    print(f"  Ligne {i+1}: {row}")
    else:
        print("Aucun fichier Excel trouvé dans le répertoire")

if __name__ == "__main__":
    main()