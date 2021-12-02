from fastapi import FastAPI

fast_app = FastAPI()


@fast_app.get("/")
async def root():
    return {"message": "Hello World"}