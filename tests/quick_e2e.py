import os
from pathlib import Path
from low_trust_photo_backup.client.tracking import detect_created_and_modified_files
from low_trust_photo_backup.client.preparation import group_files_by_size

TEST_PATH_STR = "C:\\Users\\joeun\\02_Photos\\iPhone12 Monthly"
# TEST_PATH_STR = os.path.join("tests", "test_dir")


c_u_files = detect_created_and_modified_files(Path(TEST_PATH_STR))
# print(c_u_files)

groups = group_files_by_size(c_u_files, max_size_gb=2)
for group in groups:
    print(f"{len(group)=}")