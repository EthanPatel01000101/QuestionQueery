import tkinter as tk
from tkinter import ttk
import sqlite3
import google.generativeai as genai
import os
from random import shuffle
import io
import requests
from PyPDF2 import PdfMerger
import datetime
import ast

class Filter:
    def __init__(self):
        self.years = getField("Year")
        self.papers = getField("Paper")
        self.questions = getField("QuestionNumber")
        self.topics = getField("Topics")
        self.modules = getField("Module")
        self.difficulties = getField("Difficulty")

    def shuffleAll(self):
        l = [item for item in (
            self.years + self.papers + self.questions +
            self.topics + self.modules + self.difficulties
        ) if item]
        shuffle(l)
        return list(set(l))


def getField(fieldName: str) -> list[str]:
    #Field Names:   QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT DISTINCT {fieldName} FROM questions")

    unique_topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return unique_topics

class SearchBar:
    def __init__(self, filter: Filter) -> None:
        api_key = os.environ.get("GOOGLE_API_TOKEN_QUESTION")
        if not api_key:
            raise EnvironmentError("Missing GOOGLE_API_TOKEN_QUESTION environment variable.")
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=f"""
            This is a list of possible categories {filter.shuffleAll()}, Given a query I want you to find all relevant categories.
            Example: Query: Give me all data between 2022 to 2024 Return: ["2022", "2023", "2024"], Query: give me a question relating to
            finite automata Return: ["Finite Automata", "Automaton Theory", "Automata Theory"]. You must return a list and only a list.
                                      """)
        
    def search(self, message: str) -> list[str]:
        response = self.model.generate_content(message)
        l = ast.literal_eval(response.text)
        if isinstance(l, list):
            return l
        else:
            return []

class ExportFiles:
    def __init__(self):
        pass
    def merge_pdfs(self, urls: list[str]) -> None:
        output_path = open(f"{datetime.datetime.now()}.pdf",  "x")
        output_path.close()
        merger = PdfMerger()

        for url in urls:
            response = requests.get(url)
            response.raise_for_status()  # make sure it worked
            file_bytes = io.BytesIO(response.content)
            merger.append(file_bytes)

        with open(output_path, "wb") as f_out:
            merger.write(f_out)

        merger.close()

def getLink(yearSat: int, paperNumber: int, questionNumber: int) -> str:
    return f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/y{yearSat}p{paperNumber}q{questionNumber}.pdf"

#Turn on the Filter for those topics
#Get all papers from each topic
#Remove ones that are not relevant (if all categories of a field is returned)
#Display images of each pdf with a checkbox in the top left corner (could be scrollable)
#Checkbox enabled by default
#Send the list of urls to merge_pdfs for ExportFiles