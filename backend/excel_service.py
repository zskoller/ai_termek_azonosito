import io
import pandas as pd
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from models import Product

class ProductExcelImport(BaseModel):
    vendor_serial_number: str
    name_hu: str
    category: Optional[str] = None
    quantity: Optional[int] = 0
    supplier: Optional[str] = None
    notes: Optional[str] = None


def process_excel_file(contents: bytes, db: Session):
    df = pd.read_excel(io.BytesIO(contents))
    df.columns = [str(col).strip() for col in df.columns]
    
    mapping = {
        "Vendor Serial Number": "vendor_serial_number",
        "Product Name": "name_hu",
        "Category": "category",
        "Quantity": "quantity",
        "Supplier": "supplier",
        "Notes": "notes"
    }
    
    imported_count = 0
    errors = []
    
    for index, row in df.iterrows():
        row_num = index + 2
        try:
            row_data = {}
            for excel_col, schema_field in mapping.items():
                matched_col = next((c for c in df.columns if c.lower() == excel_col.lower()), None)
                if matched_col:
                    val = row[matched_col]
                    row_data[schema_field] = None if pd.isna(val) else val
            
            if not row_data.get('vendor_serial_number') and not row_data.get('name_hu'):
                continue
                
            if row_data.get('vendor_serial_number') is not None:
                val_str = str(row_data['vendor_serial_number'])
                if val_str.endswith('.0'):
                    val_str = val_str[:-2]
                row_data['vendor_serial_number'] = val_str
            
            if row_data.get('quantity') is None:
                row_data['quantity'] = 0
            else:
                try:
                    row_data['quantity'] = int(float(row_data['quantity']))
                except:
                    row_data['quantity'] = 0

            validated_row = ProductExcelImport(**row_data)
            
            db_product = Product(
                vendor_serial_number=validated_row.vendor_serial_number,
                name_hu=validated_row.name_hu,
                category=validated_row.category,
                quantity=validated_row.quantity,
                supplier=validated_row.supplier,
                notes=validated_row.notes
            )
            db.add(db_product)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Hiba a(z) {row_num}. sorban: {str(e)}")
    
    if imported_count > 0:
        db.commit()
        
    return {
        "imported_products": imported_count,
        "errors": errors
    }


# MODOSÍTVA: Bevezettük az opcionális search_query paramétert
def export_products_to_excel(db_session: Session, search_query: Optional[str] = None):
    """
    Kiolvassa a termékeket az adatbázisból (opcionálisan szűrve a keresőszóra), 
    és egy letölthető Excel fájlt generál belőle.
    """
    # Alap query felépítése
    query = db_session.query(Product)
    
    # Ha a felhasználó beírt egy keresőszót, rászűrünk a névre, cikkszámra vagy kategóriára
    if search_query and search_query.strip():
        search_filter = f"%{search_query.strip()}%"
        query = query.filter(
            (Product.name_hu.ilike(search_filter)) |
            (Product.vendor_serial_number.ilike(search_filter)) |
            (Product.category.ilike(search_filter))
        )
        
    # Csak a szűrt eredményeket kérjük le
    products = query.all()
    
    data = []
    for p in products:
        data.append({
            "ID": p.id,
            "Cikkszám (Vendor SN)": p.vendor_serial_number,
            "Név (HU)": p.name_hu,
            "Név (EN)": p.name_en,
            "Név (PL)": p.name_pl,
            "Kategória": p.category,
            "Mennyiség": p.quantity,
            "Beszállító": p.supplier,
            "Megjegyzés": p.notes,
            "AI Vektor betöltve?": "Igen" if p.image_embedding is not None else "Nem"
        })
        
    df = pd.DataFrame(data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Szűrt_Készlet")
        
    buffer.seek(0)
    
    return StreamingResponse(
        buffer, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=szurt_keszlet.xlsx"}
    )