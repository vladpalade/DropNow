import pandas as pd
import os

fisiere_csv = [
    'Electronics.csv', 
    'Clothing.csv', 
    'reviews_general_25k.csv'
]

date_combinate = []

for fisier in fisiere_csv:
    if os.path.exists(fisier):
        df = pd.read_csv(fisier, low_memory=False) 
        
        # Aducem toate coloanele la acelasi nume
        df = df.rename(columns={
            'reviews.rating': 'Score', 'rating': 'Score', 'stars': 'Score', 'Rating': 'Score',
            'reviews.title': 'Summary', 'title': 'Summary', 'Title': 'Summary',
            'reviews.text': 'Text', 'reviewText': 'Text', 'Review Text': 'Text'
        })
        
        if 'Score' in df.columns and 'Text' in df.columns:
            if 'Summary' not in df.columns:
                df['Summary'] = ""
                
            df_curat = df[['Score', 'Summary', 'Text']].copy()
            date_combinate.append(df_curat)
            print(f"    [OK] Am extras {len(df_curat)} recenzii valide.")
        else:
            print(f"    [EROARE] Fișierul {fisier} nu are coloanele corecte!")
    else:
        print(f" ⚠️ ATENȚIE: Nu am găsit {fisier}.")


dataset_complet = pd.concat(date_combinate, ignore_index=True)

dataset_complet['Summary'] = dataset_complet['Summary'].fillna("")
dataset_complet['Text'] = dataset_complet['Text'].fillna("")
dataset_complet['Text_Complet'] = dataset_complet['Summary'].astype(str) + " " + dataset_complet['Text'].astype(str)

# Fortam notele sa fie numere intregi de la 1 la 5
dataset_complet['Score'] = pd.to_numeric(dataset_complet['Score'], errors='coerce')
dataset_complet = dataset_complet.dropna(subset=['Score'])
dataset_complet['Score'] = dataset_complet['Score'].astype(int)
dataset_complet = dataset_complet[dataset_complet['Score'].isin([1, 2, 3, 4, 5])]

# Filtram recenziile irelevante
cuvinte_inutile = ['shipping', 'delivery', 'arrived', 'box', 'packaging', 'courier']
masca = ~dataset_complet['Text_Complet'].str.lower().str.contains('|'.join(cuvinte_inutile))
dataset_final = dataset_complet[masca]

# Printam distributia finala
print(dataset_final['Score'].value_counts().sort_index())

dataset_final[['Score', 'Text_Complet']].to_csv('date_perfecte.csv', index=False)
