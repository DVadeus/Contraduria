from fastapi import FastAPI

app = FastAPI(title="Portal SECOP Bogotá", version="1.0")


@app.get("/")
def home():
    return {"status": "ok"}
