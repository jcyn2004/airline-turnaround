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
from typing import Dict, Any, Union, Optional, Tuple, List, Literal, TypedDict
from neuro_san.interfaces.coded_tool import CodedTool
from pypdf import PdfReader
from datetime import datetime
import time
import logging
from enum import Enum
from dataclasses import dataclass
import re
import pandas as pd

## findRestriction
## Addtion to check restriction per discussion with Risto 
# class pull_restriction(CodedTool):
class ExtractDocs(CodedTool):
    """
    CodedTool implementation extracts text from all PDFs in the given directory.
    Returns a dictionary mapping each PDF file name to its extracted text.
    """

    print("\n")
    print("\n")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&& THIS IS A CHECK THAT pull_restriction Coded Tool has been called &&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("\n")
    print("\n")

    def __init__(self):
        # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
        self.default_path = ["coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin"]

        self.docs_path = {
            "cabin crew seats and service entry door lining panels": "coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin/passenger_seating_area",
        }

            # "cabin crew seats and service entry door lining panels": "coded_tools/aircraft_cleaning/knowdocs/cabin/cabin_crew_seats_and_service_entry_door_lining_panels",

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
        print(f"App name in args: {app_name}")
        print("\n")
        print("\n")
        if app_name is None:
            return "Error: No app name provided."
        directory = self.docs_path.get(app_name, self.default_path)
        print("\n")
        print("\n")
        print(f"directory: {directory}")
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
            print("directory not found:", directory)
            print("\n")
            print("\n")  
            raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

        print("\n")
        print("\n")
        print("Check point #2")
        print("\n")
        print("\n")  

        # content = restriction_applies
        content = ''
        docs = {}
        for root, dirs, files in os.walk(directory):

            print("\n")
            print("\n")
            print("Check point #3")
            print("root: ", root)
            print("dirs: ", dirs)
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
                    print("file_path: ", file_path)
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
                    print("file_path: ", file_path)
                    print("\n")
                    print("\n")
                    # Extract text file content
                    # Consider only files with name containing 'caution' as sign of existing restriction
                    if ('caution' not in file_path): 
                        content = self.extract_txt_content(file_path)
                        # Store in the dictionary using a relative path
                        rel_path = os.path.relpath(file_path, directory)
                        docs[rel_path] = content

        print("############### Documents extraction done in ExtractDocs ###############")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("docs: ", docs)
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("content: ", content)
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")

        if not docs:
            print("No PDF or text files found in the directory, or no restriction found.")
            return {"docs": {}}
        # return {"files": docs}
        # if (content is not None): 
        # if (content is None): 
        #     restriction_applies = 'no'
        # else: 
        #     restriction_applies = 'yes'
        # sly_data["restriction_applies"] = restriction_applies
        cleaning_procedure = content
        sly_data["cleaning_procedure"] = cleaning_procedure

        print("\n")
        print("\n")
        print("+++++++++++++++ PROCEDURE RESPONSE +++++++++++++++")
        print("cleaning_procedure: ", cleaning_procedure)
        print("\n")
        # print("restriction_applies: ", restriction_applies)
        print("+++++++++++++++ PROCEDURE RESPONSE +++++++++++++++")
        print("\n")
        print("\n")

        return cleaning_procedure #, restriction_applies
    
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

        cleaning_procedure = "".join(text_output)
        return cleaning_procedure

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

# class ExtractDocs(CodedTool):
#     """
#     CodedTool implementation extracts text from all PDFs in the given directory.
#     Returns a dictionary mapping each PDF file name to its extracted text.
#     """

#     print("\n")
#     print("\n")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&& Line 32 - THIS IS A CHECK THAT extractdocs Coded Tool has been called &&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("\n")
#     print("\n")

#     def __init__(self):
#         # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
#         self.default_path = ["coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin"]

#         self.docs_path = {
#             "cabin crew seats and service entry door lining panels": "coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin/passenger_seating_area",
#         }

#             # "cabin crew seats and service entry door lining panels": "coded_tools/aircraft_cleaning/knowdocs/cabin/cabin_crew_seats_and_service_entry_door_lining_panels",

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: An argument dictionary with the following keys:
#             - "directory" (str): The directory containing the documents.

#         :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
#             but whose values are meant to be kept out of the chat stream.

#             This dictionary is largely to be treated as read-only.
#             It is possible to add key/value pairs to this dict that do not
#             yet exist as a bulletin board, as long as the responsibility
#             for which coded_tool publishes new entries is well understood
#             by the agent chain implementation and the coded_tool implementation
#             adding the data is not invoke()-ed more than once.

#             Keys expected for this implementation are:
#                 None

#         :return:
#             If successful:
#                 A dictionary containing extracted text with the keys:
#                 - "file_name": The path and name of the processed document file.
#                 - "text": The extracted text from the document.
#             Otherwise:
#                 A text string error message in the format:
#                 "Error: <error message>"
#         """

#         app_name: str = args.get("app_name", None)
#         print("\n")
#         print("\n")
#         print("############### Line 79 - PDF text reader from extractdocs ###############")
#         print("\n")
#         print("\n")
#         print(f" Line 82 - App name in args: {app_name}")
#         print("\n")
#         print("\n")
#         if app_name is None:
#             return "Error: No app name provided."
#         directory = self.docs_path.get(app_name, self.default_path)
#         print("\n")
#         print("\n")
#         print(f" Line 90 - directory: {directory}")
#         # Mdified from initial code to pick the first element of list
#         directory = directory[0]

#         print("\n")
#         print("\n")
#         print(f" Line 96 - directory: {directory}")
#         print("\n")
#         print(" Line 98 - directory:", directory)
#         print("\n")        
#         print("\n")  

#         if not isinstance(directory, (str, bytes, os.PathLike)):
#             print("\n")
#             print("\n")
#             print(" Line 105 - Check point #1")
#             print(" Line 106 - directory not found:", directory)
#             print("\n")
#             print("\n")  
#             raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

#         print("\n")
#         print("\n")
#         print(" Line 113 - Check point #2")
#         print("\n")
#         print("\n")  

#         # content = restriction_applies
#         content = ''
#         docs = {}
#         for root, dirs, files in os.walk(directory):

#             print("\n")
#             print("\n")
#             print(" Line 124 - Check point #3")
#             print(" Line 125 - root: ", root)
#             print(" Line 126 - dirs: ", dirs)
#             print("\n")
#             print("\n")  

#             for file in files:

#                 print("\n")
#                 print("\n")
#                 print(" Line 134 - Check point #4")
#                 print("\n")
#                 print("\n")  

#                 # Build the full path to the file
#                 print("\n")
#                 print("\n")
#                 print(" Line 141 - root: ", root)
#                 print(" Line 142 - file: ", file)
#                 print("\n")
#                 print("\n")
#                 file_path = os.path.join(root, file)
#                 if file.lower().endswith(".pdf"):
#                     print("\n")
#                     print("\n")
#                     print("*************** Line 149 - PDF formatted file reader  from extractdocs ***************")
#                     print("\n")
#                     print("\n")
#                     print(" Line 152 - file_path: ", file_path)
#                     print("\n")
#                     print("\n")
#                     # Extract PDF content
#                     content = self.extract_pdf_content(file_path)
#                     # Store in the dictionary using a relative path (relative to the main directory)
#                     rel_path = os.path.relpath(file_path, directory)
#                     docs[rel_path] = content

