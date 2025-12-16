from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- Auth ---
class LoginIn(BaseModel):
    password: str = Field(min_length=1)

class TokenOut(BaseModel):
    token: str

# --- Ingredient ---
class IngredientIn(BaseModel):
    name: str
    unit: str = "unit"
    unit_price: Optional[float] = None
    price_currency: str = "BRL"

class IngredientOut(IngredientIn):
    id: int
    class Config:
        from_attributes = True

# --- Dish ---
class DishIn(BaseModel):
    name: str
    notes: Optional[str] = ""

class DishOut(DishIn):
    id: int
    class Config:
        from_attributes = True

# --- DishIngredient ---
class DishIngredientSetItemIn(BaseModel):
    ingredient_id: int
    amount: float
    unit: Optional[str] = None

class DishIngredientsSetIn(BaseModel):
    items: List[DishIngredientSetItemIn] = []

class DishIngredientOut(BaseModel):
    id: int
    dish_id: int
    ingredient_id: int
    amount: float
    unit: str
    ingredient: IngredientOut

    class Config:
        from_attributes = True

# --- Cycle / Overrides ---
class DayOverrideOut(BaseModel):
    id: int
    date: str
    breakfast_dish_id: Optional[int] = None
    lunch_dish_id: Optional[int] = None
    snack_dish_id: Optional[int] = None
    dinner_dish_id: Optional[int] = None

    class Config:
        from_attributes = True

class CycleDayIn(BaseModel):
    breakfast_dish_id: Optional[int] = None
    lunch_dish_id: Optional[int] = None
    snack_dish_id: Optional[int] = None
    dinner_dish_id: Optional[int] = None

class CycleDayOut(CycleDayIn):
    id: int
    day_index: int
    class Config:
        from_attributes = True

# --- Calendar ---
class MealSlotOut(BaseModel):
    dish_id: Optional[int] = None
    dish_name: Optional[str] = None

class MealsOut(BaseModel):
    breakfast: MealSlotOut
    lunch: MealSlotOut
    snack: MealSlotOut
    dinner: MealSlotOut

class CalendarCellOut(BaseModel):
    date: str
    in_month: bool
    meals: Optional[MealsOut] = None

class CalendarOut(BaseModel):
    year: int
    month: int
    weekdays: List[str]
    weeks: List[List[CalendarCellOut]]
    cycle_mode: str

# --- Shopping ---
class ShoppingItemOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    unit: str
    amount: float
    unit_price: Optional[float] = None
    price_currency: str = "BRL"
    estimated_cost: Optional[float] = None

class ShoppingOut(BaseModel):
    start: str
    end: str
    items: List[ShoppingItemOut]
    estimated_total: float
    currency: Optional[str] = None
