import os
import time
import shutil
import argparse
from config_loader import INPUT_DIR, OUTPUT_DIR
from ims_modifier import ImsManifest


def get_archives():
    available_files = os.listdir(INPUT_DIR)
    return available_files


def main(pretty=False, lti_placeholder=False):
    # Get a list of all `.zip` files to process, count the number of archives and notify the user
    archives = [file for file in get_archives() if file.lower().endswith('.zip')]
    total_archives = len(archives)
    print(f"Processing {total_archives} Archives...")
    start_time = time.time()

    # Iterate over the list of archives with an index for progress tracking
    for index, file in enumerate(archives):

        # Unpack and inspect the archive
        # unzip_archive(file)
        ims = ImsManifest(file)

        # Check if the archive contains Blackboard Ultra content
        if ims.is_ultra():

            # Retrieve and fix assignments in the manifest
            assignments = ims.get_assignment_resources()
            ims.fix_assignments(assignments)

            # Retrieve and fix discussions in the manifest
            discussions = ims.get_discussion_resources()
            ims.fix_discussions(discussions)

            # Remove unused categories from the gradebook
            ims.fix_gradebook()

            if lti_placeholder:
                documents = ims.get_documents()
                ims.add_lti_placeholder(documents)

            if pretty:
                ims.write_changes(pretty_print=True)
            else:
                ims.write_changes()
        else:
            shutil.copy(f"{INPUT_DIR}/{file}", f"{OUTPUT_DIR}/PATCHED_{file}")

        # Provide feedback every 10 files or when processing the last archive
        if index % 10 == 0 or index == len(archives) - 1:
            print(f"Processed {index + 1}/{len(archives)} archives so far...")

    # Calculate and print the total processing time
    print(f"{total_archives} Archives Processed in {int(time.time() - start_time)} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process IMS archive files")
    parser.add_argument("-p", "--pretty", action="store_true", help="Make XML output human readable")
    parser.add_argument("-l", "--lti", action="store_true", help="Add Placeholder for LTIs")

    args = parser.parse_args()
    main(pretty=args.pretty, lti_placeholder=args.lti)