#                 elif file.lower().endswith(".txt"):
#                     print("\n")
#                     print("\n")
#                     print("*************** Line 164 - TXT formatted file reader  from extractdocs ***************")
#                     print("\n")
#                     print("\n")
#                     print(" Line 167 - file_path: ", file_path)
#                     print("\n")
#                     print("\n")
#                     # Extract text file content
#                     # Consider only files with name containing 'caution' as sign of existing restriction
#                     if ('caution' not in file_path): 
#                         content = self.extract_txt_content(file_path)
#                         # Store in the dictionary using a relative path
#                         rel_path = os.path.relpath(file_path, directory)
#                         docs[rel_path] = content

#         print("############### Line 178 - Documents extraction  from extractdocs  ###############")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print(" Line 184 - docs: ", docs)
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print(" Line 190 - content: ", content)
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")

#         if not docs:
#             print("No PDF or text files found in the directory, or no restriction found.")
#             return {"docs": {}}
#         # return {"files": docs}
#         # if (content is not None): 
#         # if (content is None): 
#         #     restriction_applies = 'no'
#         # else: 
#         #     restriction_applies = 'yes'
#         # sly_data["restriction_applies"] = restriction_applies
#         cleaning_procedure = content
#         sly_data["cleaning_procedure"] = cleaning_procedure

#         print("\n")
#         print("\n")
#         print("+++++++++++++++ Line 211 - PROCEDURE RESPONSE +++++++++++++++")
#         print(" Line 212 - cleaning_procedure: ", cleaning_procedure)
#         print("\n")
#         # print("restriction_applies: ", restriction_applies)
#         print("+++++++++++++++ Line 215 - PROCEDURE RESPONSE +++++++++++++++")
#         print("\n")
#         print("\n")

#         return cleaning_procedure #, restriction_applies


# class ExtractDocs(CodedTool):
#     """
#     CodedTool implementation extracts text from all PDFs in the given directory.
#     Returns a dictionary mapping each PDF file name to its extracted text.
#     """

#     print("\n")
#     print("\n")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&& Line 32 - THIS IS A CHECK THAT extractdocs Coded Tool has been called &&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("\n")
#     print("\n")

#     def __init__(self):
#         # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
#         self.default_path = ["coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin"]

#         self.docs_path = {
#             "cabin crew seats and service entry door lining panels": "coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin/passenger_seating_area",
#         }

#             # "cabin crew seats and service entry door lining panels": "coded_tools/aircraft_cleaning/knowdocs/cabin/cabin_crew_seats_and_service_entry_door_lining_panels",

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: An argument dictionary with the following keys:
#             - "directory" (str): The directory containing the documents.

#         :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
#             but whose values are meant to be kept out of the chat stream.

#             This dictionary is largely to be treated as read-only.
#             It is possible to add key/value pairs to this dict that do not
#             yet exist as a bulletin board, as long as the responsibility
#             for which coded_tool publishes new entries is well understood
#             by the agent chain implementation and the coded_tool implementation
#             adding the data is not invoke()-ed more than once.

#             Keys expected for this implementation are:
#                 None

#         :return:
#             If successful:
#                 A dictionary containing extracted text with the keys:
#                 - "file_name": The path and name of the processed document file.
#                 - "text": The extracted text from the document.
#             Otherwise:
#                 A text string error message in the format:
#                 "Error: <error message>"
#         """

#         app_name: str = args.get("app_name", None)
#         print("\n")
#         print("\n")
#         print("############### Line 79 - PDF text reader from extractdocs ###############")
#         print("\n")
#         print("\n")
#         print(f" Line 82 - App name in args: {app_name}")
#         print("\n")
#         print("\n")
#         if app_name is None:
#             return "Error: No app name provided."
#         directory = self.docs_path.get(app_name, self.default_path)
#         print("\n")
#         print("\n")
#         print(f" Line 90 - directory: {directory}")
#         # Mdified from initial code to pick the first element of list
#         directory = directory[0]

#         print("\n")
#         print("\n")
#         print(f" Line 96 - directory: {directory}")
#         print("\n")
#         print(" Line 98 - directory:", directory)
#         print("\n")        
#         print("\n")  

#         if not isinstance(directory, (str, bytes, os.PathLike)):
#             print("\n")
#             print("\n")
#             print(" Line 105 - Check point #1")
#             print(" Line 106 - directory not found:", directory)
#             print("\n")
#             print("\n")  
#             raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

#         print("\n")
#         print("\n")
#         print(" Line 113 - Check point #2")
#         print("\n")
#         print("\n")  

#         # content = restriction_applies
#         content = ''
#         docs = {}
#         for root, dirs, files in os.walk(directory):

#             print("\n")
#             print("\n")
#             print(" Line 124 - Check point #3")
#             print(" Line 125 - root: ", root)
#             print(" Line 126 - dirs: ", dirs)
#             print("\n")
#             print("\n")  

#             for file in files:

#                 print("\n")
#                 print("\n")
#                 print(" Line 134 - Check point #4")
#                 print("\n")
#                 print("\n")  

#                 # Build the full path to the file
#                 print("\n")
#                 print("\n")
#                 print(" Line 141 - root: ", root)
#                 print(" Line 142 - file: ", file)
#                 print("\n")
#                 print("\n")
#                 file_path = os.path.join(root, file)
#                 if file.lower().endswith(".pdf"):
#                     print("\n")
#                     print("\n")
#                     print("*************** Line 149 - PDF formatted file reader  from extractdocs ***************")
#                     print("\n")
#                     print("\n")
#                     print(" Line 152 - file_path: ", file_path)
#                     print("\n")
#                     print("\n")
#                     # Extract PDF content
#                     content = self.extract_pdf_content(file_path)
#                     # Store in the dictionary using a relative path (relative to the main directory)
#                     rel_path = os.path.relpath(file_path, directory)
#                     docs[rel_path] = content

#                 elif file.lower().endswith(".txt"):
#                     print("\n")
#                     print("\n")
#                     print("*************** Line 164 - TXT formatted file reader  from extractdocs ***************")
#                     print("\n")
#                     print("\n")
#                     print(" Line 167 - file_path: ", file_path)
#                     print("\n")
#                     print("\n")
#                     # Extract text file content
#                     # Consider only files with name containing 'caution' as sign of existing restriction
#                     if ('caution' not in file_path): 
#                         content = self.extract_txt_content(file_path)
#                         # Store in the dictionary using a relative path
#                         rel_path = os.path.relpath(file_path, directory)
#                         docs[rel_path] = content

#         print("############### Line 178 - Documents extraction  from extractdocs  ###############")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print(" Line 184 - docs: ", docs)
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print("\n")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print(" Line 190 - content: ", content)
#         print("+++++++++++++++ DOCS +++++++++++++++")
#         print("\n")
#         print("\n")
#         print("+++++++++++++++ DOCS +++++++++++++++")

