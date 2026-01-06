# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san-studio SDK Software in commercial settings.
#
import os
from typing import Any, Dict, Union, TypedDict, Literal
from typing import Any
from typing import Dict
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool
from pypdf import PdfReader


class ExtractDocs(CodedTool):
    """
    CodedTool implementation extracts text from all PDFs in the given directory.
    Returns a dictionary mapping each PDF file name to its extracted text.
    """

    def __init__(self):
        # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
        self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/cabin"]

        self.docs_path = {
            "cabin passenger seating": "coded_tools/aircraft_cleaning/knowdocs/cabin/passenger_seating_area",
        }

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: An argument dictionary with the following keys:
            - "directory" (str): The directory containing the documents.

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
            but whose values are meant to be kept out of the chat stream.

            This dictionary is largely to be treated as read-only.
            It is possible to add key/value pairs to this dict that do not
            yet exist as a bulletin board, as long as the responsibility
            for which coded_tool publishes new entries is well understood
            by the agent chain implementation and the coded_tool implementation
            adding the data is not invoke()-ed more than once.

            Keys expected for this implementation are:
                None

        :return:
            If successful:
                A dictionary containing extracted text with the keys:
                - "file_name": The path and name of the processed document file.
                - "text": The extracted text from the document.
            Otherwise:
                A text string error message in the format:
                "Error: <error message>"
        """
        app_name: str = args.get("app_name", None)
        print("\n")
        print("\n")
        print("############### PDF text reader ###############")
        print("\n")
        print("\n")
        print(f"App name: {app_name}")
        print("\n")
        print("\n")
        if app_name is None:
            return "Error: No app name provided."
        directory = self.docs_path.get(app_name, self.default_path)

        # directory = directory[0]

        print("\n")
        print("\n")
        print(f"directory: {directory}")
        print("\n")
        print("directory:", directory)
        print("\n")        
        print("\n")  

        if not isinstance(directory, (str, bytes, os.PathLike)):
            print("\n")
            print("\n")
            print("Check point #1")
            print("\n")
            print("\n")  
            raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

        print("\n")
        print("\n")
        print("Check point #2")
        print("\n")
        print("\n")  

        docs = {}
        for root, dirs, files in os.walk(directory):

            print("\n")
            print("\n")
            print("Check point #3")
            print("\n")
            print("\n")  

            for file in files:

                print("\n")
                print("\n")
                print("Check point #4")
                print("\n")
                print("\n")  

                # Build the full path to the file
                print("\n")
                print("\n")
                print("root: ", root)
                print("file: ", file)
                print("\n")
                print("\n")
                file_path = os.path.join(root, file)
                if file.lower().endswith(".pdf"):
                    print("\n")
                    print("\n")
                    print("*************** PDF formatted file reader ***************")
                    print("\n")
                    print("\n")
                    # Extract PDF content
                    content = self.extract_pdf_content(file_path)
                    # Store in the dictionary using a relative path (relative to the main directory)
                    rel_path = os.path.relpath(file_path, directory)
                    docs[rel_path] = content
                elif file.lower().endswith(".txt"):
                    print("\n")
                    print("\n")
                    print("*************** TXT formatted file reader ***************")
                    print("\n")
                    print("\n")
                    # Extract text file content
                    content = self.extract_txt_content(file_path)
                    # Store in the dictionary using a relative path
                    rel_path = os.path.relpath(file_path, directory)
                    docs[rel_path] = content
        print("############### Documents extraction done ###############")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print(docs)
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        if not docs:
            print("No PDF or text files found in the directory.")
            return {"docs": {}}
        return {"files": docs}

    def extract_pdf_content(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file using pypdf, while attempting to preserve
        pagination (by inserting page headers).

        :param pdf_path: Full path to the PDF file.
        :return: Extracted text from the PDF.
        """
        text_output = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                # Add a page header for pagination
                text_output.append(f"\n\n--- Page {page_num + 1} ---\n\n")
                # Extract text from the page (fall back to empty string if None)
                page_text = page.extract_text() or ""
                text_output.append(page_text)
        except Exception as e:
            # In case there's an issue with reading the PDF
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

        return "".join(text_output)

    def extract_txt_content(self, txt_path: str) -> str:
        """
        Extract text from a plain text file.

        :param txt_path: Full path to the TXT file.
        :return: Content of the text file.
        """
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                print("\n")
                print("\n")
                print("text file path: ", txt_path)
                print("\n")
                print("\n")
                return f.read()
        except Exception as e:
            # In case there's an issue with reading the text file
            print(f"Error reading TXT {txt_path}: {e}")
            return ""
        

