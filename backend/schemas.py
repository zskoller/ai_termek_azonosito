from pydantic import BaseModel, Field
from typing import Optional

# Ez a séma határozza meg, hogy egy Excel sor milyen adatokat KÖTELES tartalmazni
class ProductExcelImport(BaseModel):
    vendor_serial_number: str = Field(..., min_length=1)  # Nem lehet üres
    product_name: str = Field(..., min_length=1)         # Nem lehet üres
    category: Optional[str] = None                        # Opcionális szöveg
    quantity: int = Field(default=0, ge=0)                # Szám, és legalább 0 (ge = greater or equal)
    supplier: Optional[str] = None                        # Opcionális szöveg
    notes: Optional[str] = None                           # Opcionális szöveg