#         if not docs:
#             print("No PDF or text files found in the directory, or no restriction found.")
#             return {"docs": {}}
#         # return {"files": docs}
#         # if (content is not None): 
#         # if (content is None): 
#         #     restriction_applies = 'no'
#         # else: 
#         #     restriction_applies = 'yes'
#         # sly_data["restriction_applies"] = restriction_applies
#         cleaning_procedure = content
#         sly_data["cleaning_procedure"] = cleaning_procedure

#         print("\n")
#         print("\n")
#         print("+++++++++++++++ Line 211 - PROCEDURE RESPONSE +++++++++++++++")
#         print(" Line 212 - cleaning_procedure: ", cleaning_procedure)
#         print("\n")
#         # print("restriction_applies: ", restriction_applies)
#         print("+++++++++++++++ Line 215 - PROCEDURE RESPONSE +++++++++++++++")
#         print("\n")
#         print("\n")

#         return cleaning_procedure #, restriction_applies


# class ExtractDocs(CodedTool):
#     """
#     CodedTool implementation extracts text from all PDFs in the given directory.
#     Returns a dictionary mapping each PDF file name to its extracted text.
#     """

#     print("\n")
#     print("\n")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&& THIS IS A CHECK THAT extractdocs Coded Tool has been called &&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#     print("\n")
#     print("\n")

#     def __init__(self):
#         # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
#         # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/cabin"]

#         self.default_path = ["coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin"]


#         self.docs_path = {
#             "cabin passenger seating": "coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin/passenger_seating_area",
#         }

#             # "cabin passenger seating": "coded_tools/aircraft_cleaning/knowdocs/cabin/passenger_seating_area",

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: An argument dictionary with the following keys:
#             - "directory" (str): The directory containing the documents.

#         :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
#             but whose values are meant to be kept out of the chat stream.

#             This dictionary is largely to be treated as read-only.
#             It is possible to add key/value pairs to this dict that do not
#             yet exist as a bulletin board, as long as the responsibility
#             for which coded_tool publishes new entries is well understood
#             by the agent chain implementation and the coded_tool implementation
#             adding the data is not invoke()-ed more than once.

#             Keys expected for this implementation are:
#                 None

#         :return:
#             If successful:
#                 A dictionary containing extracted text with the keys:
#                 - "file_name": The path and name of the processed document file.
#                 - "text": The extracted text from the document.
#             Otherwise:
#                 A text string error message in the format:
#                 "Error: <error message>"
#         """

#         print("\n")
#         print("\n")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&& THIS IS A CHECK THAT ExtractDocs Coded Tool has been called &&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("\n")
#         print("\n")

#         content = ''

#         user_inquiry: str = args.get("user_inquiry", None)
#         print("\n")
#         print("\n")
#         print("user_inquiry in args: ",user_inquiry)
#         print("\n")
#         print("\n")
#         if not user_inquiry:
#             print("user inquiry not provided. Trying to get it from sly_data")
#             user_inquiry = sly_data.get("user_inquiry")
#             print("\n")
#             print("\n")
#             print("user_inquiry in sly_data: ",user_inquiry)
#             print("\n")
#             print("\n")            
#         if sly_data.get("user_inquiry", None) is None:
#             sly_data["user_inquiry"] = user_inquiry
#             print("\n")
#             print("\n")
#             print("user_inquiry in sly_data: ",user_inquiry)
#             print("\n")
#             print("\n")            
#         if sly_data.get("user_inquiry", None) is None:
#             sly_data["user_inquiry"] = user_inquiry

#         user_response_to_recommendation: str = args.get("user_response_to_recommendation", None)
#         print("\n")
#         print("\n")
#         print("user_response_to_recommendation in args: ",user_response_to_recommendation)
#         print("\n")
#         print("\n")
#         if not user_response_to_recommendation:
#             print("response to recommendation not provided. Trying to get it from sly_data")
#             user_response_to_recommendation = sly_data.get("user_response_to_recommendation")
#             print("\n")
#             print("\n")
#             print("user_response_to_recommendation in sly_data: ",user_response_to_recommendation)
#             print("\n")
#             print("\n")            
#         if sly_data.get("user_response_to_recommendation", None) is None:
#             sly_data["user_response_to_recommendation"] = user_response_to_recommendation

#         restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
#         print("\n")
#         print("\n")
#         print("restriction_on_cleaning in args: ",restriction_on_cleaning)
#         print("\n")
#         print("\n")
#         if not restriction_on_cleaning:
#             print("restriction on cleaning not provided. Trying to get it from sly_data")
#             restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
#             print("\n")
#             print("\n")
#             print("restriction_on_cleaning in sly_data: ",restriction_on_cleaning)
#             print("\n")
#             print("\n")    
#         if sly_data.get("restriction_on_cleaning", None) is None:
#             sly_data["restriction_on_cleaning"] = restriction_on_cleaning

#         compliance_response: str = args.get("compliance_response", None)
#         print("\n")
#         print("\n")
#         print("compliance_response in args: ",compliance_response)
#         print("\n")
#         print("\n")
#         if not compliance_response:
#             print("user inquiry compliant not provided. Trying to get it from sly_data")
#             compliance_response = sly_data.get("compliance_response")
#             print("\n")
#             print("\n")
#             print("compliance_response in sly_data: ",compliance_response)
#             print("\n")
#             print("\n")   
#         if sly_data.get("compliance_response", None) is None:
#             sly_data["compliance_response"] = compliance_response

#         app_name: str = args.get("app_name", None)
#         print("\n")
#         print("\n")
#         print("############### PDF text reader in extract docs ###############")
#         print("\n")
#         print("\n")
#         print(f"App name in args: {app_name}")
#         print("\n")
#         print("\n")
#         if app_name is None:
#             return "Error: No app name provided."
#         directory = self.docs_path.get(app_name, self.default_path)

#         directory = directory[0]

#         print("\n")
#         print("\n")
#         print(f"directory: {directory}")
#         print("\n")
#         print("directory:", directory)
#         print("\n")        
#         print("\n")  

#         if not isinstance(directory, (str, bytes, os.PathLike)):
#             print("\n")
#             print("\n")
#             print("Check point #1")
#             print("directory not found:", directory)
#             print("\n")
#             print("\n")  
#             raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

#         print("\n")
#         print("\n")
#         print("Check point #2")
#         print("\n")
#         print("\n")  

#         # if ((user_response_to_recommendation != 'yes') | (restriction_applies != 'yes') | (restriction_on_cleaning is None)):

#         if ((user_response_to_recommendation == 'yes') | (restriction_on_cleaning is None) | (compliance_response == 'compliant')):

#             docs = {}
#             for root, dirs, files in os.walk(directory):

#                 print("\n")
#                 print("\n")
#                 print("Check point #3")
#                 print("\n")
#                 print("\n")  

#                 for file in files:

#                     print("\n")
#                     print("\n")
#                     print("Check point #4")
#                     print("\n")
#                     print("\n")  

