import io
import requests
from PyPDF2 import PdfMerger

def merge_pdfs(urls, output_path):
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

url1 = getLink(2023, 8, 3)
url2 = getLink(2023, 1, 1)

merge_pdfs([url1, url2], "combined.pdf")