from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import web_scraper
import ai_analyzer
import uvicorn
import sqlite3
import json
import os

app = FastAPI(title="TrustFactor Dropshipping AI", version="1.0")

# CORS permite frontend-ului (JS) sa comunice cu backendul fara erori de securitate in browser
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# SQLite: Relational Database
# Cream o schema de baza de date cu doua tabele: utilizatori si istoricul calcularilor financiare.
def init_db():
    with sqlite3.connect("trustfactor.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS istoric (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT, url TEXT, titlu TEXT, cantitate INTEGER,
                scor_calitate REAL, scor_final REAL, 
                pret_ali_bucata REAL, pret_emag_bucata REAL, profit_pachet REAL, 
                verdict TEXT, top_recenzii TEXT, link_competitor TEXT
            )
        """)
init_db()

#Pydantic: Data Validation
# Ne asigura ca request-urile HTTP primite de la frontend au formatul strict asteptat (string-uri).
class CerereProdus(BaseModel): 
    url: str
    username: str

class CerereAuth(BaseModel): 
    username: str
    password: str

@app.get("/")
def citeste_interfata():
    if os.path.exists("index.html"): 
        return FileResponse("index.html")
    return {"eroare": "Fisierul index.html lipseste din folder."}

@app.post("/login")
def login(date: CerereAuth):
    # Cauta in tabela de utilizatori o intrare cu datele respective
    with sqlite3.connect("trustfactor.db") as conn:
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (date.username, date.password)).fetchone()
        if user: 
            return {"mesaj": "Autentificare reusita!"}
        return {"eroare": "Nume de utilizator sau parola incorecte!"}

@app.post("/signup")
def creare_cont(date: CerereAuth):
    # Creaza o linie noua in baza de date
    try:
        with sqlite3.connect("trustfactor.db") as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (date.username, date.password))
        return {"mesaj": "Cont creat cu succes!"}
    except sqlite3.IntegrityError: 
        return {"eroare": "Acest nume de utilizator exista deja!"}

@app.post("/analizeaza-produs")
def analizeaza_produs(date: CerereProdus):
    rez = web_scraper.extrage_recenzii(date.url)
    
    lista_recenzii = rez.get("recenzii", [])
    if not lista_recenzii:
        scor_calitate = 2.5 
        top_3 = ["Nu s-au putut extrage recenzii text pentru acest produs."]
    else:
        # Folosim modelul ML ca sa analizam calitatea produsului
        scor_calitate, top_3 = ai_analyzer.analizeaza_recenzii(lista_recenzii)
    
    cantitate = max(1, rez["cantitate"])
    pret_ali_pachet = rez["pret_ali"]
    pret_emag_pachet = rez["pret_emag"]
    
    pret_ali_bucata = pret_ali_pachet / cantitate
    pret_emag_bucata = pret_emag_pachet / cantitate
    profit_pachet = pret_emag_pachet - pret_ali_pachet
    
    marja_profit = 0
    if pret_emag_pachet > 0:
        marja_profit = (profit_pachet / pret_emag_pachet) * 100

    puncte_calitate = scor_calitate # maxim 5 puncte de la AI
    puncte_profit = min(5.0, max(0.0, marja_profit / 10)) # maxim 5 puncte din profit
    scor_final_10 = round(puncte_calitate + puncte_profit, 1)

    if scor_final_10 >= 8.0:
        verdict = "Recomandat"
    elif scor_final_10 >= 6.0:
        verdict = "Acceptabil"
    else: 
        verdict = "Riscant"
    
    # Salvam produsul in baza de date
    with sqlite3.connect("trustfactor.db") as conn:
        conn.execute("""
            INSERT INTO istoric (username, url, titlu, cantitate, scor_calitate, scor_final, pret_ali_bucata, pret_emag_bucata, profit_pachet, verdict, top_recenzii, link_competitor) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date.username, date.url, rez["titlu"], cantitate, scor_calitate, scor_final_10, pret_ali_bucata, pret_emag_bucata, profit_pachet, verdict, json.dumps(top_3), rez["link_emag"]))
    
    return {
        "mesaj": "Analiză completă!",
        "titlu": rez["titlu"],
        "cantitate": cantitate,
        "pret_ali_bucata": pret_ali_bucata,
        "pret_emag_bucata": pret_emag_bucata,
        "profit_pachet": profit_pachet,
        "scor_calitate": scor_calitate,
        "scor_final": scor_final_10,
        "verdict": verdict,
        "top_recenzii": top_3,
        "link_emag": rez.get("link_emag", "")
    }

@app.get("/istoric/{username}")
def get_istoric(username: str):
    with sqlite3.connect("trustfactor.db") as conn:
        cursor = conn.execute("SELECT id, url, titlu, cantitate, scor_calitate, scor_final, pret_ali_bucata, pret_emag_bucata, profit_pachet, verdict, top_recenzii, link_competitor FROM istoric WHERE username=? ORDER BY id DESC", (username,))
        randuri = cursor.fetchall()
        
    istoric = []
    for r in randuri:
        istoric.append({
            "id": r[0], "url": r[1], "titlu": r[2], "cantitate": r[3], "scor_calitate": r[4], "scor_final": r[5], 
            "ali_buc": r[6], "emag_buc": r[7], "profit_pachet": r[8], "verdict": r[9], "top_recenzii": json.loads(r[10]), "link_competitor": r[11]
        })
    return istoric

# scoate intrarea itemului selectat
@app.delete("/sterge-istoric/{item_id}")
def sterge_istoric(item_id: int):
    with sqlite3.connect("trustfactor.db") as conn: 
        conn.execute("DELETE FROM istoric WHERE id=?", (item_id,))
    return {"mesaj": "Produs sters din istoric!"}

if __name__ == "__main__":
    print("🚀 Backend TrustFactor Pornit: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)