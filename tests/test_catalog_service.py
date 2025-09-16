import os
from pathlib import Path
from low_trust_photo_backup.catalog_service import update_directory_catalog
from low_trust_photo_backup.db_helper import SQLiteDB

def test_update_directory_catalog():
    db_path = os.path.join("tests","demo.db")
    Path(db_path).unlink(missing_ok=True)
    db = SQLiteDB(db_path)

    files_stmt = """
        hash TEXT PRIMARY KEY,
        machine_name TEXT NOT NULL,
        filepath TEXT NOT NULL,
        updated_date TEXT 
        """
    db.create_table("files", schema=files_stmt)


    # dirs_stmt = """
    #     machine_name TEXT NOT NULL,
    #     directory_path TEXT NOT NULL,
    #     last_catalogged TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #     """
    # db.create_table("dirs", schema=files_stmt)

    update_directory_catalog("src", db, "Alfonsus")
    