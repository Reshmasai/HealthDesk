from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()


class HealthQuery(BaseModel):
    name: str
    symptoms: str
    severity: str

@app.get('/')
def root():
    return {"message: HealthDest API running"}

@app.post('/query')
def HandleQuery(query: HealthQuery):
    return {
        "message": "query received",
        "data": query
    }


