import os
import time
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg_pool import ConnectionPool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LoanTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


def get_database_pool():
    global pool

    if pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL environment variable is not set")

        pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1,
            max_size=10,
            open=False,
        )

        pool.open()

    return pool


class LoanCreate(BaseModel):
    borrower_name: str
    amount: float
    status: str


@app.on_event("startup")
def startup():
    retries = 5

    for attempt in range(1, retries + 1):
        try:
            db_pool = get_database_pool()

            with db_pool.connection() as connection:
                connection.execute("SELECT 1")

            logger.info("Database connection established")
            return

        except Exception as exc:
            logger.warning(
                "Database connection attempt %s/%s failed: %s",
                attempt,
                retries,
                exc,
            )

            if attempt < retries:
                time.sleep(2)

    raise RuntimeError("Could not connect to PostgreSQL")


@app.on_event("shutdown")
def shutdown():
    global pool

    if pool is not None:
        pool.close()


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "pod": os.getenv("HOSTNAME", "unknown"),
    }


@app.get("/readyz")
def readyz():
    try:
        db_pool = get_database_pool()

        with db_pool.connection() as connection:
            connection.execute("SELECT 1")

        return {"status": "ready"}

    except Exception as exc:
        logger.error("Database readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/loans")
def get_loans():
    try:
        db_pool = get_database_pool()

        with db_pool.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, borrower_name, amount, status, created_at
                FROM loans
                ORDER BY id
                """
            ).fetchall()

        return [
            {
                "id": row[0],
                "borrower_name": row[1],
                "amount": float(row[2]),
                "status": row[3],
                "created_at": row[4].isoformat(),
            }
            for row in rows
        ]

    except Exception as exc:
        logger.error("Failed to fetch loans: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch loans")


@app.post("/loans")
def create_loan(loan: LoanCreate):
    if loan.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero",
        )

    if loan.status not in {"Pending", "Approved", "Rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid loan status",
        )

    try:
        db_pool = get_database_pool()

        with db_pool.connection() as connection:
            row = connection.execute(
                """
                INSERT INTO loans (borrower_name, amount, status)
                VALUES (%s, %s, %s)
                RETURNING id, borrower_name, amount, status, created_at
                """,
                (loan.borrower_name, loan.amount, loan.status),
            ).fetchone()

        return {
            "id": row[0],
            "borrower_name": row[1],
            "amount": float(row[2]),
            "status": row[3],
            "created_at": row[4].isoformat(),
        }

    except Exception as exc:
        logger.error("Failed to create loan: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create loan")