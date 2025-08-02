from fastapi import FastAPI

app = FastAPI(title="CRM Bot API")

@app.get("/")
async def root():
    return {"message": "Welcome to CRM Bot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/bots")
async def get_bots():
    return {"message": "List of connected bots"}

@app.get("/users")
async def get_users():
    return {"message": "List of users"}

@app.get("/subscriptions")
async def get_subscriptions():
    return {"message": "Manage subscriptions (placeholder for payment management)"}
