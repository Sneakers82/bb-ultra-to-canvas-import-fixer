import os
import zipfile
from lxml import etree
from config_loader import INPUT_DIR, OUTPUT_DIR, IMSMANIFEST


class ImsManifest:
    """Class to manage and modify the imsmanifest.xml file in a Blackboard course export."""

    def __init__(self, archive_file):
        """Initialize the ImsManifest by loading and parsing the imsmanifest.xml file."""
        self.archive_file = archive_file
        self.working_archive = f"{INPUT_DIR}/{archive_file}"
        self.manifest_root = self.extract_file(IMSMANIFEST)
        self.ns_map = {'bb': 'http://www.blackboard.com/content-packaging/'}
        self.files_to_modify = {}

    def extract_file(self, file_to_extract):

        # Open file we want to inspect
        with zipfile.ZipFile(self.working_archive, 'a') as archive:
            xml_bytes = archive.read(file_to_extract)
            root = etree.fromstring(xml_bytes)

            return root

    def store_changes(self, file_to_write, data):
        self.files_to_modify[file_to_write] = data

    def write_changes(self, pretty_print=False):

        temp_archive = f"{OUTPUT_DIR}/{self.archive_file}.tmp"  # Temporary archive for rebuilding
        with zipfile.ZipFile(self.working_archive, 'r') as archive:
            with zipfile.ZipFile(temp_archive, 'w', compression=zipfile.ZIP_DEFLATED) as temp_archive:
                for item in archive.infolist():
                    if item.filename in self.files_to_modify:

                        # Write the modified file
                        data = self.files_to_modify[item.filename]
                        temp_archive.writestr(
                            item.filename,
                            etree.tostring(
                                data,
                                pretty_print=pretty_print,
                                encoding='UTF-8'))
                    else:
                        # Stream unchanged files directly
                        with archive.open(item.filename) as source_file:
                            temp_archive.writestr(item, source_file.read())

        # Rename tmp Archive once done
        os.rename(f"{OUTPUT_DIR}/{self.archive_file}.tmp", f"{OUTPUT_DIR}/PATCHED_{self.archive_file}")

        # Clear the modification dictionary after applying changes
        self.files_to_modify.clear()

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
        return bool(self.manifest_root.xpath(".//item/title[text()='ROOT']"))

    def get_assignment_resources(self):
        """Retrieve assignment resource files listed in the manifest.

                Returns:
                    list: A list of paths to assignment data files within the manifest.
                """
        assignments = self.manifest_root.xpath(f".//resource[@type='resource/x-bb-link']", namespaces=self.ns_map)

        dat_files = [assignment.get('{http://www.blackboard.com/content-packaging/}file') for assignment in assignments
                     if assignment.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def get_discussion_resources(self):
        """Retrieve discussion resource files listed in the manifest.

                Returns:
                    list: A list of paths to assignment data files within the manifest.
                """
        discussions = self.manifest_root.xpath(f".//resource[@bb:title='' "
                                               f"and @type='resource/x-bb-link']", namespaces=self.ns_map)

        dat_files = [discussion.get('{http://www.blackboard.com/content-packaging/}file') for discussion in discussions
                     if discussion.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def get_gradebook_resource(self):
        """Retrieve gradebook resource files listed in the manifest.

                Returns:
                    list: A list of paths to assignment data files within the manifest.
                """
        gradebook = self.manifest_root.xpath(f".//resource[@type='course/x-bb-gradebook']", namespaces=self.ns_map)

        dat_files = [gradebook.get('{http://www.blackboard.com/content-packaging/}file') for gradebook in gradebook
                     if gradebook.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def get_documents(self):
        """Retrieve document resource files listed in the manifest.

        Returns:
            list: A list of paths to document data files within the manifest.
        """
        documents = self.manifest_root.xpath(f".//resource[@type='course/x-bb-gradebook']", namespaces=self.ns_map)

        dat_files = [document.get('{http://www.blackboard.com/content-packaging/}file') for document in documents
                     if document.get('{http://www.blackboard.com/content-packaging/}file')]

        return dat_files

    def add_lti_placeholder(self, dat_files):
        """Add placeholders for LTI resources in data files to indicate non-transferable content.

                Args:
                    dat_files (list): List of data file paths to modify for LTI placeholders.
                """
        for file in dat_files:

            dat_file_root = self.extract_file(file)

            title = dat_file_root.xpath(".//TITLE")[0]
            content_handler = dat_file_root.xpath("//CONTENTHANDLER")[0]

            if content_handler.values()[0].startswith("resource/x-bb-blti"):
                content_handler.set("value", "resource/x-bb-externallink")
                current_title = title.values()[0]
                placeholder = "[LTI Content: Replace] "
                title.set("value", placeholder + current_title)
                self.store_changes(file, dat_file_root)

    def get_ultra_assignments(self, resource_files):
        ultra_assignments = []
        fallback_assignments = []

        for file in resource_files:
            dat_file_root = self.extract_file(file)

            referrer = dat_file_root.find("REFERRER")
            referredto = dat_file_root.find("REFERREDTO")

            referrer_type = referrer.get("type")
            referredto_type = referredto.get("type")

            if referrer_type == "CONTENT" and referredto_type == "COURSE_ASSESSMENT":

                referrer = dat_file_root.xpath(".//REFERRER/@id")[0] + ".dat"
                referred_to = dat_file_root.xpath(".//REFERREDTO/@id")[0] + ".dat"

                referred_to_file_root = self.extract_file(referred_to)
                asmtid = referred_to_file_root.xpath("//ASMTID/@value")[0] + ".dat"

                asmtid_file_root = self.extract_file(asmtid)
                asmtid_ultra_assignment = asmtid_file_root.xpath(".//assessmentmetadata/bbmd_assessment_subtype[text("
                                                                 ")='Assignment']")
                if asmtid_ultra_assignment:
                    assignment = (file, referrer, referred_to, asmtid)
                    ultra_assignments.append(assignment)
                else:
                    assignment = (file, referrer, referred_to, asmtid)
                    fallback_assignments.append(assignment)

        return ultra_assignments if ultra_assignments else fallback_assignments

    def fix_assignments(self, dat_files):
        """Convert Blackboard assignments to Canvas-compatible format in data files.

               Args:
                   dat_files (list): List of data file paths to process for assignment conversion.
               """
        ultra_assignment_files = self.get_ultra_assignments(dat_files)

        for file in ultra_assignment_files:

            resource = file[0]
            referrer = file[1]
            referred_to = file[2]
            asmtid = file[3]

            referrer_file_root = self.extract_file(referrer)
            referrer_content_handler = referrer_file_root.xpath("//CONTENTHANDLER")[0]

            asmtid_file_root = self.extract_file(asmtid)
            asmtid_ultra_assignment = asmtid_file_root.xpath(".//assessmentmetadata/bbmd_assessment_subtype[text("
                                                             ")='Assignment']")
            asmtid_ultra_questions = asmtid_file_root.xpath(".//response_label")
            asmtid_ultra_question_banks = asmtid_file_root.xpath(".//selection_metadata[@mdname='bbmd_questionid']")
            asmtid_ultra_short_response = asmtid_file_root.xpath(".//bbmd_questiontype[text()='Short Response']")
            asmtid_ultra_fill_in_the_blank = asmtid_file_root.xpath(".//bbmd_questiontype[contains(text(), 'Fill "
                                                                    "in the Blank')]")

            # Check Bb Ultra asmtid file to see if it is an Assignment
            if (asmtid_ultra_assignment or
                    # Check Bb Ultra asmtid file to see if it has questions
                    (not (asmtid_ultra_questions or asmtid_ultra_question_banks or asmtid_ultra_short_response or
                          asmtid_ultra_fill_in_the_blank))):

                # Convert Ultra Assignment to Learn Original so Canvas can import it properly
                if asmtid_ultra_assignment and asmtid_ultra_assignment[0].text == "Assignment":
                    asmtid_formatted_text = asmtid_file_root.xpath(".//mat_formattedtext")
                else:
                    asmtid_formatted_text = asmtid_file_root.xpath(".//flow/material/mat_extension"
                                                                   "/mat_formattedtext")

                # Update Content handler for Assignment
                referrer_content_handler.set("value", "resource/x-bb-assignment")
                referrer_body_text = referrer_file_root.xpath("//BODY/TEXT")[0]

                if referrer_body_text.text is None:
                    referrer_body_text.text = ""

                for assignment_text in asmtid_formatted_text:
                    if assignment_text.text is not None:
                        referrer_body_text.text += assignment_text.text
                    else:
                        pass

                self.store_changes(referrer, referrer_file_root)

                files_to_delete = [resource, referred_to, asmtid]
                for file_to_delete in files_to_delete:
                    self.store_changes(file_to_delete, etree.Element("deleted"))

                self.remove_resource(files_to_delete)

    def fix_discussions(self, dat_files):
        """Convert Blackboard Discussions to Canvas-compatible format in data files.

               Args:
                   dat_files (list): List of data file paths to process for discussion conversion.
               """
        for file in dat_files:

            dat_file_root = self.extract_file(file)

            referrer = dat_file_root.find("REFERRER")
            referredto = dat_file_root.find("REFERREDTO")

            referrer_type = referrer.get("type")
            referredto_type = referredto.get("type")

            if referrer_type == "CONTENT" and referredto_type == "FORUM":
                referrer_content = dat_file_root.xpath(".//REFERRER/@id")[0] + ".dat"
                referred_to_forum = dat_file_root.xpath(".//REFERREDTO/@id")[0] + ".dat"

                # Get forum description
                referred_to_forum_root = self.extract_file(referred_to_forum)
                referred_to_forum_text_data = referred_to_forum_root.xpath(".//MESSAGETEXT/TEXT")

                # Check if None Type
                forum_description = "".join(
                    [text.text if text.text is not None else "" for text in referred_to_forum_text_data])

                # Get forum content
                referrer_content_root = self.extract_file(referrer_content)
                referrer_content_body_text = referrer_content_root.xpath("//BODY/TEXT")[0]

                # Fix forum description
                if referrer_content_body_text.text is None:
                    referrer_content_body_text.text = ""
                referrer_content_body_text.text += forum_description

                self.store_changes(referrer_content, referrer_content_root)

            elif referrer_type == "CONTENT" and referredto_type == "CONTENT":
                referrer = dat_file_root.xpath(".//REFERRER/@id")[0] + ".dat"

                referrer_file_root = self.extract_file(referrer)
                referrer_content_handler = referrer_file_root.xpath("//CONTENTHANDLER")[0]

                # Update Content handler of Forum
                referrer_content_handler.set("value", "resource/x-bb-forumlink")

                self.store_changes(referrer, referrer_file_root)

            else:
                pass

        # Remove INTERACTIVE group
        interactive_group = self.manifest_root.xpath("//item[title='INTERACTIVE']")

        if interactive_group:
            for item in interactive_group:
                parent = item.getparent()
                parent.remove(item)

        self.store_changes(IMSMANIFEST, self.manifest_root)

    def fix_gradebook(self):
        gradebook = self.get_gradebook_resource()
        gradebook_data = self.extract_file(gradebook[0])
        gradebook_empty_categories = gradebook_data.xpath(
            "//CATEGORY[not(@id = //OUTCOMEDEFINITION/CATEGORYID/@value)]")

        for category in gradebook_empty_categories:
            category.getparent().remove(category)
            self.store_changes(gradebook[0], gradebook_data)

    def remove_resource(self, resources):
        """Remove specified resources from the manifest.

        Args:
            resources (list): List of resource file paths to remove from the manifest.
        """
        for resource in resources:
            item_to_remove = self.manifest_root.xpath(f".//resource[@bb:file='{resource}']", namespaces=self.ns_map)
            item_to_remote_parent = item_to_remove[0].getparent()
            item_to_remote_parent.remove(item_to_remove[0])

        self.store_changes(IMSMANIFEST, self.manifest_root)