#                     # Build the full path to the file
#                     print("\n")
#                     print("\n")
#                     print("root: ", root)
#                     print("file: ", file)
#                     print("\n")
#                     print("\n")
#                     file_path = os.path.join(root, file)
#                     if file.lower().endswith(".pdf"):
#                         print("\n")
#                         print("\n")
#                         print("*************** PDF formatted file reader ***************")
#                         print("\n")
#                         print("\n")
#                         # Extract PDF content
#                         content = self.extract_pdf_content(file_path)
#                         # Store in the dictionary using a relative path (relative to the main directory)
#                         rel_path = os.path.relpath(file_path, directory)
#                         docs[rel_path] = content
#                     elif file.lower().endswith(".txt"):
#                         print("\n")
#                         print("\n")
#                         print("*************** TXT formatted file reader ***************")
#                         print("\n")
#                         print("\n")
#                         # Extract text file content
#                         content = self.extract_txt_content(file_path)
#                         # Store in the dictionary using a relative path
#                         rel_path = os.path.relpath(file_path, directory)
#                         docs[rel_path] = content
#             print("############### Documents extraction done in ExtractDocs ###############")
#             print("\n")
#             print("\n")
#             print("+++++++++++++++ DOCS +++++++++++++++")
#             print("\n")
#             print("\n")
#             print(docs)
#             print("\n")
#             print("\n")
#             print("+++++++++++++++ DOCS +++++++++++++++")
#             if not docs:
#                 print("No PDF or text files found in the directory.")
#                 return {"docs": {}}
#             # return {"files": docs}
#         cleaning_procedure = content
#         sly_data["cleaning_procedure"] = cleaning_procedure

#         print("\n")
#         print("\n")
#         print("+++++++++++++++ COMPLIANT CLEANING +++++++++++++++")
#         print(cleaning_procedure)
#         print("+++++++++++++++ COMPLIANT CLEANING +++++++++++++++")
#         print("\n")
#         print("\n")

#         return cleaning_procedure

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
        

## findRestriction
## Addtion to check restriction per discussion with Risto 
class pull_restriction(CodedTool):
    """
    CodedTool implementation extracts text from all PDFs in the given directory.
    Returns a dictionary mapping each PDF file name to its extracted text.
    """

    print("\n")
    print("\n")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&& THIS IS A CHECK THAT pull_restriction Coded Tool has been called &&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("\n")
    print("\n")

    def __init__(self):
        # self.default_path = ["coded_tools/aircraft_cleaning/knowdocs/Help Center.txt"]
        self.default_path = ["coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin"]

        self.docs_path = {
            "cabin crew seats and service entry door lining panels": "coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/knowdocs/cabin/passenger_seating_area",
        }

            # "cabin crew seats and service entry door lining panels": "coded_tools/aircraft_cleaning/knowdocs/cabin/cabin_crew_seats_and_service_entry_door_lining_panels",

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
        print(f"App name in args: {app_name}")
        print("\n")
        print("\n")
        if app_name is None:
            return "Error: No app name provided."
        directory = self.docs_path.get(app_name, self.default_path)
        print("\n")
        print("\n")
        print(f"directory: {directory}")
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
            print("directory not found:", directory)
            print("\n")
            print("\n")  
            raise TypeError(f"Expected str, bytes, or os.PathLike object, got {type(directory).__name__} instead")

        print("\n")
        print("\n")
        print("Check point #2")
        print("\n")
        print("\n")  

        # content = restriction_applies
        content = ''
        docs = {}
        for root, dirs, files in os.walk(directory):

            print("\n")
            print("\n")
            print("Check point #3")
            print("root: ", root)
            print("dirs: ", dirs)
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
                    print("file_path: ", file_path)
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
                    print("file_path: ", file_path)
                    print("\n")
                    print("\n")
                    # Extract text file content
                    # Consider only files with name containing 'caution' as sign of existing restriction
                    if ('caution' in file_path): 
                        content = self.extract_txt_content(file_path)
                        # Store in the dictionary using a relative path
                        rel_path = os.path.relpath(file_path, directory)
                        docs[rel_path] = content

        print("############### Documents extraction done in pull_restriction ###############")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("docs: ", docs)
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("content: ", content)
        print("+++++++++++++++ DOCS +++++++++++++++")
        print("\n")
        print("\n")
        print("+++++++++++++++ DOCS +++++++++++++++")

        if not docs:
            print("No PDF or text files found in the directory, or no restriction found.")
            return {"docs": {}}
        # return {"files": docs}
        # if (content is not None): 
        # if (content is None): 
        #     restriction_applies = 'no'
        # else: 
        #     restriction_applies = 'yes'
        # sly_data["restriction_applies"] = restriction_applies
        restriction_on_cleaning = content
        sly_data["restriction_on_cleaning"] = restriction_on_cleaning

        print("\n")
        print("\n")
        print("+++++++++++++++ PROCEDURE RESPONSE +++++++++++++++")
        print("restriction_on_cleaning: ", restriction_on_cleaning)
        print("\n")
        # print("restriction_applies: ", restriction_applies)
        print("+++++++++++++++ PROCEDURE RESPONSE +++++++++++++++")
        print("\n")
        print("\n")

        return restriction_on_cleaning #, restriction_applies
    
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

class create_escalation(CodedTool):
    """
    CodedTool implementation creates an escalation.
    Returns an escalation message.
    """

    print("\n")
    print("\n")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&& line 1244 - THIS IS A CHECK THAT create_escalation Coded Tool has been called &&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("\n")
    print("\n")

    print("\n")
    print("\n")
    print("\n")
    print("############################ line 1253 -  ESCALATE EXCEPTION CLASS CHECK  ############################")
    print("\n")
    print("\n")
    print("\n")
    print("############################ line 1257 -  ESCALATE EXCEPTION CLASS CHECK  ############################")
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
                restriction_on_cleaning 
                user_response_to_recommendation

        :return:
            If successful:
                A dictionary containing extracted text with the keys:
                - "file_name": The path and name of the processed document file.
                - "text": The extracted text from the document.
            Otherwise:
                A text string error message in the format:
                "Error: <error message>"
        """

        # user inquiry type is required to fulfill the inquiry.
        user_inquiry: str = args.get("user_inquiry", None)
        print("\n")
        print("\n")
        print("line 1303 - user_inquiry in args: ",user_inquiry)
        print("\n")
        print("\n")
        if not user_inquiry:
            print("No user_inquiry provided. Trying to get it from sly_data")
            user_inquiry = sly_data.get("user_inquiry")
            print("\n")
            print("\n")
            print("user_inquiry in sly_data: ",user_inquiry)
            print("\n")
            print("\n")   
        if not user_inquiry:
            sly_data["user_inquiry"] = user_inquiry

        # restriction on cleaning type is required to fulfill the inquiry.
        restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
        print("\n")
        print("\n")
        print("line 1321 - restriction_on_cleaning in args: ",restriction_on_cleaning)
        print("\n")
        print("\n")
        if not restriction_on_cleaning:
            print("No ground restriction on cleaning provided. Trying to get it from sly_data")
            restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
            print("\n")
            print("\n")
            print("restriction_on_cleaning in sly_data: ",restriction_on_cleaning)
            print("\n")
            print("\n")   
        if not restriction_on_cleaning:
            sly_data["restriction_on_cleaning"] = restriction_on_cleaning

        # response to recommendation type is required to fulfill the inquiry.
        user_response_to_recommendation: str = args.get("user_response_to_recommendation", None)
        print("\n")
        print("\n")
        print("line 1339 - user_response_to_recommendation in args: ",user_response_to_recommendation)
        print("\n")
        print("\n")
        if not user_response_to_recommendation:
            print("No response to recommendation provided. Trying to get it from sly_data")
            user_response_to_recommendation = sly_data.get("user_response_to_recommendation")
            print("\n")
            print("\n")
            print("user_response_to_recommendation in sly_data: ",user_response_to_recommendation)
            print("\n")
            print("\n")   
        if not user_response_to_recommendation:
            sly_data["user_response_to_recommendation"] = user_response_to_recommendation

        # app_name: str = args.get("app_name", None)
        print("\n")
        print("\n")
        print("############### line 1356 - ESCALATION ###############")
        print("\n")
        print("\n")
        print("Message")
        print("\n")
        print("\n")

        escalation_response = 'No escalation on cleaning.'

        if ((user_response_to_recommendation is 'no') & (restriction_on_cleaning is not None)): 

            message = f"Your cleaning plan \"{user_inquiry}\" does not comply with the cleaning restriction {restriction_on_cleaning}. Please reach out to your manager for advise."
            print(message)
            print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")
            # escalation_on_cleaning = "Your cleaning plan does not comply with guidelines. Please reach out to your manager for advise." 
            # print(escalation_on_cleaning)
            # print("\n")
            # print("\n")
            escalation_response = message
            sly_data["escalation_response"] = escalation_response

            print("############### ESCALATION COMPLETED !!! ###############")
            print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")

            print("\n")
            print("\n")
            print("+++++++++++++++ ESCALATION ON CLEANING +++++++++++++++")
            print("line 1387 - escalation_response: ", escalation_response)
            print("+++++++++++++++ ESCALATION ON CLEANING +++++++++++++++")
            print("\n")
            print("\n")

            return escalation_response

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

# class cleaning_tracker(CodedTool):
#     """
#     Aircraft cleaning tracker.
#     """

