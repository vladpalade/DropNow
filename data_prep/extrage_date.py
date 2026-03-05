import pandas as pd

# Curatare fisier 500k recenzii
try:
    df_gigant = pd.read_csv('Reviews.csv')
except FileNotFoundError:
    exit()

# Unim titlul cu textul
df_gigant['Summary'] = df_gigant['Summary'].fillna("")
df_gigant['Text'] = df_gigant['Text'].fillna("")
df_gigant['Text_Complet'] = df_gigant['Summary'] + " " + df_gigant['Text']

# Scoatem continutul irelevant
cuvinte_inutile = ['shipping', 'delivery', 'arrived', 'box', 'packaging', 'courier']
masca = ~df_gigant['Text_Complet'].str.lower().str.contains('|'.join(cuvinte_inutile))
df_curat = df_gigant[masca]

# Fortam 3000 de recenzii pe rating
df_extras = df_curat.groupby('Score').sample(n=3000, random_state=42)

# Ne asiguram ca avem exact coloanele pe care le cere data_prep.py
df_final = df_extras[['Score', 'Summary', 'Text']]

nume_fisier_nou = 'reviews_general_25k.csv'
df_final.to_csv(nume_fisier_nou, index=False)