from fastapi import APIRouter, Depends

from .. import crud
from ..dependencies import get_db
from ..schemas import Category, Menu, MenuIn, MenuPatch

router = APIRouter(prefix="/api/menus", tags=["menus"])


@router.get("", response_model=list[Menu])
def list_menus(category: Category | None = None, db=Depends(get_db)):
    return crud.list_menus(db, category)


@router.post("", response_model=Menu, status_code=201)
def create_menu(body: MenuIn, db=Depends(get_db)):
    return crud.create_menu(db, body.name, body.price, body.category)


@router.get("/{menu_id}", response_model=Menu)
def get_menu(menu_id: int, db=Depends(get_db)):
    return crud.get_menu(db, menu_id)


@router.patch("/{menu_id}", response_model=Menu)
def update_menu(menu_id: int, body: MenuPatch, db=Depends(get_db)):
    return crud.update_menu(db, menu_id, body.model_dump())


@router.delete("/{menu_id}", response_model=Menu)
def delete_menu(menu_id: int, db=Depends(get_db)):
    return crud.delete_menu(db, menu_id)
