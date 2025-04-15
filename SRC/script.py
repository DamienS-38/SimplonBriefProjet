# Imports
import os
import sqlite3
import pandas as pd


# Chargement des CSV
df_produits = pd.read_csv('DATA/produits.csv', delimiter=',')
df_magasins = pd.read_csv('DATA/magasins.csv', delimiter=',')
df_ventes = pd.read_csv('DATA/ventes.csv', delimiter=',')

#Vérification du chargement des CSV
print(df_produits.head())
print(df_magasins.head())
print(df_ventes.head())

#Récupération des csv en ligne
url_produits="https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=0&single=true&output=csv"
url_magasins = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=714623615&single=true&output=csv"
url_ventes   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSawI56WBC64foMT9pKCiY594fBZk9Lyj8_bxfgmq-8ck_jw1Z49qDeMatCWqBxehEVoM6U1zdYx73V/pub?gid=760830694&single=true&output=csv"



# Connexion à la base SQLite
db_path = os.path.join("DATA", "pme.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Activer les clés étrangères
cursor.execute('PRAGMA foreign_keys = ON;')

# Création des tables si elles n'existent pas
cursor.execute('''
CREATE TABLE IF NOT EXISTS Produit (
    id_produit TEXT PRIMARY KEY,
    nom TEXT,
    prix REAL,
    stock INT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Magasins (
    id_magasin TEXT PRIMARY KEY,
    ville TEXT,
    Nb_salarie INT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Ventes (
    id_vente INTEGER PRIMARY KEY AUTOINCREMENT,
    id_produit TEXT,
    id_magasin TEXT,
    date_vente TEXT,
    quantite INTEGER,
    FOREIGN KEY(id_produit) REFERENCES Produit(id_produit),
    FOREIGN KEY(id_magasin) REFERENCES Magasins(id_magasin)
    --,    UNIQUE(id_produit, id_magasin, date_vente)
)
''')





# Renommage des colonnes
df_produits = df_produits.rename(columns={
    'ID Référence produit': 'id_produit',
    'Nom': 'nom',
    'Prix': 'prix',
    'Stock': 'stock'
})
ordre_colonnes_produits = ['id_produit', 'nom', 'prix', 'stock']
df_produits = df_produits[ordre_colonnes_produits]

df_magasins = df_magasins.rename(columns={
    'ID Magasin': 'id_magasin',
    'Ville': 'ville',
    'Nombre de salariés': 'nb_salarie'
})

df_ventes = df_ventes.rename(columns={
    'ID Magasin': 'id_magasin',
    'ID Référence produit': 'id_produit',
    'Date': 'date_vente',
    'Quantité': 'quantite'
})
ordre_colonnes_ventes = ['id_produit', 'id_magasin', 'date_vente', 'quantite']
df_ventes = df_ventes[ordre_colonnes_ventes]

# Éviter les doublons sur Produits
id_produit_existant = pd.read_sql("SELECT id_produit FROM Produit", conn)['id_produit'].tolist()
df_produits = df_produits[~df_produits['id_produit'].isin(id_produit_existant)]

# Éviter les doublons sur Magasins
id_magasin_existant = pd.read_sql("SELECT id_magasin FROM Magasins", conn)['id_magasin'].tolist()
df_magasins = df_magasins[~df_magasins['id_magasin'].isin(id_magasin_existant)]

# Éviter les doublons sur Ventes (via clé composite)
print(df_ventes.dtypes)
df_ventes['vente_key'] = (
    df_ventes['id_produit'].astype(str) + "_" +
    df_ventes['id_magasin'].astype(str) + "_" +
    df_ventes['date_vente'].astype(str)
)
print(df_ventes.dtypes)
ventes_existantes = pd.read_sql("SELECT id_produit, id_magasin, date_vente FROM Ventes", conn)

ventes_existantes['vente_key'] = ventes_existantes['id_produit'] + "_" + ventes_existantes['id_magasin'] + "_" + ventes_existantes['date_vente']
df_ventes = df_ventes[~df_ventes['vente_key'].isin(ventes_existantes['vente_key'])]
df_ventes = df_ventes.drop(columns=['vente_key'])



# Insertion des données
print(df_produits.shape)
df_produits.to_sql('Produit', conn, if_exists='append', index=False)
print("Insertion des produits terminée.")

df_magasins.to_sql('Magasins', conn, if_exists='append', index=False)
print("Insertion des magasins terminée.")

df_ventes.to_sql('Ventes', conn, if_exists='append', index=False)
print("Insertion des ventes terminée.")

# Finalisation
conn.commit()
conn.close()
