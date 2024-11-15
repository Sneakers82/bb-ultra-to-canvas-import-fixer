import os
import time
import zipfile
import shutil
import argparse

from config_loader import TEMP_DIR, INPUT_DIR, OUTPUT_DIR
from lxml import etree
from ims_modifier import ImsManifest


def get_archives():
    available_files = os.listdir(INPUT_DIR)
    return available_files


def unzip_archive(archive_name):
    if os.path.exists(TEMP_DIR):
        clear_dir(TEMP_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    with zipfile.ZipFile(f"{INPUT_DIR}/{archive_name}", "r") as archive:
        archive.extractall(TEMP_DIR)


def zip_archive(archive_name):
    archive_path = os.path.join(OUTPUT_DIR, "PATCHED_" + archive_name)
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), TEMP_DIR))


def make_pretty():
    get_files = os.listdir(TEMP_DIR)
    for xml_file in get_files:
        if xml_file.lower().endswith(('.dat', '.xml')):
            file_path = os.path.join(TEMP_DIR, xml_file)
            try:
                xml_data = etree.parse(file_path)
                xml_data.write(file_path, pretty_print=True, encoding='UTF-8', xml_declaration=True)
            except etree.XMLSyntaxError:
                pass


def clear_dir(path):
    shutil.rmtree(path, ignore_errors=True)


def main(pretty=False, lti_placeholder=False):

    # Get a list of all `.zip` files to process, count the number of archives and notify the user
    archives = [file for file in get_archives() if file.lower().endswith('.zip')]
    total_archives = len(archives)
    print(f"Processing {total_archives} Archives...")
    start_time = time.time()

    # Iterate over the list of archives with an index for progress tracking
    for index, file in enumerate(archives):

        # Unpack and inspect the archive
        unzip_archive(file)
        ims = ImsManifest()

        # Check if the archive contains Blackboard Ultra content
        if ims.is_ultra():

            if lti_placeholder:
                documents = ims.get_documents()
                ims.add_lti_placeholder(documents)

            # Retrieve and fix assignments in the manifest
            assignments = ims.get_assignment_resources()
            ims.fix_assignments(assignments)
            ims.write_imsmanifest()

            if pretty:
                make_pretty()

        # Repack the archive and clear the temporary directory
        zip_archive(file)
        clear_dir(TEMP_DIR)

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
