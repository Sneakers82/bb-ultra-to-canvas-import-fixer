import os
from lxml import etree
from config_loader import TEMP_DIR, IMSMANIFEST
from dat_file import read_dat_file, save_dat_file, delete_dat_file


class ImsManifest:
    """Class to manage and modify the imsmanifest.xml file in a Blackboard course export."""
    def __init__(self):
        """Initialize the ImsManifest by loading and parsing the imsmanifest.xml file."""
        self.file_path = os.path.join(TEMP_DIR, IMSMANIFEST)
        self.manifest = etree.parse(self.file_path)
        self.manifest_root = self.manifest.getroot()
        self.ns_map = {'bb': 'http://www.blackboard.com/content-packaging/'}

    def self_test(self):
        """Check if the manifest root element is present.

                Returns:
                    bool: True if the manifest root has elements, otherwise False.
                """
        return bool(len(self.manifest_root))

    def is_ultra(self):
        """Determine if the course is a Blackboard Ultra course by checking for ROOT element.

                Returns:
                    bool: True if the course type is Ultra, otherwise False.
                """
        return bool(self.manifest_root.xpath(".//item/title[text()='ROOT']", namespaces=self.ns_map))

    def get_assignment_resources(self):
        """Retrieve assignment resource files listed in the manifest.

                Returns:
                    list: A list of paths to assignment data files within the manifest.
                """
        assignments = self.manifest_root.xpath(f".//resource[starts-with(@bb:title, 'New Assignment') "
                                               f"and @type='resource/x-bb-link']", namespaces=self.ns_map)

        dat_files = [assignment.get('{http://www.blackboard.com/content-packaging/}file') for assignment in assignments
                     if assignment.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def get_documents(self):
        """Retrieve document resource files listed in the manifest.

        Returns:
            list: A list of paths to document data files within the manifest.
        """
        documents = self.manifest_root.xpath(f".//resource[@type='resource/x-bb-document']", namespaces=self.ns_map)

        dat_files = [document.get('{http://www.blackboard.com/content-packaging/}file') for document in documents
                     if document.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def add_lti_placeholder(self, dat_files):
        """Add placeholders for LTI resources in data files to indicate non-transferable content.

                Args:
                    dat_files (list): List of data file paths to modify for LTI placeholders.
                """
        for file in dat_files:
            dat_file_data = read_dat_file(file)
            dat_file_root = dat_file_data.getroot()

            title = dat_file_root.xpath(".//TITLE")[0]
            content_handler = dat_file_root.xpath("//CONTENTHANDLER")[0]

            if content_handler.values()[0].startswith("resource/x-bb-blti"):
                content_handler.set("value", "resource/x-bb-externallink")
                current_title = title.values()[0]
                placeholder = "[LTI Content: Replace] "
                title.set("value", placeholder + current_title)
                save_dat_file(file, dat_file_data)

    def fix_assignments(self, dat_files):
        """Convert Blackboard assignments to Canvas-compatible format in data files.

               Args:
                   dat_files (list): List of data file paths to process for assignment conversion.
               """
        for file in dat_files:
            dat_file_data = read_dat_file(file)
            dat_file_root = dat_file_data.getroot()

            referrer = dat_file_root.xpath(".//REFERRER/@id")[0] + ".dat"
            referred_to = dat_file_root.xpath(".//REFERREDTO/@id")[0] + ".dat"

            referrer_file_data = read_dat_file(referrer)
            referrer_file_root = referrer_file_data.getroot()
            referrer_content_handler = referrer_file_root.xpath("//CONTENTHANDLER")[0]

            # Update Content handler for Assignment
            referrer_content_handler.set("value", "resource/x-bb-assignment")

            referred_to_file_data = read_dat_file(referred_to)
            referred_to_file_root = referred_to_file_data.getroot()
            asmtid = referred_to_file_root.xpath("//ASMTID/@value")[0] + ".dat"

            asmtid_file_data = read_dat_file(asmtid)
            asmtid_file_root = asmtid_file_data.getroot()
            asmtid_formatted_text = asmtid_file_root.xpath("//mat_formattedtext")

            referrer_body_text = referrer_file_root.xpath("//BODY/TEXT")[0]

            if referrer_body_text.text is None:
                referrer_body_text.text = ""

            for assignment_text in asmtid_formatted_text:
                if assignment_text.text is not None:
                    referrer_body_text.text += assignment_text.text
                else:
                    pass

            save_dat_file(referrer, referrer_file_data)

            files_to_delete = [file, referred_to, asmtid]
            delete_dat_file(files_to_delete)
            self.remove_resource(files_to_delete)

    def remove_resource(self, resources):
        """Remove specified resources from the manifest.

        Args:
            resources (list): List of resource file paths to remove from the manifest.
        """
        for resource in resources:
            item_to_remove = self.manifest_root.xpath(f".//resource[@bb:file='{resource}']", namespaces=self.ns_map)
            item_to_remote_parent = item_to_remove[0].getparent()
            item_to_remote_parent.remove(item_to_remove[0])

    def write_imsmanifest(self):
        """Write changes to the imsmanifest.xml file."""

        with open(self.file_path, "wb") as file:
            self.manifest.write(file, encoding='UTF-8', xml_declaration=True)