#     # SHOP_1 = "Bob's Coffee Shop"
#     # SHOP_2 = "Henry's Fast Food"
#     # SHOP_3 = "Joe's Gas Station"
#     # SHOP_4 = "Jack's Liquor Store"
#     # SHOPS = [SHOP_1, SHOP_2, SHOP_3, SHOP_4]
#     # FIRST_ORDER_ID = {SHOP_1: 100, SHOP_2: 200, SHOP_3: 300, SHOP_4: 400}

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - app_name: the name of the app.
#             - restriction_on_cleaning: the details of the cleaning restriction.
#             - escalation_on_cleaning: the details of the escalation.
#             - user_response_to_recommendation: user response to cleaning recommendation. 

#         :param sly_data: a dictionary with the following keys:
#             - app_name: the name of the app.
#             - restriction_on_cleaning: the details of the cleaning restriction.
#             - escalation_on_cleaning: the details of the escalation.
#             - user_response_to_recommendation: user response to cleaning recommendation. 
#         """

#         print("\n")
#         print("\n")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&& THIS IS A CHECK THAT cleaning_tracker Coded Tool has been called &&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("\n")
#         print("\n")

#         # :return:
#         #     In case of successful execution:
#         #         an order number as a string.
#         #     otherwise:
#         #         a string error message in the format:
#         #         "Error: <error message>"

#         print(">>>>>>>>>>>>>>>>>>> cleaning tracker >>>>>>>>>>>>>>>>>>")
#         # State and parameters of teh cleaning. 

#         user_inquiry: str = args.get("app_user_inquiryname", None)
#         print("\n")
#         print("\n")
#         print("user_inquiry in args: ",user_inquiry)
#         print("\n")
#         print("\n")
#         if not user_inquiry:
#             print("No user inquiry provided. Trying to get it from sly_data")
#             user_inquiry = sly_data.get("user_inquiry")
#             print("\n")
#             print("\n")
#             print("user_inquiry in sly_data: ",user_inquiry)
#             print("\n")
#             print("\n")   
#         if sly_data.get("user_inquiry", None) is None:
#             sly_data["user_inquiry"] = user_inquiry

#         app_name: str = args.get("app_name", None)
#         print("\n")
#         print("\n")
#         print("app_name in args: ",app_name)
#         print("\n")
#         print("\n")
#         if not app_name:
#             print("No customer name provided. Trying to get it from sly_data")
#             app_name = sly_data.get("app_name")
#             print("\n")
#             print("\n")
#             print("app_name in sly_data: ",app_name)
#             print("\n")
#             print("\n")   
#         if sly_data.get("app_name", None) is None:
#             sly_data["app_name"] = app_name

#         restriction_applies: str = args.get("restriction_applies", None)
#         print("\n")
#         print("\n")
#         print("restriction_applies in args: ",restriction_applies)
#         print("\n")
#         print("\n")
#         if not restriction_applies:
#             print("No restriction applies provided. Trying to get it from sly_data")
#             restriction_applies = sly_data.get("restriction_applies")
#             print("\n")
#             print("\n")
#             print("restriction_applies in sly_data: ",restriction_applies)
#             print("\n")
#             print("\n")   
#         if sly_data.get("restriction_applies", None) is None:
#             sly_data["restriction_applies"] = restriction_applies

#         restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
#         print("\n")
#         print("\n")
#         print("restriction_on_cleaning in args: ",restriction_on_cleaning)
#         print("\n")
#         print("\n")
#         if not restriction_on_cleaning:
#             print("No restriction on cleaning provided. Trying to get it from sly_data")
#             restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
#             print("\n")
#             print("\n")
#             print("restriction_on_cleaning in sly_data: ",restriction_on_cleaning)
#             print("\n")
#             print("\n")   
#         if sly_data.get("restriction_on_cleaning", None) is None:
#             sly_data["restriction_on_cleaning"] = restriction_on_cleaning
        
#         escalation_on_cleaning: str = args.get("escalation_on_cleaning", None)
#         print("\n")
#         print("\n")
#         print("escalation_on_cleaning in args: ",escalation_on_cleaning)
#         print("\n")
#         print("\n")
#         if not escalation_on_cleaning:
#             print("No escalation on cleaning provided. Trying to get it from sly_data")
#             escalation_on_cleaning = sly_data.get("escalation_on_cleaning")
#             print("\n")
#             print("\n")
#             print("escalation_on_cleaning in sly_data: ",escalation_on_cleaning)
#             print("\n")
#             print("\n")   
#         if sly_data.get("escalation_on_cleaning", None) is None:
#             sly_data["escalation_on_cleaning"] = escalation_on_cleaning

#         user_response_to_recommendation: str = args.get("user_response_to_recommendation", None)
#         print("\n")
#         print("\n")
#         print("user_response_to_recommendation in args: ",user_response_to_recommendation)
#         print("\n")
#         print("\n")
#         if not user_response_to_recommendation:
#             print("No response to recommendation provided. Trying to get it from sly_data")
#             user_response_to_recommendation = sly_data.get("user_response_to_recommendation")
#             print("\n")
#             print("\n")
#             print("user_response_to_recommendation in sly_data: ",user_response_to_recommendation)
#             print("\n")
#             print("\n")   
#         if sly_data.get("user_response_to_recommendation", None) is None:
#             sly_data["user_response_to_recommendation"] = user_response_to_recommendation

