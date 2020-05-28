from econuy.app import db
from econuy.app.tasks import clear_tables


if __name__ == "__main__":
    clear_tables(db.engine)
