from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Nura Backend API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Nura Backend", "version": "1.0.0"}


@app.post("/chat/assistant")
async def chat_assistant(request: dict):
    message = request.get("message", "")
    return {
        "response": f"Hello! You said: {message}. This is a simple test response from the backend.",
        "status": "success",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
