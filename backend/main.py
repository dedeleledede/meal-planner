from __future__ import annotations

import os
import calendar
import datetime as dt
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .db import Base, engine, get_db
from . import models, schemas
from .auth import create_token, verify_token, get_password_ok

# Create tables (simple starter approach)
Base.metadata.create_all(bind=engine)

APP_NAME = "MealPlanner (28-day cycle)"
app = FastAPI(title=APP_NAME)

# --- CORS ---
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
origins = [o.strip() for o in origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer = HTTPBearer(auto_error=False)

def require_auth(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload

# ---------- Auth ----------
@app.post("/api/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn):
    if not get_password_ok(body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    return {"token": create_token({"sub": "editor"})}

@app.get("/api/me")
def me(user=Depends(require_auth)):
    return {"ok": True, "user": user}

# ---------- Ingredients ----------
@app.get("/api/ingredients", response_model=List[schemas.IngredientOut])
def list_ingredients(db: Session = Depends(get_db)):
    items = db.query(models.Ingredient).order_by(models.Ingredient.name.asc()).all()
    return items

@app.post("/api/ingredients", response_model=schemas.IngredientOut)
def create_ingredient(body: schemas.IngredientIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    existing = db.query(models.Ingredient).filter(models.Ingredient.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    ing = models.Ingredient(
        name=body.name.strip(),
        unit=body.unit.strip(),
        unit_price=body.unit_price,
        price_currency=body.price_currency
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing

@app.put("/api/ingredients/{ingredient_id}", response_model=schemas.IngredientOut)
def update_ingredient(ingredient_id: int, body: schemas.IngredientIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    ing = db.get(models.Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Not found")
    ing.name = body.name.strip()
    ing.unit = body.unit.strip()
    ing.unit_price = body.unit_price
    ing.price_currency = body.price_currency
    db.commit()
    db.refresh(ing)
    return ing

@app.delete("/api/ingredients/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    ing = db.get(models.Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Not found")

    # Remove references in dish_ingredients first (safe even if none)
    db.query(models.DishIngredient).filter(models.DishIngredient.ingredient_id == ingredient_id).delete(
        synchronize_session=False
    )

    db.delete(ing)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete ingredient because it is still referenced. Remove it from dishes/template first."
        )
    return {"ok": True}

# ---------- Dishes ----------
@app.get("/api/dishes", response_model=List[schemas.DishOut])
def list_dishes(db: Session = Depends(get_db)):
    items = db.query(models.Dish).order_by(models.Dish.name.asc()).all()
    return items

@app.post("/api/dishes", response_model=schemas.DishOut)
def create_dish(body: schemas.DishIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    existing = db.query(models.Dish).filter(models.Dish.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dish already exists")
    dish = models.Dish(name=body.name.strip(), notes=body.notes or "")
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish

@app.put("/api/dishes/{dish_id}", response_model=schemas.DishOut)
def update_dish(dish_id: int, body: schemas.DishIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Not found")
    dish.name = body.name.strip()
    dish.notes = body.notes or ""
    db.commit()
    db.refresh(dish)
    return dish

@app.delete("/api/dishes/{dish_id}")
def delete_dish(dish_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Not found")

    # Remove references to this dish in the 28-day cycle and in overrides (avoid FK errors)
    for Model in (models.CycleDay, models.DayOverride):
        db.query(Model).filter(Model.breakfast_dish_id == dish_id).update(
            {Model.breakfast_dish_id: None}, synchronize_session=False
        )
        db.query(Model).filter(Model.lunch_dish_id == dish_id).update(
            {Model.lunch_dish_id: None}, synchronize_session=False
        )
        db.query(Model).filter(Model.snack_dish_id == dish_id).update(
            {Model.snack_dish_id: None}, synchronize_session=False
        )
        db.query(Model).filter(Model.dinner_dish_id == dish_id).update(
            {Model.dinner_dish_id: None}, synchronize_session=False
        )

    # Remove dish_ingredients rows explicitly (works even if DB FK cascades are off)
    db.query(models.DishIngredient).filter(models.DishIngredient.dish_id == dish_id).delete(
        synchronize_session=False
    )

    db.delete(dish)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete dish because it is still referenced. Clear it from cycle/overrides first."
        )
    return {"ok": True}

# Dish ingredients
@app.get("/api/dishes/{dish_id}/ingredients", response_model=List[schemas.DishIngredientOut])
def get_dish_ingredients(dish_id: int, db: Session = Depends(get_db)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish.ingredients

@app.put("/api/dishes/{dish_id}/ingredients", response_model=List[schemas.DishIngredientOut])
def set_dish_ingredients(dish_id: int, body: schemas.DishIngredientsSetIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    # wipe
    for di in list(dish.ingredients):
        db.delete(di)
    db.flush()

    # insert
    for entry in body.items:
        ing = db.get(models.Ingredient, entry.ingredient_id)
        if not ing:
            raise HTTPException(status_code=400, detail=f"Ingredient id {entry.ingredient_id} not found")
        di = models.DishIngredient(
            dish_id=dish.id,
            ingredient_id=ing.id,
            amount=entry.amount,
            unit=entry.unit or ing.unit
        )
        db.add(di)

    db.commit()
    db.refresh(dish)
    return dish.ingredients

# ---------- 28-day meal cycle template ----------
@app.get("/api/cycle", response_model=List[schemas.CycleDayOut])
def get_cycle(db: Session = Depends(get_db)):
    ensure_cycle(db)
    return db.query(models.CycleDay).order_by(models.CycleDay.day_index.asc()).all()

@app.put("/api/cycle/{day_index}", response_model=schemas.CycleDayOut)
def set_cycle_day(day_index: int, body: schemas.CycleDayIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    if day_index < 1 or day_index > 28:
        raise HTTPException(status_code=400, detail="day_index must be 1..28")
    ensure_cycle(db)
    row = db.query(models.CycleDay).filter(models.CycleDay.day_index == day_index).first()
    row.breakfast_dish_id = body.breakfast_dish_id
    row.lunch_dish_id = body.lunch_dish_id
    row.snack_dish_id = body.snack_dish_id
    row.dinner_dish_id = body.dinner_dish_id
    db.commit()
    db.refresh(row)
    return row

# ---------- Date overrides (optional per date) ----------
@app.get("/api/overrides", response_model=List[schemas.DayOverrideOut])
def list_overrides(year: int, month: int, db: Session = Depends(get_db)):
    start = dt.date(year, month, 1)
    end = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)  # next month
    rows = db.query(models.DayOverride).filter(models.DayOverride.date >= start, models.DayOverride.date < end).all()
    return rows

@app.put("/api/override/{date_str}", response_model=schemas.DayOverrideOut)
def set_override(date_str: str, body: schemas.CycleDayIn, db: Session = Depends(get_db), _=Depends(require_auth)):
    try:
        date = dt.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    row = db.query(models.DayOverride).filter(models.DayOverride.date == date).first()
    if not row:
        row = models.DayOverride(date=date)
        db.add(row)
    row.breakfast_dish_id = body.breakfast_dish_id
    row.lunch_dish_id = body.lunch_dish_id
    row.snack_dish_id = body.snack_dish_id
    row.dinner_dish_id = body.dinner_dish_id
    db.commit()
    db.refresh(row)
    return row

@app.delete("/api/override/{date_str}")
def clear_override(date_str: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    try:
        date = dt.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    row = db.query(models.DayOverride).filter(models.DayOverride.date == date).first()
    if not row:
        return {"ok": True}
    db.delete(row)
    db.commit()
    return {"ok": True}

# ---------- Calendar view ----------
WEEKDAYS_PT = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]

@app.get("/api/calendar", response_model=schemas.CalendarOut)
def get_calendar(year: int, month: int, db: Session = Depends(get_db)):
    ensure_cycle(db)

    cal = calendar.Calendar(firstweekday=6)  # 6 = Sunday
    weeks = cal.monthdatescalendar(year, month)

    dishes = {d.id: d for d in db.query(models.Dish).all()}
    overrides = {o.date: o for o in db.query(models.DayOverride).all()}

    out_weeks: List[List[schemas.CalendarCellOut]] = []
    for wk in weeks:
        row: List[schemas.CalendarCellOut] = []
        for day in wk:
            if day.month != month:
                row.append(schemas.CalendarCellOut(date=day.isoformat(), in_month=False, meals=None))
                continue

            ovr = overrides.get(day)
            if ovr:
                meals = _meals_from_ids(ovr.breakfast_dish_id, ovr.lunch_dish_id, ovr.snack_dish_id, ovr.dinner_dish_id, dishes)
            else:
                idx = ((day.day - 1) % 28) + 1
                cyc = db.query(models.CycleDay).filter(models.CycleDay.day_index == idx).first()
                meals = _meals_from_ids(cyc.breakfast_dish_id, cyc.lunch_dish_id, cyc.snack_dish_id, cyc.dinner_dish_id, dishes)

            row.append(schemas.CalendarCellOut(date=day.isoformat(), in_month=True, meals=meals))
        out_weeks.append(row)

    return schemas.CalendarOut(
        year=year,
        month=month,
        weekdays=WEEKDAYS_PT,
        weeks=out_weeks,
        cycle_mode="28-day"
    )

def _meals_from_ids(b: Optional[int], l: Optional[int], s: Optional[int], d: Optional[int], dishes: Dict[int, models.Dish]) -> schemas.MealsOut:
    def name(did: Optional[int]) -> Optional[str]:
        if not did:
            return None
        dish = dishes.get(did)
        return dish.name if dish else None
    return schemas.MealsOut(
        breakfast={"dish_id": b, "dish_name": name(b)},
        lunch={"dish_id": l, "dish_name": name(l)},
        snack={"dish_id": s, "dish_name": name(s)},
        dinner={"dish_id": d, "dish_name": name(d)},
    )

def ensure_cycle(db: Session):
    count = db.query(models.CycleDay).count()
    if count >= 28:
        return
    # Create missing days with null meals
    existing = {c.day_index for c in db.query(models.CycleDay).all()}
    for i in range(1, 29):
        if i in existing:
            continue
        db.add(models.CycleDay(day_index=i))
    db.commit()

# ---------- Shopping list ----------
@app.get("/api/shopping", response_model=schemas.ShoppingOut)
def shopping(start: str, end: str, db: Session = Depends(get_db)):
    """
    Aggregate ingredient totals from planned meals between start and end inclusive.
    start/end: YYYY-MM-DD
    """
    try:
        start_d = dt.date.fromisoformat(start)
        end_d = dt.date.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="start/end must be YYYY-MM-DD")
    if end_d < start_d:
        raise HTTPException(status_code=400, detail="end must be >= start")

    ensure_cycle(db)

    # Load data
    dishes = {d.id: d for d in db.query(models.Dish).all()}
    overrides = {o.date: o for o in db.query(models.DayOverride).all()}
    cycle = {c.day_index: c for c in db.query(models.CycleDay).all()}
    ingredients = {i.id: i for i in db.query(models.Ingredient).all()}

    # Collect dish ids used
    used_dish_ids: List[int] = []
    day = start_d
    while day <= end_d:
        ovr = overrides.get(day)
        if ovr:
            ids = [ovr.breakfast_dish_id, ovr.lunch_dish_id, ovr.snack_dish_id, ovr.dinner_dish_id]
        else:
            idx = ((day.day - 1) % 28) + 1
            c = cycle[idx]
            ids = [c.breakfast_dish_id, c.lunch_dish_id, c.snack_dish_id, c.dinner_dish_id]
        used_dish_ids.extend([i for i in ids if i])
        day += dt.timedelta(days=1)

    # Aggregate ingredients
    totals: Dict[int, Dict[str, Any]] = {}
    for dish_id in used_dish_ids:
        dish = dishes.get(dish_id)
        if not dish:
            continue
        for di in dish.ingredients:
            ing = ingredients.get(di.ingredient_id)
            if not ing:
                continue
            # Normalize unit: keep di.unit
            key = (ing.id, di.unit)
            k = f"{ing.id}::{di.unit}"
            if k not in totals:
                totals[k] = {
                    "ingredient_id": ing.id,
                    "ingredient_name": ing.name,
                    "unit": di.unit,
                    "amount": 0.0,
                    "unit_price": ing.unit_price,
                    "price_currency": ing.price_currency,
                }
            totals[k]["amount"] += float(di.amount)

    items: List[schemas.ShoppingItemOut] = []
    grand_total = 0.0
    currency = None
    for v in sorted(totals.values(), key=lambda x: (x["ingredient_name"], x["unit"])):
        cost = None
        if v["unit_price"] is not None:
            cost = v["amount"] * float(v["unit_price"])
            grand_total += cost
            currency = currency or v["price_currency"]
        items.append(schemas.ShoppingItemOut(
            ingredient_id=v["ingredient_id"],
            ingredient_name=v["ingredient_name"],
            unit=v["unit"],
            amount=v["amount"],
            unit_price=v["unit_price"],
            price_currency=v["price_currency"],
            estimated_cost=cost
        ))

    return schemas.ShoppingOut(
        start=start_d.isoformat(),
        end=end_d.isoformat(),
        items=items,
        estimated_total=grand_total if items else 0.0,
        currency=currency
    )