#         compliance_response: str = args.get("compliance_response", None)
#         print("\n")
#         print("\n")
#         print("compliance_response in args: ",compliance_response)
#         print("\n")
#         print("\n")
#         if not compliance_response:
#             print("No user inquiry compliant provided. Trying to get it from sly_data")
#             compliance_response = sly_data.get("compliance_response")
#             print("\n")
#             print("\n")
#             print("compliance_response in sly_data: ",compliance_response)
#             print("\n")
#             print("\n")   
#         if sly_data.get("compliance_response", None) is None:
#             sly_data["compliance_response"] = compliance_response

#         if (user_response_to_recommendation == 'yes'): 
#             compliance_response = 'yes'

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)

##########
# class final_response(CodedTool):
#     """
#     Aircraft cleaning tracker.
#     """

#     # SHOP_1 = "Bob's Coffee Shop"
#     # SHOP_2 = "Henry's Fast Food"
#     # SHOP_3 = "Joe's Gas Station"
#     # SHOP_4 = "Jack's Liquor Store"
#     # SHOPS = [SHOP_1, SHOP_2, SHOP_3, SHOP_4]
#     # FIRST_ORDER_ID = {SHOP_1: 100, SHOP_2: 200, SHOP_3: 300, SHOP_4: 400}

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - app_name: the name of the app.
#             - restriction_on_cleaning: the details of the cleaning restriction.
#             - restriction_applies: the determinarion whether restriction applies to user inquiry.
#             - escalation_on_cleaning: the details of the escalation.
#             - user_response_to_recommendation: user response to cleaning recommendation. 

#         :param sly_data: a dictionary with the following keys:
#             - app_name: the name of the app.
#             - restriction_on_cleaning: the details of the cleaning restriction.
#             - restriction_applies: the determinarion whether restriction applies to user inquiry.
#             - escalation_on_cleaning: the details of the escalation.
#             - user_response_to_recommendation: user response to cleaning recommendation. 
#         """

#         print("\n")
#         print("\n")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&& THIS IS A CHECK THAT final_response Coded Tool has been called &&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
#         print("\n")
#         print("\n")

#         # :return:
#         #     In case of successful execution:
#         #         an order number as a string.
#         #     otherwise:
#         #         a string error message in the format:
#         #         "Error: <error message>"

#         print(">>>>>>>>>>>>>>>>>>> cleaning tracker >>>>>>>>>>>>>>>>>>")
#         # State and parameters of teh cleaning. 

#         app_name: str = args.get("app_name", None)
#         if not app_name:
#             print("No customer name provided. Trying to get it from sly_data")
#             app_name = sly_data.get("app_name")
#             print("app_name from sly_data:", app_name)
#         if sly_data.get("app_name", None) is None:
#             sly_data["app_name"] = app_name
        
#         restriction_on_cleaning: str = args.get("restriction_on_cleaning", None)
#         if not restriction_on_cleaning:
#             print("No restriction on cleaning provided. Trying to get it from sly_data")
#             restriction_on_cleaning = sly_data.get("restriction_on_cleaning")
#             print("restriction_on_cleaning from sly_data:", restriction_on_cleaning)
#         if sly_data.get("restriction_on_cleaning", None) is None:
#             sly_data["restriction_on_cleaning"] = restriction_on_cleaning

#         restriction_applies: str = args.get("restriction_applies", None)
#         if not restriction_applies:
#             print("No restriction applies cleaning provided. Trying to get it from sly_data")
#             restriction_applies = sly_data.get("restriction_applies")
#             print("restriction_applies from sly_data:", restriction_applies)
#         if sly_data.get("restriction_applies", None) is None:
#             sly_data["restriction_applies"] = restriction_applies

#         escalation_on_cleaning: str = args.get("escalation_on_cleaning", None)
#         if not escalation_on_cleaning:
#             print("No escalation on cleaning provided. Trying to get it from sly_data")
#             escalation_on_cleaning = sly_data.get("escalation_on_cleaning")
#             print("escalation_on_cleaning from sly_data:", escalation_on_cleaning)
#         if sly_data.get("escalation_on_cleaning", None) is None:
#             sly_data["escalation_on_cleaning"] = escalation_on_cleaning

#         user_response_to_recommendation: str = args.get("user_response_to_recommendation", None)
#         if not user_response_to_recommendation:
#             print("No response to recommendation provided. Trying to get it from sly_data")
#             user_response_to_recommendation = sly_data.get("user_response_to_recommendation")
#             print("user_response_to_recommendation from sly_data:", user_response_to_recommendation)
#         if sly_data.get("user_response_to_recommendation", None) is None:
#             sly_data["user_response_to_recommendation"] = user_response_to_recommendation

#         def build_final_response(
#             app_name: str,
#             restriction_applies: str,
#             restriction_on_cleaning: str,
#             escalation_on_cleaning: str,
#             user_response_to_recommendation: str,
#         ) -> ClearanceDict:

#             return {
#                 "app_name": app_name,
#                 "restriction_applies": restriction_applies,
#                 "restriction_on_cleaning": restriction_on_cleaning,
#                 "escalation_on_cleaning": escalation_on_cleaning,
#                 "user_response_to_recommendation": user_response_to_recommendation,
#             }

#         final_response = build_final_response(
#             app_name = app_name,
#             restriction_applies = restriction_applies,
#             restriction_on_cleaning = restriction_on_cleaning,
#             escalation_on_cleaning = escalation_on_cleaning,
#             user_response_to_recommendation = user_response_to_recommendation,
#         )

#         return final_response

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)

# class TrackerAPI(CodedTool):
#     """
#     Manages flight turnaround data by reading from or writing to a shared data store.
    
#     This API handles aircraft turnaround status information including flight details,
#     ground services, and various operational statuses during aircraft servicing.
#     """
    
#     # NO CONSTRUCTOR - configuration comes through args or sly_data
    
#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Tuple[Optional[str], ...]:
#         """
#         Process flight turnaround data by reading from args or sly_data, and updating sly_data.
        
#         Args:
#             args: Dictionary containing:
#                 - Field values to write to sly_data
#                 - '_config': Optional TrackerConfig for this invocation
#             sly_data: Shared data store containing current flight turnaround state
            
#         Returns:
#             Tuple containing values for all fields defined in config.return_fields
            
#         Note:
#             - If a field exists in args, it's written to sly_data (write mode)
#             - If a field doesn't exist in args, it's read from sly_data (read mode)
#         """
#         logger.info("=" * 60)
#         logger.info("TrackerAPI invoked")
#         logger.info("=" * 60)
        
#         # Get or create configuration
#         config = self._get_config(args, sly_data)
        
#         # Process all tracked fields
#         field_values = self._process_all_fields(args, sly_data, config)
        
#         # Log final state summary
#         self._log_data_summary(field_values, config)
        
#         # Return specific fields as defined in configuration
#         return self._build_return_tuple(field_values, config)
    
#     def _get_config(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> TrackerConfig:
#         """
#         Get configuration from args or sly_data, with lazy initialization.
        
#         Priority:
#         1. args['_config'] - Config passed for this specific invocation
#         2. sly_data['_tracker_config'] - Shared config initialized once per request
#         3. Default config - Create and store in sly_data for reuse
        
