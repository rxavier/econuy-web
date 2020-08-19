from econuy_web import db, create_app
from econuy_web.tasks import clear_tables


if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    clear_tables(db.get_engine(bind="queries"))
