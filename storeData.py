import google.generativeai as genai
import os

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
    if median >= 15:
        return "Easy"
    elif median >= 10:
        return "Medium"
    else:
        return "Hard"
    
def getTopics(question_id: str) -> list[str]:
    """
    Uses Google Generative AI to suggest 3 subtopic tags for a given question ID.
    """

    
    # Define your model — you can use 'gemini-1.5-pro' or similar
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=f"""
    You are an expert Cambridge Computer Science examiner.
    Your task is to classify past paper questions into precise first-year subtopics.
    Always choose the most specific topic that fits the question
    Example valid outputs: "Automaton Theory", "Turing Machines", "Complexity Theory".
    You must ONLY return a string with the subtopic and nothing else.
    You will be given a sequence of unrelated pdf links, open the pdf and begin
    """)

    prompt = f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/{question_id}.pdf"

    response = model.generate_content(prompt)

    print(response.text)
    # Clean up the output
    text = response.text.strip()

    if text.count(" ") > 0:
        return "meow"
    else:
        return text  # make sure it's exactly 3

def packageData(id, median, module):
    extract = extractData(id)
    year, paper, questionNumber = extract[0], extract[1], extract[2]
    skill = difficulty(median)

genai.configure(api_key=os.environ["GOOGLE_API_TOKEN_QUESTION"])
print(getTopics(id))