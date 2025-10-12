import tkinter as tk
from tkinter import ttk
import sqlite3
import google.generativeai as genai
import os
from random import shuffle

class Filter:
    def __init__(self):
        self.years = getField("Year")
        self.papers = getField("Paper")
        self.questions = getField("QuestionNumber")
        self.topics = getField("Topics")
        self.modules = getField("Module")
        self.difficulties = getField("Difficulty")

    def shuffleAll(self):
        l = self.years + self.papers + self.questions + self.topics + self.modules + self.difficulties
        shuffle(l)
        return l
    
def getField(fieldName: str) -> list[str]:
    #Field Names:   QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT DISTINCT {fieldName} FROM questions")

    unique_topics = [row[0] for row in cursor.fetchall()]
    return unique_topics

class SearchBar:
    def __init__(self):
        genai.configure(api_key=os.environ["GOOGLE_API_TOKEN_QUESTION"])
        
        self.model = genai.GenerationModel("gemini-2.5-flash", system_instruction=f"""
            This is a list of possible categories {f.shuffleAll()}, Given a query I want you to find all relevant categories.
            Example: Query: Give me all data between 2022 to 2024 Return: ["2022", "2023", "2024"], Query: give me a question relating to
            finite automata Return: ["Finite Automata", "Automaton Theory", "Automata Theory"]. You must return a list and only a list.
                                      """)
        
    def search(self, message):
        response = self.model.generate_content(message)
        
f = Filter()
print(f.shuffleAll())