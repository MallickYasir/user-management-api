from sqlmodel import SQLModel, create_engine, Session

# 1. Database URL (Using SQLite for simplicity)
sqlite_url = "sqlite:///database.db"

# 2. Create the engine
engine = create_engine(sqlite_url)

# 3. Function to create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 4. Function to get database session
def get_session():
    with Session(engine) as session:
        yield session