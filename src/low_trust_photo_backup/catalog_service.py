"""
Module responsible for catalogging a directory
    - computing file hashes
    - updating an sqlite db
"""
from pathlib import Path
from datetime import datetime
from typing import List, Union
from low_trust_photo_backup.utils import walk_files_generator, compute_hash
from low_trust_photo_backup.db_helper import SQLiteDB


def update_directory_catalog(directory: Union[str, Path], db: SQLiteDB,
                             machine_name: str) -> None:
    """
    Compute hashes of all files under the given directory and update the
    directory catalog db.
    """
    for file in walk_files_generator(directory):
        hash = compute_hash(file)
        row_dict = {
            "hash": hash,
            "machine_name": machine_name,
            "filepath": file,
            "updated_date": str(datetime.now())
        }
        db.insert("files", row_dict) # TODO some kind of updating logic (delete all prexisting hashes before inserting?)
        # TODO inserting one row at a time not very efficient


def get_new_files_list(db: SQLiteDB, source_machine: str,
                       dest_machine: str) -> List[str]:
    """
    Uses the directory catalog to compare the contents of a source machine and
    target machine, returning a list of files only in source
    """
    # TODO files only in source (new hash, new path)
    query = """
    SELECT DISTINCT s.filepath
    FROM files s
    WHERE s.machine_name = ?
    AND s.hash NOT IN (
        SELECT DISTINCT d.hash 
        FROM files d 
        WHERE d.machine_name = ?
    )
    AND s.filepath NOT IN (
        SELECT DISTINCT d.filepath
        FROM files d
        WHERE d.machine_name = ?)
    """
    params = (source_machine, dest_machine, source_machine, dest_machine)
    return db.fetch_list_str(query, params) 


    # TODO moved file (existing hash, !=path)
    # TODO modified file (existing path, new hash)