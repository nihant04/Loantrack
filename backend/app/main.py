from fastapi import FastAPI

app = FastAPI(title="LoanTrack API")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/loans")
def get_loans():
    return []


@app.post("/loans")
def create_loan():
    return {"message": "Loan endpoint is ready"}