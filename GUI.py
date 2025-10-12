import tkinter as tk
from tkinter import ttk
import sqlite3

class Filter:
    def __init__(self):
        self.years = getField("Year")
        self.papers = getField("Paper")
        self.questions = getField("QuestionNumber")
        self.topics = getField("Topics")
        self.modules = getField("Module")
        self.difficulties = getField("Difficulty")

def getField(fieldName: str) -> list[str]:
    #Field Names:   QuestionID, Year, Paper, QuestionNumber, Topics, Module, Difficulty
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT DISTINCT {fieldName} FROM questions")

    unique_topics = [row[0] for row in cursor.fetchall()]
    return unique_topics

# -------- GUI --------
class Application:
    def __init__(self, master):
        self.master = master
        self.master.title("Question Filter Dashboard")
        self.master.geometry("1536x864")
        self.master.configure(bg="#e9edf2")

        self.filter_data = Filter()
        self.font_main = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 16, "bold")

        # ---- Top Bar (leaves space for buttons) ----
        top_bar = tk.Frame(master, height=60, bg="#d7dce3")
        top_bar.pack(side="top", fill="x")

        ttk.Button(top_bar, text="Main Menu").pack(side="left", padx=15, pady=10)
        ttk.Button(top_bar, text="Export").pack(side="left", padx=15, pady=10)

        # ---- Main Content Area ----
        main_frame = tk.Frame(master, bg="#e9edf2")
        main_frame.pack(fill="both", expand=True)

        # Left placeholder (empty or future content)
        left_frame = tk.Frame(main_frame, bg="#f5f6fa", width=768)
        left_frame.pack(side="left", fill="both", expand=True)

        # Right half: Filter UI
        right_frame = tk.Frame(main_frame, bg="#ffffff", width=768, relief="ridge", bd=2)
        right_frame.pack(side="right", fill="both")
        right_frame.pack_propagate(False)  # Fix width to 768 px

        # ---- Title ----
        tk.Label(right_frame, text="Filters", font=self.title_font, bg="#ffffff").pack(pady=15)

        # ---- Filter Fields ----
        filter_area = tk.Frame(right_frame, bg="#ffffff")
        filter_area.pack(fill="x", padx=20, pady=10)

        self.create_dropdown(filter_area, "Year", self.filter_data.years, 0, 0)
        self.create_dropdown(filter_area, "Paper", self.filter_data.papers, 0, 1)
        self.create_dropdown(filter_area, "Question", self.filter_data.questions, 1, 0)
        self.create_dropdown(filter_area, "Topic", self.filter_data.topics, 1, 1)
        self.create_dropdown(filter_area, "Module", self.filter_data.modules, 2, 0)
        self.create_dropdown(filter_area, "Difficulty", self.filter_data.difficulties, 2, 1)

        # ---- Buttons ----
        button_frame = tk.Frame(right_frame, bg="#ffffff")
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="Apply Filters", command=self.apply_filters).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Clear", command=self.clear_filters).grid(row=0, column=1, padx=10)

        # ---- Results ----
        result_frame = tk.LabelFrame(right_frame, text="Results", font=self.font_main, bg="#ffffff", padx=10, pady=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.result_box = tk.Text(result_frame, wrap="word", font=("Consolas", 11))
        self.result_box.pack(fill="both", expand=True)

    # ---- Helper to make dropdowns ----
    def create_dropdown(self, parent, label_text, values, row, col):
        frame = tk.Frame(parent, bg="#ffffff")
        frame.grid(row=row, column=col, padx=15, pady=10, sticky="ew")

        tk.Label(frame, text=label_text, font=self.font_main, bg="#ffffff").pack(anchor="w")
        combo = ttk.Combobox(frame, values=values, state="readonly", font=self.font_main)
        combo.pack(fill="x", pady=5)
        setattr(self, f"{label_text.lower()}_combo", combo)

    # ---- Actions ----
    def apply_filters(self):
        year = self.year_combo.get()
        paper = self.paper_combo.get()
        question = self.question_combo.get()
        topic = self.topic_combo.get()
        module = self.module_combo.get()
        difficulty = self.difficulty_combo.get()

        filters = {
            "Year": year,
            "Paper": paper,
            "QuestionNumber": question,
            "Topics": topic,
            "Module": module,
            "Difficulty": difficulty
        }

        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", "Applied Filters:\n\n")
        for key, val in filters.items():
            if val:
                self.result_box.insert("end", f"{key}: {val}\n")

    def clear_filters(self):
        for combo_name in ["year", "paper", "question", "topic", "module", "difficulty"]:
            combo = getattr(self, f"{combo_name}_combo")
            combo.set("")
        self.result_box.delete("1.0", "end")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x400")
    app = Application(root)
    root.mainloop()