## findRestriction
## Addtion to check restriction per discussion with Risto 
class findRestriction(CodedTool):
    """
    CodedTool implementation extracts text from all PDFs in the given directory.
    Returns a dictionary mapping each PDF file name to its extracted text.
    """

    def __init__(self):
        # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
        self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/cabin"]

        self.docs_path = {
            "cabin crew seats and service entry door lining panels": "coded_tools/aircraft_cleaning/knowdocs/cabin/cabin_crew_seats_and_service_entry_door_lining_panels",
        }

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: An argument dictionary with the following keys:
            - "directory" (str): The directory containing the documents.

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
            but whose values are meant to be kept out of the chat stream.

            This dictionary is largely to be treated as read-only.
            It is possible to add key/value pairs to this dict that do not
            yet exist as a bulletin board, as long as the responsibility
            for which coded_tool publishes new entries is well understood
            by the agent chain implementation and the coded_tool implementation
            adding the data is not invoke()-ed more than once.

            Keys expected for this implementation are:
                None

        :return:
            If successful:
                A dictionary containing extracted text with the keys:
                - "file_name": The path and name of the processed document file.
                - "text": The extracted text from the document.
            Otherwise:
                A text string error message in the format:
                "Error: <error message>"
        """

        print("\n")
        print("\n")
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("&&&& THIS IS A CHECK THAT findRestriction Coded Tool has been called &&&&&")
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("\n")
        print("\n")

        app_name: str = args.get("app_name", None)
        print("\n")
        print("\n")
        print("############### PDF text reader ###############")
        print("\n")
        print("\n")
        print(f"App name: {app_name}")
        print("\n")
        print("\n")
        if app_name is None:
            return "Error: No app name provided."
        directory = self.docs_path.get(app_name, self.default_path)

        # Mdified from initial code to pick the first element of list
        directory = directory[0]

        print("\n")
        print("\n")
        print(f"directory: {directory}")
        print("\n")
        print("directory:", directory)
        print("\n")        
        print("\n")  

        if not isinstance(directory, (str, bytes, os.PathLike)):
            print("\n")
            print("\n")
            print("Check point #1")
            print("\n")
            print("\n")  
            raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

        print("\n")
        print("\n")
        print("Check point #2")
        print("\n")
        print("\n")  

        docs = {}
        for root, dirs, files in os.walk(directory):

            print("\n")
            print("\n")
            print("Check point #3")
            print("\n")
            print("\n")  

            for file in files:

                print("\n")
                print("\n")
                print("Check point #4")
                print("\n")
                print("\n")  

                # Build the full path to the file
                print("\n")
                print("\n")
                print("root: ", root)
                print("file: ", file)
                print("\n")
                print("\n")
                file_path = os.path.join(root, file)
                if file.lower().endswith(".pdf"):
                    print("\n")
                    print("\n")
                    print("*************** PDF formatted file reader ***************")
                    print("\n")
                    print("\n")
                    # Extract PDF content
                    content = self.extract_pdf_content(file_path)
                    # Store in the dictionary using a relative path (relative to the main directory)
                    rel_path = os.path.relpath(file_path, directory)
                    docs[rel_path] = content

                elif file.lower().endswith(".txt"):
                    print("\n")
                    print("\n")
                    print("*************** TXT formatted file reader ***************")
                    print("\n")
                    print("\n")
                    # Extract text file content
                    # Consider only files with name containing 'caution' as sign of existing restriction
                    if ('caution' in file_path): 
                        content = self.extract_txt_content(file_path)
                        # Store in the dictionary using a relative path
                        rel_path = os.path.relpath(file_path, directory)
                        docs[rel_path] = content

        print("############### Documents extraction done ###############")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print(docs)
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        if not docs:
            print("No PDF or text files found in the directory, or no restriction found.")
            return {"docs": {}}
        return {"files": docs}



    def extract_pdf_content(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file using pypdf, while attempting to preserve
        pagination (by inserting page headers).

        :param pdf_path: Full path to the PDF file.
        :return: Extracted text from the PDF.
        """
        text_output = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                # Add a page header for pagination
                text_output.append(f"\n\n--- Page {page_num + 1} ---\n\n")
                # Extract text from the page (fall back to empty string if None)
                page_text = page.extract_text() or ""
                text_output.append(page_text)
        except Exception as e:
            # In case there's an issue with reading the PDF
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

        # restriction_on_cleaning = "".join(text_output)
        # return restriction_on_cleaning

        return "".join(text_output)

    def extract_txt_content(self, txt_path: str) -> str:
        """
        Extract text from a plain text file.

        :param txt_path: Full path to the TXT file.
        :return: Content of the text file.
        """
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                print("\n")
                print("\n")
                print("text file path: ", txt_path)
                print("\n")
                print("\n")

                # restriction_on_cleaning = f.read()
                # return restriction_on_cleaning

                return f.read()
        except Exception as e:
            # In case there's an issue with reading the text file
            print(f"Error reading TXT {txt_path}: {e}")
            return ""
        
