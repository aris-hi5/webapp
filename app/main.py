import sys
import os
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.models import Consumable, IceCream, Topping
from database.database import initialize_tables, SessionLocal
from crud.ice_cream import (
    create_ice_cream,
    get_all_ice_creams,
)
from crud.topping import (
    create_topping,
    get_all_toppings,
)
from crud.consumable import (
    create_consumable,
    get_all_consumables,
)
from crud.order import (
    create_order,
    get_all_orders,
)
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 테이블 및 데이터베이스 설정
initialize_tables()

db = SessionLocal()


@app.get("/")
def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/item")
def get_add_item_page(request: Request, db: Session = Depends(get_db)):
    ice_creams = get_all_ice_creams(db)
    toppings = get_all_toppings(db)
    consumables = get_all_consumables(db)
    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "ice_creams": ice_creams,
            "toppings": toppings,
            "consumables": consumables,
        },
    )


@app.post("/item")
def create_new_item(
    request: Request,
    item_type: str = Form(...),
    item_name: str = Form(...),
    item_price: int = Form(...),
    item_quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    if item_type == "ice_cream":
        create_ice_cream(db, item_name, item_price, item_quantity)
    elif item_type == "topping":
        create_topping(db, item_name, item_price, item_quantity)
    elif item_type == "consumable":
        create_consumable(db, item_name, item_price, item_quantity)
    return get_add_item_page(request, db)


@app.delete("/item/{item_type}/{item_id}")
def delete_item(item_type: str, item_id: int, db: Session = Depends(get_db)):
    if item_type == "ice_cream":
        db.query(IceCream).filter(IceCream.id == item_id).delete()
    elif item_type == "topping":
        db.query(Topping).filter(Topping.id == item_id).delete()
    elif item_type == "consumable":
        db.query(Consumable).filter(Consumable.id == item_id).delete()
    db.commit()
    return {"success": True}


@app.get("/order")
def get_order_page(request: Request, db: Session = Depends(get_db)):
    ice_creams = get_all_ice_creams(db)
    toppings = get_all_toppings(db)
    consumables = get_all_consumables(db)
    consumables = [c for c in consumables if c.name != "컵"]
    return templates.TemplateResponse(
        "order.html",
        {
            "request": request,
            "ice_creams": ice_creams,
            "toppings": toppings,
            "consumables": consumables,
        },
    )


@app.post("/order")
def create_new_order(
    request: Request,
    ice_cream_id: int = Form(...),
    topping_ids: str = Form(None),
    consumable_ids: str = Form(None),
    db: Session = Depends(get_db),
):
    topping_ids_list = (
        [int(id) for id in topping_ids.split(",") if id] if topping_ids else []
    )
    consumable_ids_list = (
        [int(id) for id in consumable_ids.split(",") if id] if consumable_ids else []
    )
    create_order(db, ice_cream_id, topping_ids_list, consumable_ids_list)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/stock")
def read_inventory_page(request: Request, db: Session = Depends(get_db)):
    ice_creams = get_all_ice_creams(db)
    toppings = get_all_toppings(db)
    consumables = get_all_consumables(db)
    inventory_data = {
        "ice_cream": {ic.name: ic.quantity for ic in ice_creams},
        "topping": {tp.name: tp.quantity for tp in toppings},
        "consumable": {cs.name: cs.quantity for cs in consumables},
    }
    return templates.TemplateResponse(
        "stock.html", {"request": request, "inventory_data": inventory_data}
    )


@app.get("/history")
def read_order_history(request: Request, db: Session = Depends(get_db)):
    orders = get_all_orders(db)
    return templates.TemplateResponse(
        "history.html", {"request": request, "orders": orders}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")