#         Args:
#             args: Input arguments
#             sly_data: Shared data store
            
#         Returns:
#             TrackerConfig instance
#         """
#         # Check if config passed in args for this specific invocation
#         if '_config' in args:
#             logger.debug("Using config from args")
#             return args['_config']
        
#         # Check if config already exists in sly_data (lazy initialization)
#         if '_tracker_config' not in sly_data:
#             logger.info("Initializing default config in sly_data")
#             sly_data['_tracker_config'] = self._create_default_config()
        
#         logger.debug("Using config from sly_data")
#         return sly_data['_tracker_config']
    
#     def _create_default_config(self) -> TrackerConfig:
#         """
#         Create the default configuration for flight turnaround tracking.
        
#         Returns:
#             Default TrackerConfig instance
#         """
#         return TrackerConfig(
#             tracked_fields=FLIGHT_TURNAROUND_TRACKED_FIELDS,
#             return_fields=FLIGHT_TURNAROUND_RETURN_FIELDS
#         )
    
#     def _process_all_fields(
#         self, 
#         args: Dict[str, Any], 
#         sly_data: Dict[str, Any],
#         config: TrackerConfig
#     ) -> Dict[str, Optional[str]]:
#         """
#         Process all tracked fields by checking args first, then falling back to sly_data.
        
#         Args:
#             args: Input arguments potentially containing new values
#             sly_data: Existing data store to read from or write to
#             config: Configuration defining which fields to track
            
#         Returns:
#             Dictionary mapping field names to their current values
#         """
#         field_values = {}
        
#         for field_name in config.tracked_fields:
#             # Skip internal config fields
#             if field_name.startswith('_'):
#                 continue
                
#             value, source = self._process_field(field_name, args, sly_data)
#             field_values[field_name] = value
            
#         return field_values
    
#     def _process_field(
#         self, 
#         field_name: str, 
#         args: Dict[str, Any], 
#         sly_data: Dict[str, Any]
#     ) -> Tuple[Optional[str], DataSource]:
#         """
#         Process a single field by attempting to read from args, then sly_data.
        
#         Args:
#             field_name: Name of the field to process
#             args: Input arguments (write mode if field exists here)
#             sly_data: Shared data store (read mode if field not in args)
            
#         Returns:
#             Tuple of (field_value, data_source)
#         """
#         # Check if value provided in args (write mode)
#         value = args.get(field_name)
        
#         if value is not None:
#             # Write mode: update sly_data with new value
#             sly_data[field_name] = value
#             logger.info(f"[WRITE] {field_name}: '{value}' (source: args)")
#             return value, DataSource.ARGS
        
#         # Read mode: try to get from sly_data
#         logger.debug(f"[READ] {field_name} not in args, checking sly_data")
#         value = sly_data.get(field_name)
        
#         if value is not None:
#             logger.info(f"[READ] {field_name}: '{value}' (source: sly_data)")
#             return value, DataSource.SLY_DATA
        
#         # Field not found in either location
#         logger.warning(f"[NOT FOUND] {field_name}: No value in args or sly_data")
#         return None, DataSource.NOT_FOUND
    
#     def _build_return_tuple(
#         self, 
#         field_values: Dict[str, Optional[str]],
#         config: TrackerConfig
#     ) -> Tuple[Optional[str], ...]:
#         """
#         Build return tuple from field values based on configured return fields.
        
#         Args:
#             field_values: Dictionary of all processed field values
#             config: Configuration defining which fields to return
            
#         Returns:
#             Tuple of values corresponding to config.return_fields
#         """
#         return_values = tuple(field_values.get(field) for field in config.return_fields)
#         logger.info(f"Returning {len(return_values)} fields: {config.return_fields}")
#         return return_values
    
#     def _log_data_summary(
#         self, 
#         field_values: Dict[str, Optional[str]],
#         config: TrackerConfig
#     ) -> None:
#         """
#         Log a summary of all field values for traceability.
        
#         Args:
#             field_values: Dictionary of all processed field values
#             config: Configuration defining tracked fields
#         """
#         logger.info("-" * 60)
#         logger.info("DATA SUMMARY")
#         logger.info("-" * 60)
        
#         for field_name in config.tracked_fields:
#             if field_name.startswith('_'):
#                 continue
                
#             value = field_values.get(field_name)
#             status = "SET" if value is not None else "UNSET"
#             return_marker = " [RETURN]" if field_name in config.return_fields else ""
#             logger.info(f"{field_name:40s} | {status:6s} | {value}{return_marker}")
        
#         logger.info("=" * 60)
    
#     async def async_invoke(
#         self, 
#         args: Dict[str, Any], 
#         sly_data: Dict[str, Any]
#     ) -> Tuple[Optional[str], ...]:
#         """
#         Asynchronous wrapper for invoke method.
        
#         Delegates to synchronous invoke since operations are fast and non-blocking.
        
#         Args:
#             args: Dictionary containing new field values to write to sly_data
#             sly_data: Shared data store containing current flight turnaround state
            
#         Returns:
#             Tuple containing values for all fields defined in config.return_fields
#         """
#         logger.debug("Async invoke called, delegating to synchronous invoke")
#         return self.invoke(args, sly_data)