# escalateException

class escalateException(CodedTool):
    """
    CodedTool implementation extracts text from all PDFs in the given directory.
    Returns a dictionary mapping each PDF file name to its extracted text.
    """

    print("\n")
    print("\n")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&& THIS IS A CHECK THAT escalateException Coded Tool has been called &&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("\n")
    print("\n")

    print("\n")
    print("\n")
    print("\n")
    print("############################  ESCALATE EXCEPTION CLASS CHECK  ############################")
    print("\n")
    print("\n")
    print("\n")
    print("############################  ESCALATE EXCEPTION CLASS CHECK  ############################")
    print("\n")
    print("\n")
    print("\n")

    # def __init__(self):
    #     # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
    #     self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/cabin"]

    #     self.docs_path = {
    #         "cabin passenger seating": "coded_tools/aircraft_cleaning/knowdocs/cabin/passenger_seating_area",
    #     }

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: An argument dictionary with the following keys:
            - "directory" (str): The directory containing the documents.

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
            but whose values are meant to be kept out of the chat stream.

            This dictionary is largely to be treated as read-only.
            It is possible to add key/value pairs to this dict that do not
            yet exist as a bulletin board, as long as the responsibility
            for which coded_tool publishes new entries is well understood
            by the agent chain implementation and the coded_tool implementation
            adding the data is not invoke()-ed more than once.

            Keys expected for this implementation are:
                None

        :return:
            If successful:
                A dictionary containing extracted text with the keys:
                - "file_name": The path and name of the processed document file.
                - "text": The extracted text from the document.
            Otherwise:
                A text string error message in the format:
                "Error: <error message>"
        """

        # ground clearance type is required to fulfill the request.
        restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
        if not restriction_on_cleaning:
            print("No ground restriction on cleaning provided. Trying to get it from sly_data")
            restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
        # if not traffic_direction:
        #     error = "Error: Please provide a ground clearance type for the request."
        #     print(error)
        #     return error    
        sly_data["restriction_on_cleaning"] = restriction_on_cleaning

        # app_name: str = args.get("app_name", None)
        print("\n")
        print("\n")
        print("############### ESCALATION ###############")
        print("\n")
        print("\n")
        print("Message")
        print("\n")
        print("\n")

        message = f"The cleaning task has the following restriction: {restriction_on_cleaning}. Your cleaning plan does not comply with guidelines. Please reach out to your manager for advise."
        print(message)
        print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")
        print("\n")
        print("\n")
        # escalation_on_cleaning = "Your cleaning plan does not comply with guidelines. Please reach out to your manager for advise." 
        # print(escalation_on_cleaning)
        # print("\n")
        # print("\n")
        escalation_on_cleaning = message
        sly_data["escalation_on_cleaning"] = escalation_on_cleaning

        print("############### ESCALATION COMPLETED !!! ###############")
        print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")
        print("\n")
        print("\n")

        return escalation_on_cleaning

    # def extract_pdf_content(self, pdf_path: str) -> str:
    #     """
    #     Extract text from a PDF file using pypdf, while attempting to preserve
    #     pagination (by inserting page headers).

    #     :param pdf_path: Full path to the PDF file.
    #     :return: Extracted text from the PDF.
    #     """
    #     text_output = []
    #     try:
    #         reader = PdfReader(pdf_path)
    #         for page_num, page in enumerate(reader.pages):
    #             # Add a page header for pagination
    #             text_output.append(f"\n\n--- Page {page_num + 1} ---\n\n")
    #             # Extract text from the page (fall back to empty string if None)
    #             page_text = page.extract_text() or ""
    #             text_output.append(page_text)
    #     except Exception as e:
    #         # In case there's an issue with reading the PDF
    #         print(f"Error reading PDF {pdf_path}: {e}")
    #         return ""

    #     return "".join(text_output)

    # def extract_txt_content(self, txt_path: str) -> str:
    #     """
    #     Extract text from a plain text file.

    #     :param txt_path: Full path to the TXT file.
    #     :return: Content of the text file.
    #     """
    #     try:
    #         with open(txt_path, "r", encoding="utf-8") as f:
    #             print("\n")
    #             print("\n")
    #             print("text file path: ", txt_path)
    #             print("\n")
    #             print("\n")
    #             return f.read()
    #     except Exception as e:
    #         # In case there's an issue with reading the text file
    #         print(f"Error reading TXT {txt_path}: {e}")
    #         return ""

    # create_cleaning_tracker


