from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello! Server is working!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/test")
def test():
    return {"status": "ok", "message": "Routes are working!"}