import os


os.environ.setdefault(
    "DATABASE_URL", "postgresql://expense:expense@localhost:5432/expense"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AUTH_JWKS_URL", "http://localhost:4000/api/auth/jwks")
os.environ.setdefault("AUTH_JWT_ISSUER", "http://localhost:4000")
os.environ.setdefault("AUTH_JWT_AUDIENCE", "expense-api")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_REGION", "auto")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin")
os.environ.setdefault("RECEIPTS_BUCKET", "receipts")