########
# Structured payload returned to other agents/tools
class CleaningDict(TypedDict):
    restriction_on_cleaning: str                 # restriction on cleaning 
    escalation_on_cleaning: str                 # escalation on cleaning 

def build_cleaning_summary(
    restriction_on_cleaning: str,
    escalation_on_cleaning: str,
    ) -> CleaningDict:
    """
    Return a standardized cleaning dict for multi-agent handoffs.
    Raises ValueError on invalid input.
    """

    return {
        "restriction_on_cleaning": restriction_on_cleaning,
        "escalation_on_cleaning": escalation_on_cleaning
    }
########

######
class trackerAPI(CodedTool):

    """
    Cleaning information.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: a dictionary with the following keys:
            - restriction_on_cleaning: the restriction on training.
            - escalation_on_cleaning: the escalation on training.

        :param sly_data: a dictionary with the following keys:

        :return:
            In case of successful execution:
                all parameters available.
            otherwise:
                a string error message in the format:
                "Error: <error message>"
        """
        print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")

        # "restriction_on_cleaning": {
        #     "type": "string",
        #     "description": "The restriction on cleaning"
        # },
        # "escalation_on_cleaning": {
        #     "type": "string",
        #     "description": "This is the escalation message on cleaning"
        # },


        # # Client name is required to place an order.
        # customer_name: str = args.get("customer_name", None)
        # if not customer_name:
        #     print("No customer name provided. Trying to get it from sly_data")
        #     customer_name = sly_data.get("username")
        # if not customer_name:
        #     error = "Error: Please provide a valid customer name for the order."
        #     print(error)
        #     return error

        file_path_log = "/Users/971244/demospace/neuro-san-studio/test_debug/airlineturnaround.txt"

        # restriction on cleaning is needed in particular. 
        restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
        if not restriction_on_cleaning:
            print("No flight number provided. Trying to get it from sly_data")
            restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
        # if not flight_number:
        #     error = "Error: Please provide a flight number for the request."
        #     print(error)
        #     return error
        sly_data["restriction_on_cleaning"] = restriction_on_cleaning

        # escalation on cleaning is required to fulfill the request. 
        escalation_on_cleaning: str = args.get("escalation_on_cleaning", None)
        if not escalation_on_cleaning:
            print("No escalation_on_cleaning provided. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
        # if not aircraft_type:
        #     error = "Error: Please provide an aircraft type for the request."
        #     print(error)
        #     return error
        sly_data["escalation_on_cleaning"] = escalation_on_cleaning

        # build_cleaning_summary

        return build_cleaning_summary(
            restriction_on_cleaning=restriction_on_cleaning,
            escalation_on_cleaning=escalation_on_cleaning,
        )
