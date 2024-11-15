import os

from lxml import etree
from config_loader import TEMP_DIR


def read_dat_file(dat_file):
    dat_file_path = os.path.join(TEMP_DIR, f"{dat_file}")
    dat_file_data = etree.parse(dat_file_path)

    return dat_file_data


def save_dat_file(dat_file, dat_file_data):
    dat_file_path = os.path.join(TEMP_DIR, f"{dat_file}")

    with open(dat_file_path, "wb") as file:
        dat_file_data.write(file, encoding='UTF-8', xml_declaration=True)


def delete_dat_file(dat_files):
    for file in dat_files:
        file_to_delete = os.path.join(TEMP_DIR, file)
        os.remove(file_to_delete)
