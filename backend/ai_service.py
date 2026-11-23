from sentence_transformers import SentenceTransformer
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import text
import io

# Modell betöltése (mivel már le van töltve, most már azonnal kész áll)
model = SentenceTransformer('clip-ViT-B-32')

def generate_image_embedding(image_bytes: bytes) -> list[float]:
    """Kép bájtokból 512 dimenziós AI vektort generál."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    embedding = model.encode(image)
    return embedding.tolist()

def search_similar_products(image_bytes: bytes, db: Session, limit: int = 5):
    """
    Legenerálja a feltöltött kép vektorát, majd a pgvector segítségével 
    megkeresi a top X leghasonlóbb terméket az adatbázisban.
    """
    # 1. Generálunk vektort a keresendő képből
    query_vector = generate_image_embedding(image_bytes)
    
    # 2. Átalakítjuk a vektort olyan szöveges formátummá, amit a PostgreSQL megért (pl: '[0.12, -0.43, ...]')
    vector_str = str(query_vector)
    
    # 3. Nyers SQL lekérdezést használunk a pgvector <=> (koszinusz távolság) operátorával.
    # A koszinusz távolság 0 és 2 között lehet. A 0 a tökéletes egyezés, a 2 a teljes ellentét.
    # Kiszámolunk egy Hasonlósági Pontszámot (Similarity Score) is: (1 - távolság) * 100
    query = text("""
        SELECT id, vendor_serial_number, name_hu, category, quantity, supplier,
               (1 - (image_embedding <=> :vector)) * 100 AS confidence_score
        FROM products
        WHERE image_embedding IS NOT NULL
        ORDER BY image_embedding <=> :vector
        LIMIT :limit
    """)
    
    # 4. Lefuttatjuk a keresést az adatbázisban
    result = db.execute(query, {"vector": vector_str, "limit": limit})
    
    # 5. Szépen formázott listává alakítjuk az eredményt
    hits = []
    for row in result:
        hits.append({
            "id": row.id,
            "vendor_serial_number": row.vendor_serial_number,
            "name_hu": row.name_hu,
            "category": row.category,
            "quantity": row.quantity,
            "supplier": row.supplier,
            "confidence_score": round(row.confidence_score, 2)  # Kerekítjük 2 tizedesjegyre
        })
        
    return hits