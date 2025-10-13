import tkinter as tk
from tkinter import ttk, filedialog
import sqlite3, os, io, requests, datetime, ast, threading, webbrowser
import google.generativeai as genai
from random import shuffle
from PyPDF2 import PdfMerger

class Filter:
    def __init__(self):
        # Initialize fields by getting unique values from the database
        self.years = self._getField("Year")
        self.papers = self._getField("Paper")
        self.questions = self._getField("QuestionNumber")
        self.topics = self._getField("Topics")
        self.modules = self._getField("Module")
        self.difficulties = self._getField("Difficulty")

    def _getField(self, fieldName: str) -> list[str]:
        # Field Names: QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty
        # This is the original getField function, renamed for clarity within the class
        conn = sqlite3.connect("questions.db")
        cursor = conn.cursor()

        cursor.execute(f"SELECT DISTINCT {fieldName} FROM questions")

        unique_topics = [row[0] for row in cursor.fetchall()]
        conn.close()
        # Convert list items to string, handling potential None/null values gracefully
        return [str(item) for item in unique_topics if item is not None]

    def shuffleAll(self):
        # Flattens and shuffles all filter categories for the LLM system prompt
        l = [item for item in (
            self.years + self.papers + self.questions +
            self.topics + self.modules + self.difficulties
        ) if item]
        shuffle(l)
        return list(set(l))

class SearchBar:
    def __init__(self, filter_instance: Filter) -> None:
        api_key = os.environ.get("GOOGLE_API_TOKEN_QUESTION")
        if not api_key:
            # Note: For real-world deployment, you'd handle this more robustly than just an EnvironmentError
            print("WARNING: Missing GOOGLE_API_TOKEN_QUESTION environment variable. Search functionality will be disabled.")
            self.model = None
            return

        genai.configure(api_key=api_key)

        # Create a detailed system instruction for the model
        system_instruction = f"""
            You are a precise but context-aware query parser for a university past paper database.

            Given a user's free-text query, return a Python list of the most relevant category names
            from the provided list: {filter_instance.shuffleAll()}.

            Your goal is to interpret the intent carefully:
            include only categories that are either an **exact match** or a **directly dependent subtopic or synonym**
            strongly tied to the query term in an academic or exam context.

            ### Rules
            1. **Exact Match First:** Always include exact matches to the query text.
            2. **Tight Semantic Proximity:** You may include a few directly related subtopics or synonyms,
            but only if they would normally appear *within the same lecture, question, or syllabus subsection*.
            - Example: “Number Theory” → may include “Modular Arithmetic” or “Chinese Remainder Theorem”.
            - Counterexample: “SQL” → exclude “Databases” unless the query explicitly mentions “database”.
            3. **No Broad Generalization:** Do not include parent topics or distantly related areas.
            4. **Range Handling:** For ranges (e.g. “2022 to 2024”), enumerate all items within that range if present in the list.
            5. **Output Format:** Your final output must be a valid Python list literal, with no extra text.

            ### Examples
            Query: "Give me all data between 2022 to 2024"
            Return: ["2022", "2023", "2024"]

            Query: "Questions on number theory"
            Return: ["Number Theory", "Modular Arithmetic", "Chinese Remainder Theorem"]

            Query: "Show SQL questions"
            Return: ["SQL"]

            Query: "Paper 1 Question 5 and automata"
            Return: ["Paper 1", "Question 5", "Finite Automata", "Automata Theory"]

            Query: "Anything on databases"
            Return: ["Databases", "SQL"]
            """

        self.model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
        
    def search(self, message: str) -> list[str]:
        if not self.model:
             print("Search model is not configured. Returning empty list.")
             return []
        try:
            response = self.model.generate_content(message)
            # Use ast.literal_eval for safe evaluation of the list string
            l = ast.literal_eval(response.text.strip())
            if isinstance(l, list):
                return l
            else:
                return []
        except Exception as e:
            print(f"Error in LLM search: {e}")
            print(f"LLM Response Text: {response.text if 'response' in locals() else 'N/A'}")
            return []

