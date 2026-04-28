from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from .database import Base, engine, get_db
from . import models

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/admin/import")
def import_data(master_file: UploadFile = File(...), stock_file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        master_df = pd.read_excel(BytesIO(master_file.file.read()))
        stock_df = pd.read_excel(BytesIO(stock_file.file.read()))

        seen_items = set()
        seen_barcodes = set()

        for _, row in master_df.iterrows():
            item_code = str(row.get("Itm_Cd")).strip()
            barcode = str(row.get("BarCode")).strip()

            if not item_code or item_code.lower() == "nan":
                continue

            price = row.get("Price")
            vat = row.get("VAT")

            if item_code not in seen_items:
                item = db.query(models.Item).filter_by(item_code=item_code).first()

                if item:
                    if not pd.isna(price):
                        item.price = price
                    if not pd.isna(vat):
                        item.vat = vat
                else:
                    db.add(models.Item(
                        item_code=item_code,
                        item_name=row.get("Desc"),
                        arabic_name=row.get("Itm_ArabicName"),
                        price=0 if pd.isna(price) else price,
                        vat="" if pd.isna(vat) else vat
                    ))

                seen_items.add(item_code)

            if barcode and barcode.lower() != "nan":
                if barcode in seen_barcodes:
                    continue

                seen_barcodes.add(barcode)

                exists = db.query(models.Barcode).filter_by(barcode=barcode).first()

                if not exists:
                    db.add(models.Barcode(
                        barcode=barcode,
                        item_code=item_code
                    ))

        db.commit()

        db.query(models.Stock).delete()
        db.commit()

        branches = [c for c in stock_df.columns if str(c).startswith("P")]

        for _, row in stock_df.iterrows():
            item_code = str(row.get("Itm_Cd")).strip()

            if not item_code:
                continue

            for branch in branches:
                qty = row.get(branch)

                if pd.isna(qty):
                    continue

                db.add(models.Stock(
                    branch=branch,
                    item_code=item_code,
                    stock_qty=int(qty)
                ))

        db.commit()

        return {"status": "success"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scan/{branch}/{code}")
def scan(branch: str, code: str, db: Session = Depends(get_db)):

    barcode = db.query(models.Barcode).filter_by(barcode=code).first()

    if not barcode:
        for b in db.query(models.Barcode).all():
            if b.barcode and b.barcode in code:
                barcode = b
                break

    if not barcode:
        return {"found": False}

    item = db.query(models.Item).filter_by(item_code=barcode.item_code).first()

    stock = db.query(models.Stock).filter_by(
        item_code=barcode.item_code,
        branch=branch
    ).first()

    return {
        "found": True,
        "item_name": item.item_name,
        "price": item.price,
        "stock": stock.stock_qty if stock else 0
    }