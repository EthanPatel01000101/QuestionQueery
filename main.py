import io
import requests
from PyPDF2 import PdfMerger
import datetime

def merge_pdfs(urls: list[str], output_path:str) -> None:
    _ = open(output_path,  "x")
    _.close()
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