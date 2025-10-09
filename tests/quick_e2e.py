import os
from pathlib import Path
from low_trust_photo_backup.client.tracking import detect_directory_changes
from low_trust_photo_backup.client.preparation import (
    group_files_by_size,
    zip_file_groups,
)

# fake config
# TEST_PATH_STR = "C:\\Users\\joeun\\02_Photos\\iPhone12 Monthly"
TEST_PATH_STR = "/mnt/c/Users/joeun/02_Photos/iPhone12 Monthly"
# TEST_PATH_STR = os.path.join("tests", "test_dir")
ZIP_STAGING_DIR = os.path.join("tests", "zip_staging")
CLIENT_NAME = "alfonsus"


# fake main
c_u_files = detect_directory_changes(Path(TEST_PATH_STR))
# print(c_u_files)

groups = group_files_by_size(Path(TEST_PATH_STR), c_u_files, max_size_gb=2)
for group in groups:
    print(f"{len(group)=}")

zip_file_names = zip_file_groups(
    groups, output_dir=Path(ZIP_STAGING_DIR), base_name=CLIENT_NAME
)
