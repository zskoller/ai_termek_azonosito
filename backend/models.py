from sqlalchemy import Column, Integer, String, Float, Text
from pgvector.sqlalchemy import Vector
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    vendor_serial_number = Column(String, index=True)
    name_hu = Column(String)
    name_en = Column(String)
    name_pl = Column(String)
    category = Column(String)
    quantity = Column(Integer, default=0)
    supplier = Column(String)
    notes = Column(Text)
    
    # AI embedding tárolása (512 dimenziós vektor az OpenCLIP-hez)
    image_embedding = Column(Vector(512))