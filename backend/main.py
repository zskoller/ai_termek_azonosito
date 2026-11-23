import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, Base, get_db
from typing import Optional  # Beimportálva az opcionális szűréshez
import excel_service
import ai_service
import translation_service
import webshop_service
from models import Product

# 1. Automatikusan bekapcsoljuk a pgvector kiegészítőt a PostgreSQL-ben az AI-hoz
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()

# 2. Ellenőrizzük és létrehozzuk az összes táblát az indítás pillanatában
Base.metadata.create_all(bind=engine)

# 3. FastAPI alkalmazás példányosítása
app = FastAPI(title="AI Termékazonosító Rendszer")

# 4. Biztosítjuk, hogy létezzen a fizikai mappa a feltöltött termékképeknek
os.makedirs("uploaded_images", exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "A rendszer backendje sikeresen elindult!"}


@app.post("/import-excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Csak Excel (.xlsx, .xls) fájlok megengedettek!")
    try:
        contents = await file.read()
        result = excel_service.process_excel_file(contents, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a feldolgozás során: {str(e)}")


@app.post("/upload-image/{product_id}")
async def upload_image(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Termék nem található az adatbázisban!")
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Csak képfájlok (.png, .jpg, .jpeg) engedettek!")
    try:
        contents = await file.read()
        file_path = f"uploaded_images/{product_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        embedding_vector = ai_service.generate_image_embedding(contents)
        product.image_embedding = embedding_vector
        db.commit()
        return {
            "message": "Kép sikeresen feltöltve, AI vektor legenerálva és elmentve!",
            "product_id": product_id,
            "image_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a kép feldolgozásakor: {str(e)}")


@app.post("/identify-product")
async def identify_product(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Csak képfájlok (.png, .jpg, .jpeg) engedélyezettek!")
    try:
        contents = await file.read()
        best_matches = ai_service.search_similar_products(contents, db, limit=5)
        
        threshold = 70.0
        auto_identified = False
        primary_match = None
        
        if best_matches and best_matches[0]["confidence_score"] >= threshold:
            auto_identified = True
            primary_match = best_matches[0]
            
        return {
            "auto_identified": auto_identified,
            "message": "Sikeres AI keresés." if auto_identified else "A találati pontosság alacsony. Internetes keresés (fallback) javasolt.",
            "best_match": primary_match,
            "all_candidates": best_matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba az azonosítás során: {str(e)}")


@app.post("/translate-product/{product_id}")
async def translate_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Termék nem található az adatbázisban!")
    if not product.name_hu:
        raise HTTPException(status_code=400, detail="A terméknek nincs magyar neve, amit lefordíthatnánk.")
        
    name_en, name_pl = translation_service.translate_product_names(product.name_hu)
    if not name_en or not name_pl:
        raise HTTPException(status_code=500, detail="A fordítás sikertelen volt.")
        
    product.name_en = name_en
    product.name_pl = name_pl
    db.commit()
    return {
        "message": "Sikeres fordítás!",
        "product_id": product.id,
        "name_hu": product.name_hu,
        "name_en": product.name_en,
        "name_pl": product.name_pl
    }


@app.get("/search-webshop/{product_id}")
async def find_webshop_link(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Termék nem található az adatbázisban!")
        search_name = product.name_hu
        if not search_name:
            raise HTTPException(status_code=400, detail="A terméknek nincs neve, amire kereshetnénk.")
            
        webshop_url = webshop_service.search_product_link(search_name)
        if not webshop_url:
            return {
                "message": "Sajnos nem találtunk releváns webshopot a termékhez.",
                "product_id": product.id,
                "product_name": search_name,
                "webshop_url": None
            }
        return {
            "message": "Webshop link sikeresen megtalálva!",
            "product_id": product.id,
            "product_name": search_name,
            "webshop_url": webshop_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Belső szerverhiba a webshop keresésnél: {str(e)}")


# === MÓDOSÍTVA: EXCEL EXPORTÁLÁS OPCIONÁLIS KERESÉSI PARAMÉTERREL ===
@app.get("/export-excel")
def export_excel(search: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Legenerálja és letölti az Excel fájlt. 
    Ha a 'search' paraméter ki van töltve, csak a szűrt találatokat menti el.
    """
    try:
        return excel_service.export_products_to_excel(db, search_query=search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba az exportálás során: {str(e)}")