#############################################################################
# Tracker API for all parameters in the aircraft turnaround agentic system  #
# This coded tool proceeds as follows:                                      #
#   - Check the value passed by LLM args                                    #
#   - Check the sly data to read the latest value of parameters             #
#   - Update parameters with the value from args when sly data is empty     #
#   - Return the parameter relevant to the agentic system                   #
# Given the large number of parameters, a separate version of this coded    #
# tool will be edited for each agents so that it aonly returns the relevant #
# one for the agent.                                                        #
#############################################################################

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Enum to track where data originated from"""
    ARGS = "args"
    SLY_DATA = "sly_data"
    NOT_FOUND = "not_found"


@dataclass
class TrackerConfig:
    """Configuration for TrackerAPI defining tracked and return fields"""
    tracked_fields: List[str]
    return_fields: List[str]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.tracked_fields:
            raise ValueError("tracked_fields cannot be empty")
        
        if not self.return_fields:
            raise ValueError("return_fields cannot be empty")
        
        # Validate that all return fields are in tracked fields
        invalid_fields = set(self.return_fields) - set(self.tracked_fields)
        if invalid_fields:
            raise ValueError(
                f"Return fields must be subset of tracked fields. "
                f"Invalid fields: {invalid_fields}"
            )


class TrackerAPI(CodedTool):
    """
    Manages flight turnaround data by reading from or writing to a shared data store.
    
    This API handles aircraft turnaround status information including flight details,
    ground services, and various operational statuses during aircraft servicing.
    """
    
    print("\n")
    print("\n")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&& TRACKER API CALLED &&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print("\n")
    print("\n")

    # NO CONSTRUCTOR - configuration comes through args or sly_data
    
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Tuple[Optional[str], ...]:
        """
        Process flight turnaround data by reading from args or sly_data, and updating sly_data.
        
        Args:
            args: Dictionary containing:
                - Field values to write to sly_data
                - '_config': Optional TrackerConfig for this invocation
            sly_data: Shared data store containing current flight turnaround state
            
        Returns:
            Tuple containing values for all fields defined in config.return_fields
            
        Note:
            - If a field exists in args, it's written to sly_data (write mode)
            - If a field doesn't exist in args, it's read from sly_data (read mode)
        """
        logger.info("=" * 60)
        logger.info("TrackerAPI invoked")
        logger.info("=" * 60)
        
        # Get or create configuration
        config = self._get_config(args, sly_data)
        
        # Process all tracked fields
        field_values = self._process_all_fields(args, sly_data, config)
        
        # Log final state summary
        self._log_data_summary(field_values, config)
        
        # Return specific fields as defined in configuration
        return self._build_return_tuple(field_values, config)
    
    def _get_config(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> TrackerConfig:
        """
        Get configuration from args or sly_data, with lazy initialization.
        
        Priority:
        1. args['_config'] - Config passed for this specific invocation
        2. sly_data['_tracker_config'] - Shared config initialized once per request
        3. Default config - Create and store in sly_data for reuse
        
        Args:
            args: Input arguments
            sly_data: Shared data store
            
        Returns:
            TrackerConfig instance
        """
        # Check if config passed in args for this specific invocation
        if '_config' in args:
            logger.debug("Using config from args")
            return args['_config']
        
        # Check if config already exists in sly_data (lazy initialization)
        if '_tracker_config' not in sly_data:
            logger.info("Initializing default config in sly_data")
            sly_data['_tracker_config'] = self._create_default_config()
        
        logger.debug("Using config from sly_data")
        return sly_data['_tracker_config']
    
    def _create_default_config(self) -> TrackerConfig:
        """
        Create the default configuration for flight turnaround tracking.
        
        Returns:
            Default TrackerConfig instance
        """
        return TrackerConfig(
            tracked_fields=FLIGHT_TURNAROUND_TRACKED_FIELDS,
            return_fields=FLIGHT_TURNAROUND_RETURN_FIELDS
        )
    
    def _process_all_fields(
        self, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any],
        config: TrackerConfig
    ) -> Dict[str, Optional[str]]:
        """
        Process all tracked fields by checking args first, then falling back to sly_data.
        
        Args:
            args: Input arguments potentially containing new values
            sly_data: Existing data store to read from or write to
            config: Configuration defining which fields to track
            
        Returns:
            Dictionary mapping field names to their current values
        """
        field_values = {}
        
        for field_name in config.tracked_fields:
            # Skip internal config fields
            if field_name.startswith('_'):
                continue
                
            value, source = self._process_field(field_name, args, sly_data)
            field_values[field_name] = value
            
        return field_values
    
    def _process_field(
        self, 
        field_name: str, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any]
    ) -> Tuple[Optional[str], DataSource]:
        """
        Process a single field by attempting to read from args, then sly_data.
        
        Args:
            field_name: Name of the field to process
            args: Input arguments (write mode if field exists here)
            sly_data: Shared data store (read mode if field not in args)
            
        Returns:
            Tuple of (field_value, data_source)
        """
        # Check if value provided in args (write mode)
        value = args.get(field_name)
        
        if value is not None:
            # Write mode: update sly_data with new value
            sly_data[field_name] = value
            logger.info(f"[WRITE] {field_name}: '{value}' (source: args)")
            return value, DataSource.ARGS
        
        # Read mode: try to get from sly_data
        logger.debug(f"[READ] {field_name} not in args, checking sly_data")
        value = sly_data.get(field_name)
        
        if value is not None:
            logger.info(f"[READ] {field_name}: '{value}' (source: sly_data)")
            return value, DataSource.SLY_DATA
        
        # Field not found in either location
        logger.warning(f"[NOT FOUND] {field_name}: No value in args or sly_data")
        return None, DataSource.NOT_FOUND
    
    def _build_return_tuple(
        self, 
        field_values: Dict[str, Optional[str]],
        config: TrackerConfig
    ) -> Tuple[Optional[str], ...]:
        """
        Build return tuple from field values based on configured return fields.
        
        Args:
            field_values: Dictionary of all processed field values
            config: Configuration defining which fields to return
            
        Returns:
            Tuple of values corresponding to config.return_fields
        """
        return_values = tuple(field_values.get(field) for field in config.return_fields)
        logger.info(f"Returning {len(return_values)} fields: {config.return_fields}")
        return return_values
    
    def _log_data_summary(
        self, 
        field_values: Dict[str, Optional[str]],
        config: TrackerConfig
    ) -> None:
        """
        Log a summary of all field values for traceability.
        
        Args:
            field_values: Dictionary of all processed field values
            config: Configuration defining tracked fields
        """
        logger.info("-" * 60)
        logger.info("DATA SUMMARY")
        logger.info("-" * 60)
        
        for field_name in config.tracked_fields:
            if field_name.startswith('_'):
                continue
                
            value = field_values.get(field_name)
            status = "SET" if value is not None else "UNSET"
            return_marker = " [RETURN]" if field_name in config.return_fields else ""
            logger.info(f"{field_name:40s} | {status:6s} | {value}{return_marker}")
        
        logger.info("=" * 60)
    
    async def async_invoke(
        self, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any]
    ) -> Tuple[Optional[str], ...]:
        """
        Asynchronous wrapper for invoke method.
        
        Delegates to synchronous invoke since operations are fast and non-blocking.
        
        Args:
            args: Dictionary containing new field values to write to sly_data
            sly_data: Shared data store containing current flight turnaround state
            
        Returns:
            Tuple containing values for all fields defined in config.return_fields
        """
        logger.debug("Async invoke called, delegating to synchronous invoke")
        return self.invoke(args, sly_data)

# =============================================================================
# Configuration Definitions
# =============================================================================

# Define tracked fields for flight turnaround operations
FLIGHT_TURNAROUND_TRACKED_FIELDS = [
    "user_inquiry",
    "app_name",
    "restriction_on_cleaning",
    "user_response_to_recommendation",
    "compliance_response", 
    "cleaning_procedure", 
    "escalation_response"
]                                                                                                                                                                                                                                                                                                    

# Define which fields should be returned from the API
FLIGHT_TURNAROUND_RETURN_FIELDS = [
    "user_inquiry",
    "app_name",
    "restriction_on_cleaning",
    "user_response_to_recommendation",
    "compliance_response", 
    "cleaning_procedure", 
    "escalation_response"
]

# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    # Example 1: Using default configuration (stored in sly_data)
    tracker = TrackerAPI()
    
    args = {
        "flight_number": "AA123",
        "passenger_disembarkation_status": "in_progress"
    }
    sly_data = {
        "crew_exit_status": "completed",
        "baggage_unload_status": "pending"
    }
    
    result = tracker.invoke(args, sly_data)
    print(f"Result: {result}")
    
    # Example 2: Using custom configuration passed in args
    custom_config = TrackerConfig(
        tracked_fields=["flight_number", "gate_id", "flight_status"],
        return_fields=["flight_status"]
    )
    
    custom_args = {
        "_config": custom_config,  # Pass config in args
        "flight_number": "UA456"
    }
    custom_sly_data = {
        "flight_status": "on_time"
    }
    
    result2 = tracker.invoke(custom_args, custom_sly_data)
    print(f"Custom Result: {result2}")