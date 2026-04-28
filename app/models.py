from sqlalchemy import Column, String, Integer, Float, DateTime
from datetime import datetime
from .database import Base

class Item(Base):
    __tablename__ = "items"

    item_code = Column(String, primary_key=True, index=True)
    item_name = Column(String)
    arabic_name = Column(String)
    price = Column(Float)
    vat = Column(String)

class Barcode(Base):
    __tablename__ = "barcodes"

    barcode = Column(String, primary_key=True, index=True)
    item_code = Column(String)

class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    branch = Column(String)
    item_code = Column(String)
    stock_qty = Column(Integer)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    branch = Column(String)
    barcode = Column(String)
    item_code = Column(String)
    system_stock = Column(Integer)
    counted_qty = Column(Integer)
    difference = Column(Integer)
    user_name = Column(String)
    counted_at = Column(DateTime, default=datetime.utcnow)