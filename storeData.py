import google.generativeai as genai
import os
import sqlite3

id = "y2022p2q10"

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
    else:
        return "Hard"
    
def getTopics(question_id: str) -> str:
    """
    Uses Google Generative AI to suggest 3 subtopic tags for a given question ID.
    """

    
    # Define your model — you can use 'gemini-1.5-pro' or similar
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=f"""
    You are an expert Cambridge Computer Science examiner.
    Your task is to classify past paper questions into precise subtopics.
    Analyze the content of the PDF in the following links and return the most relevant topic.
    You must ONLY return a string with the subtopic and nothing else.
    Always choose the most specific topic that fits the question
    Example valid outputs: "Automaton Theory", "Turing Machines", "Complexity Theory".
    """)

    prompt = f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/{question_id}.pdf"

    response = model.generate_content(prompt)

    print(response.text)
    # Clean up the output
    text = response.text.strip()

    return text

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
    topic = getTopics(id)

    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO questions
        (QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id, year, paper, questionNumber, topic, module, skill))

    conn.commit()
    conn.close()

genai.configure(api_key=os.environ["GOOGLE_API_TOKEN_QUESTION"])

id = ""
median = -2
while median != -1:
    median = int(input("Insert Median:      "))
    id = input("Insert ID:      ")
    packageData(id, median, "Algorithms 1")