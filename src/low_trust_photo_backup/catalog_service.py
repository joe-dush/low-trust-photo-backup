"""
Module responsible for catalogging a directory
    - computing file hashes
    - updating an sqlite db
"""
from pathlib import Path
from datetime import datetime
from typing import List, Union
from low_trust_photo_backup.utils import walk_files_generator, compute_file_hash
from low_trust_photo_backup.db_helper import SQLiteDB


def update_directory_catalog(directory: Union[str, Path], db: SQLiteDB,
                             machine_name: str) -> None:
    """
    Compute hashes of all files under the given directory and update the
    directory catalog db.
    """
    for file in walk_files_generator(directory):
        hash = compute_file_hash(file)
        row_dict = {
            "hash": hash,
            "machine_name": machine_name,
            "filepath": file,
            "updated_date": str(datetime.now())
        }
        db.insert("files", row_dict) # TODO some kind of updating logic (files could be renamed, or altered)


def get_files_to_transfer(source_machine: str, dest_machine: str) -> List[str]:
    # TODO files only in source (new hash, new path)
    # TODO moved file (existing hash, !=path)
    # TODO modified file (existing path, new hash)
    pass