import os
import sqlite3
import requests
from google import genai
from google.genai import types
import pathlib

def extractData(id: str) -> tuple[int, int, int]:
    '''
    Takes in an id and returns the year, paper, question number
    '''
    try:
        return (int(id[1:5]), int(id[6:7]), int(id[8:]))
    except:
        return (int(id[1:5]), int(id[6:8]), int(id[9:]))
    
def difficulty(median: int) -> str:
    '''
    Calculates the difficulty rating
    '''
    if median >= 17:
        return "Easy"
    elif median >= 13:
        return "Medium"
    elif median >= 0:
        return "Hard"
    else:
        return "None"
    
def downloadPdf(question_id):
    pdf_url = f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/{question_id}.pdf"
    print(f"Attempting to download: {pdf_url}")

    output_url = f"gemini.pdf"

    reponse = requests.get(pdf_url)
    with open(output_url, "wb") as f:
        f.write(reponse.content)

def uploadPdf(question_id: str) -> str:
    downloadPdf(question_id)

    path = pathlib.Path("gemini.pdf")
    if not path.exists():
        return f"Error: File not found at gemini.pdf"
    
    with genai.Client(api_key=api_key) as client:    
        uploaded_file = client.files.upload(
            file=path,
            config={'display_name': path.name}
        )        

        systemInstructionText = """
                You are an expert Cambridge Computer Science examiner.
                Your task is to classify the provided past paper question (a PDF) into a precise subtopic.
                Analyze the content of the PDF file and return the single most relevant and specific subtopic.
                You must ONLY return a string with the subtopic and nothing else.
                Always choose the most specific topic that fits the question.
                Example valid outputs: "Automaton Theory", "Turing Machines", "Complexity Theory".
            """
        config = types.GenerateContentConfig(
            system_instruction=systemInstructionText,
            temperature=0.2
        )
            
        prompt = "Analyze this past paper question and return the most specific subtopic."

        response = client.models.generate_content(
            model = "gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=config   
        )
            
        client.files.delete(name=uploaded_file.name)
        return response.text
    
def createTable():
    """Creates the questions table if it doesn't already exist."""
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            QuestionID TEXT PRIMARY KEY,
            Year TEXT,
            Paper TEXT,
            QuestionNumber TEXT,
            Topics TEXT,
            Module TEXT,
            Difficulty TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Table 'questions' ready.")

def packageData(id: str, median: int, module: str):
    extract = extractData(id)
    year, paper, questionNumber = extract[0], extract[1], extract[2]
    skill = difficulty(median)
    topic = uploadPdf(id)
    paper = "Paper " + str(paper)
    questionNumber = "Question " + str(questionNumber)

    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO questions
        (QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id, year, paper, questionNumber, topic, module, skill))

    conn.commit()
    conn.close()

api_key=os.environ["GOOGLE_API_TOKEN_QUESTION"]

id = ""
type = input("Insert Module:    ")
median = -2
while median != -3:
    median = int(input("Insert Median:      "))
    id = input("Insert ID:      ")
    packageData(id, median, type)