class ExportFiles:
    def __init__(self, master_path):
        self.master_path = master_path # Storing the path for writing the merged PDF

    def merge_pdfs(self, urls: list[str], filename: str) -> None:
        """Downloads PDFs from URLs and merges them into a single file."""
        output_filepath = os.path.join(self.master_path, filename)
        merger = PdfMerger()

        for url in urls:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()  # Check for bad status codes
                
                # Use a BytesIO object to hold the PDF content in memory
                file_bytes = io.BytesIO(response.content)
                merger.append(file_bytes)
                print(f"Successfully appended: {url}")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {url}: {e}")
                # Decide whether to continue or stop on failure
                continue

        if merger.inputs:
            with open(output_filepath, "wb") as f_out:
                merger.write(f_out)
            merger.close()
            print(f"PDFs merged successfully to: {output_filepath}")
        else:
            print("No valid PDFs were appended to the merger.")
            
def getLink(yearSat: int, paper: str, question: int) -> str:
    """Generates the assumed URL for the PDF based on parameters."""
    paperNumber = extract_trailing_number(paper)
    questionNumber = extract_trailing_number(question)
    return f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/y{yearSat}p{paperNumber}q{questionNumber}.pdf"

def extract_trailing_number(s):
    # Iterate backwards from the end of the string
    i = len(s) - 1
    while i >= 0 and s[i].isdigit():
        i -= 1
    # The number starts at position i + 1
    return s[i+1:]

def open_pdf(id: str):
    webbrowser.open(f"https://www.cl.cam.ac.uk/teaching/exams/pastpapers/{id}.pdf")
# --- New UI and Logic Integration ---

class PastPaperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Past Paper Search & Export")
        self.geometry("900x600")

        # --- Application State ---
        self.filter = Filter()
        self.search_bar_logic = SearchBar(self.filter)
        self.export_path = os.getcwd() # Default export path
        self.export_files_logic = ExportFiles(self.export_path)
        self.current_results = [] # Stores rows from DB (QuestionID, Year, Paper, QNum, Topics, Module, Difficulty, Link)
        self.selected_qids = set() # Stores QuestionID of currently selected items

        self.create_widgets()

    def create_widgets(self):
        # --- Main Layout Frames ---
        self.top_frame = ttk.Frame(self, padding="10")
        self.top_frame.pack(fill='x')
        
        self.middle_frame = ttk.Frame(self, padding="10")
        self.middle_frame.pack(fill='both', expand=True)

        # --- 1. Search Bar (Top) ---
        search_label = ttk.Label(self.top_frame, text="SEARCH BAR", font=("Arial", 12, "bold"))
        search_label.pack(fill='x')
        
        self.search_entry = ttk.Entry(self.top_frame, font=("Arial", 10))
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self.perform_search_thread())

        search_button = ttk.Button(self.top_frame, text="Search", command=self.perform_search_thread)
        search_button.pack(side='left')

        # --- 2. Filter Results / Question Display (Middle) ---
        
        # Canvas and Scrollbar for scrollable content (as suggested by the sketch)
        results_canvas = tk.Canvas(self.middle_frame)
        results_canvas.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(self.middle_frame, orient='vertical', command=results_canvas.yview)
        scrollbar.pack(side='right', fill='y')

        results_canvas.configure(yscrollcommand=scrollbar.set)
        results_canvas.bind('<Configure>', lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))

        self.results_frame = ttk.Frame(results_canvas)
        results_canvas.create_window((0, 0), window=self.results_frame, anchor='nw')
        
        # Initial call to populate the results area
        self.display_results() 

        # --- 3. Export File Panel (Right) ---
        export_panel = ttk.Frame(self.middle_frame, width=200, padding="10", relief=tk.RIDGE)
        export_panel.pack(side='right', fill='y')
        export_panel.pack_propagate(False) # Prevent frame from resizing to content

        export_label = ttk.Label(export_panel, text="EXPORT FILE", font=("Arial", 12, "bold"))
        export_label.pack(pady=(0, 10))
        
        # Checkboxes as per sketch (PDF and Filtered results are redundant in this implementation)
        # We'll use them to represent "Question" and "Solution" PDF flags (for a more realistic app)
        self.export_q_var = tk.BooleanVar(value=True) # Export Questions
        self.export_a_var = tk.BooleanVar(value=False) # Export Solutions (Placeholder)
        
        ttk.Separator(export_panel, orient='horizontal').pack(fill='x', pady=5)
        
        self.export_status = ttk.Label(export_panel, text="Ready.", wraplength=180)
        self.export_status.pack(pady=(10, 5))
        
        ttk.Button(export_panel, text="Choose Save Folder", command=self.choose_export_path).pack(fill='x', pady=5)

        export_button = ttk.Button(export_panel, text="Merge & Export", command=self.export_selected_pdfs_thread)
        export_button.pack(fill='x', pady=10)
        
        # Placeholder for export path display
        self.path_label = ttk.Label(export_panel, text=f"Path: {self.export_path}", wraplength=180)
        self.path_label.pack(pady=5)
        
        # Optional: Add a 'Select All' toggle (not in sketch, but helpful)
        ttk.Separator(export_panel, orient='horizontal').pack(fill='x', pady=5)
        self.select_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(export_panel, text="Select All/None", variable=self.select_all_var, command=self.toggle_select_all).pack(anchor='w', pady=5)

    def choose_export_path(self):
        """Opens a dialog to choose the folder for saving the merged PDF."""
        new_path = filedialog.askdirectory(initialdir=self.export_path)
        if new_path:
            self.export_path = new_path
            self.export_files_logic.master_path = new_path
            self.path_label.config(text=f"Path: {self.export_path}")
            
    def toggle_select_all(self):
        """Toggles selection for all displayed questions."""
        if self.select_all_var.get():
            self.selected_qids.update([q[0] for q in self.current_results])
        else:
            self.selected_qids.clear()
        
        # Update checkboxes visually
        self.display_results() 

    def perform_search_thread(self):
        """Runs the search logic in a separate thread to keep the UI responsive."""
        query = self.search_entry.get()
        if not query:
            self.export_status.config(text="Search box is empty.")
            return

        self.export_status.config(text=f"Searching for '{query}'...")
        
        # Start a thread for the blocking LLM call
        threading.Thread(target=self._search_logic, args=(query,), daemon=True).start()

    def _search_logic(self, query):
        """The core search logic using the LLM and DB."""
        # 1. LLM Search for relevant categories
        try:
            categories = self.search_bar_logic.search(query)
        except Exception as e:
            self.after(0, lambda: self.export_status.config(text=f"LLM Search failed: {e}"))
            return

        # 2. Database Query based on categories
        if not categories:
            self.after(0, lambda: self.export_status.config(text="LLM found no matching categories."))
            self.current_results = []
        else:
            self.after(0, lambda: self.export_status.config(text=f"Found categories: {', '.join(categories[:3])}..."))
            self.current_results = self.get_questions_by_categories(categories)
        
        # 3. Update UI
        self.after(0, self.display_results)
        self.after(0, lambda: self.export_status.config(text=f"Displaying {len(self.current_results)} results."))

    def get_questions_by_categories(self, categories: list[str]) -> list:
        """Queries the database to find questions matching any of the categories."""
        conn = sqlite3.connect("questions.db")
        cursor = conn.cursor()
        
        # We need to search across all relevant fields for a match
        fields = ["QuestionID", "Year", "Paper", "QuestionNumber", "Topics", "Module", "Difficulty"]
        
        # Build the WHERE clause: match any category in any relevant field
        # The Topics and Module fields are often stored as JSON strings/lists, so we use LIKE
        where_clauses = []
        for cat in categories:
            # Check for direct match in specific fields
            where_clauses.append(f"Year = '{cat}'")
            where_clauses.append(f"Paper = '{cat}'")
            where_clauses.append(f"QuestionNumber = '{cat}'")
            # Check for substring match in more complex fields
            where_clauses.append(f"Topics LIKE '%{cat}%'") 
            where_clauses.append(f"Module LIKE '%{cat}%'")
            where_clauses.append(f"Difficulty = '{cat}'")

        if not where_clauses:
            conn.close()
            return []

        where_sql = " OR ".join(where_clauses)
        
        # Select all fields and append a calculated Link
        select_fields = ", ".join(fields)
        # Note: getLink takes (Year, Paper, QuestionNumber) which are columns 1, 2, 3 in the result set
        query = f"SELECT {select_fields} FROM questions WHERE {where_sql}"
        
        try:
            cursor.execute(query)
            # Fetch all results and append the calculated link to each row
            results_with_link = []
            for row in cursor.fetchall():
                qid, year, paper, qnum = row[0], row[1], row[2], row[3]
                # Ensure year, paper, qnum are treated as integers for getLink
                link = getLink(int(year), paper, qnum) 
                results_with_link.append(row + (link,)) # Append the link to the tuple
            
            conn.close()
            return results_with_link
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.close()
            return []

    def display_results(self):
        """Clears and re-populates the results_frame with checkboxes and placeholders."""
        # Clear existing widgets
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # If no results, display a message
        if not self.current_results:
            ttk.Label(self.results_frame, text="No results found. Try a different search.").pack(padx=20, pady=20)
            return

        # Iterate through results and create an entry for each
        for i, row in enumerate(self.current_results):
            qid, year, paper, qnum, topics, module, difficulty, link = row
            
            # Use an inner frame for layout consistency (simulating the PDF box in the sketch)
            item_frame = ttk.Frame(self.results_frame, padding="5", relief=tk.GROOVE)
            item_frame.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky='nw')

            # Checkbox: linked to the qid
            is_selected = qid in self.selected_qids
            # Note: since we're redrawing, we need to bind the state of a new variable
            check_var = tk.BooleanVar(value=is_selected) 
            
            # The command function handles state change and updates the set
            def toggle_selection(qid=qid, var=check_var):
                if var.get():
                    self.selected_qids.add(qid)
                else:
                    self.selected_qids.discard(qid)
            
            check_button = ttk.Checkbutton(item_frame, variable=check_var, command=toggle_selection)
            check_button.pack(anchor='nw', padx=5, pady=5)
            
            # Question Info (Simulating a PDF preview)
            info_text = f"QID: {qid}\nYear: {year} | Paper: {paper} | Q: {qnum}\nTopics: {topics}"
            ttk.Label(item_frame, text=info_text, wraplength=300, justify=tk.LEFT).pack(padx=5, pady=5, anchor='w')
            
            info_text2 = f"Difficulty: {difficulty} | Module: {module}"
            ttk.Label(item_frame, text=info_text2, wraplength=300, justify=tk.LEFT).pack(padx=5, pady=5, anchor='w')
            # Placeholder for a PDF image preview (The sketch shows a box with a document icon)
            # In a real app, you would generate a thumbnail here. For this example, we use a simple label.
            # Create a small, generic icon/placeholder.
            icon_button = ttk.Button(item_frame, text="[PDF Preview]", command=lambda qid=qid: open_pdf(qid))
            icon_button.pack(padx=5, pady=5, anchor='w')
            # Reconfigure the scroll region after adding new widgets
            self.results_frame.update_idletasks()
            self.results_frame.master.config(scrollregion=self.results_frame.master.bbox("all"))

    def export_selected_pdfs_thread(self):
        """Initiates the PDF merge process in a separate thread."""
        if not self.selected_qids:
            self.export_status.config(text="No questions selected for export.")
            return

        # 1. Get the URLs for the selected Question IDs
        selected_rows = [row for row in self.current_results if row[0] in self.selected_qids]
        
        # The link is the last element in the row tuple (index 7)
        urls_to_merge = [row[7] for row in selected_rows] 

        if not urls_to_merge:
            self.export_status.config(text="No valid URLs found for selected questions.")
            return

        # Generate a filename
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Merged_Papers_{len(urls_to_merge)}_Q_{now}.pdf"

        self.export_status.config(text=f"Starting merge of {len(urls_to_merge)} PDFs...")
        
        # Start the merge process in a thread
        threading.Thread(target=self._export_logic, args=(urls_to_merge, filename), daemon=True).start()

    def _export_logic(self, urls: list[str], filename: str):
        """The core PDF merging logic."""
        try:
            # The ExportFiles class handles downloading and merging
            self.export_files_logic.merge_pdfs(urls, filename)
            
            # Update status back on the main thread
            self.after(0, lambda: self.export_status.config(text=f"Export successful! File: {filename}"))
        except Exception as e:
            # Update status back on the main thread
            self.after(0, lambda: self.export_status.config(text=f"Export failed: {e}"))

# --- Main Application Run ---
if __name__ == "__main__":
    # Note: Ensure you have a 'questions.db' file in the same directory 
    # with the appropriate schema (QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty)
    # and a valid GOOGLE_API_TOKEN_QUESTION environment variable set for the search bar to work.
    
    # Simple check for database file (optional but helpful)
    if not os.path.exists("questions.db"):
        print("Error: 'questions.db' not found. Search and display will be based on empty data.")
    
    app = PastPaperApp()
    app.mainloop()