from __future__ import annotations

import datetime as dt
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, UniqueConstraint, Text
from sqlalchemy.orm import relationship

from .db import Base

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    unit = Column(String(40), nullable=False, default="unit")
    unit_price = Column(Float, nullable=True)
    price_currency = Column(String(8), nullable=False, default="BRL")

class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), unique=True, nullable=False)
    notes = Column(Text, nullable=False, default="")
    ingredients = relationship("DishIngredient", back_populates="dish", cascade="all, delete-orphan")

class DishIngredient(Base):
    __tablename__ = "dish_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False, default=0.0)
    unit = Column(String(40), nullable=False, default="unit")

    dish = relationship("Dish", back_populates="ingredients")
    ingredient = relationship("Ingredient")

    __table_args__ = (
        UniqueConstraint("dish_id", "ingredient_id", "unit", name="uq_dish_ing_unit"),
    )

class CycleDay(Base):
    __tablename__ = "cycle_days"
    id = Column(Integer, primary_key=True, index=True)
    day_index = Column(Integer, unique=True, nullable=False)  # 1..28
    breakfast_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    lunch_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    snack_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    dinner_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)

class DayOverride(Base):
    __tablename__ = "day_overrides"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    breakfast_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    lunch_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    snack_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    dinner_dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
