from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models.category import Category
from db import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

@router.get("/")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/")
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    category = Category(**data.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/{category_id}")
def update_category(category_id: int, data: CategoryCreate, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in data.dict().items():
        setattr(category, key, value)
    db.commit()
    return category

@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"detail": "Category deleted"}