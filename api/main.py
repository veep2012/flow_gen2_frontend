from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Flow Backend", version="0.1.0")


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Flow backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/items/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict[str, object]:
    return {"item_id": item_id, "query": q}


@app.post("/api/v1/items")
def create_item(item: Item) -> dict[str, object]:
    return {"id": 1, "item": item}

