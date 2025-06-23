import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Menu
import json
import os
import re
from mutagen import File
from mutagen.mp3 import HeaderNotFoundError
from mutagen.wave import InvalidChunk
from mutagen.flac import error

# Clean and sort keys for comparison
def clean_string(text):
    if text is None:
        return ""
    return re.sub(r'\W+\d+', ' ', str(text)).strip().lower()

# Search function with multiple keyword support
def search_by_keyword(file_data, keywords, key="title"):
    results = []
    cleaned_keywords = [clean_string(word) for word in keywords.split(",")]

    for file_info in file_data:
        if isinstance(file_info, dict):
            cleaned_value = clean_string(file_info.get(key, ""))
            if any(keyword in cleaned_value for keyword in cleaned_keywords):
                results.append(file_info)
    return results

# Load JSON file
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load JSON: {str(e)}")
        return []

# Create a new JSON file
def create_json():
    dir_path = filedialog.askdirectory(title="Select Music Directory")
    if not dir_path:
        return  # Exit if no directory is chosen
    
    acceptable_file_types = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.aiff', '.m4a', '.MPEG')
    file_data = []
    problem_files = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith(acceptable_file_types):
                file_path = os.path.join(root, file)

                try:
                    audio = File(file_path)

                    if audio:
                        title = audio.get("TIT2", file)
                        album = audio.get("TALB", "Unknown Album")
                        artist = audio.get("TPE1", "Unknown Artist")

                        file_info = {
                            "title": str(title),
                            "album": str(album),
                            "artist": str(artist),
                            "root": root,
                            "file_name": file
                        }

                        file_data.append(file_info)

                    else:
                        problem_files.append({"file_name": file, "root": root, "error": "No metadata found"})

                except (HeaderNotFoundError, InvalidChunk, error) as e:
                    problem_files.append({"file_name": file, "root": root, "error": str(e)})

                except OSError as os_error:
                    problem_files.append({"file_name": file, "root": root, "error": f"OSError: {str(os_error)}"})

                except Exception as e:
                    problem_files.append({"file_name": file, "root": root, "error": str(e)})

    # Save collected file data to JSON
    file_path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[("JSON Files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(file_data, file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Success", f"Created JSON file with {len(file_data)} items at {file_path}")

            if problem_files:
                problem_path = file_path.replace(".json", "_problems.json")
                with open(problem_path, 'w', encoding='utf-8') as pfile:
                    json.dump(problem_files, pfile, ensure_ascii=False, indent=4)
                messagebox.showinfo("Problem Files", f"Problematic files logged to {problem_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create JSON: {str(e)}")

# Search button callback
def search():
    keyword = keyword_entry.get()
    search_type = search_type_var.get().lower()
    results = search_by_keyword(file_data, keyword, key=search_type)
    for item in result_table.get_children():
        result_table.delete(item)
    total_results.set(f"Total Results: {len(results)}")
    if results:
        for index, result in enumerate(results, start=1):
            title = result.get("title", "Unknown")
            artist = result.get("artist", "Unknown")
            root_folder = result.get("root", "Unknown")
            result_table.insert("", "end", values=(index, title, artist, root_folder))
    else:
        messagebox.showinfo("No Results", "No matches found.")

# Load JSON button callback
def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        global file_data
        file_data = load_json(file_path)
        messagebox.showinfo("Success", f"Loaded {len(file_data)} items from {os.path.basename(file_path)}")

# Copy selected cell from the table
def copy_selected_cell():
    try:
        if selected_value:
            root.clipboard_clear()
            root.clipboard_append(str(selected_value))
    except Exception as e:
        print(f"Error copying cell: {e}")

def copy_selected_cell_ctrl(event=None):
    try:
        # Get the currently selected item and its values
        selected = result_table.focus()
        if selected:
            cell_values = result_table.item(selected, 'values')

            # Get the currently focused column (or default to the first one)
            col_id = result_table.identify_column(event.x) if event else "#1"
            column_index = int(col_id.replace("#", "")) - 1

            # Ensure the column index is valid and copy to clipboard
            if 0 <= column_index < len(cell_values):
                root.clipboard_clear()
                root.clipboard_append(str(cell_values[column_index]))
    except Exception as e:
        print(f"Error copying cell with Ctrl+C: {e}")

# Right-click context menu for copy
def show_context_menu(event):
    try:
        # Get the row and column where the right-click occurred
        row_id = result_table.identify_row(event.y)
        col_id = result_table.identify_column(event.x)

        # Check if a valid row and column were clicked
        if row_id and col_id:
            # Convert column ID from format "#n" to a zero-based index
            column_index = int(col_id.replace("#", "")) - 1

            # Select the row where the right-click occurred
            result_table.selection_set(row_id)
            result_table.focus(row_id)

            # Store the selected cell value in a global variable for copying
            global selected_value
            cell_values = result_table.item(row_id, 'values')
            if 0 <= column_index < len(cell_values):
                selected_value = cell_values[column_index]

            # Display the context menu at the mouse location
            context_menu.post(event.x_root, event.y_root)
    except Exception as e:
        print(f"Error showing context menu: {e}")
    finally:
        context_menu.grab_release()
                     
# Sorting function for headers
def sort_by_column(col, reverse=False):
    data = [(result_table.item(item, 'values')[col], item) for item in result_table.get_children()]
    data.sort(key=lambda x: (int(x[0]) if x[0].isdigit() else x[0].lower()), reverse=reverse)
    for index, (_, item) in enumerate(data):
        result_table.move(item, '', index)
    return not reverse

# Toggle sort order (ascending/descending)
def toggle_sort(col):
    global sort_order, current_sort_col

    # Reset the previous column heading if different
    if current_sort_col is not None and current_sort_col != col:
        column_name = result_table["columns"][current_sort_col]
        result_table.heading(column_name, text=column_name)

    # Toggle the sort order
    reverse = sort_order[col]
    sort_order[col] = not reverse
    current_sort_col = col

    sort_by_column(col, reverse)

    # Update the heading with arrow
    column_name = result_table["columns"][col]
    direction = "⬆" if not reverse else "⬇"
    result_table.heading(column_name, text=f"{column_name} {direction}")

# GUI setup
root = tk.Tk()
root.title("Music Search App")
root.geometry("850x450")
root.iconbitmap(os.path.abspath("music_search.ico"))

# Frame for top controls
top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=5, pady=5)

# Total results label
total_results = tk.StringVar(value="Total Results: 0")
total_results_label = tk.Label(root, textvariable=total_results)
total_results_label.pack(side="top")

# Dropdown for search type
search_type_var = tk.StringVar(value="Title")
search_type_label = tk.Label(root, text="Search By:")
search_type_label.pack()
search_type_dropdown = ttk.Combobox(root, textvariable=search_type_var, values=["Title", "Artist"], state="readonly")
search_type_dropdown.pack()

# Keyword entry
keyword_label = tk.Label(root, text="Keywords (comma-separated):")
keyword_label.pack()
keyword_entry = tk.Entry(root, width=50)
keyword_entry.pack()

# Create JSON button
create_button = tk.Button(top_frame, text="Create JSON", command=create_json)
create_button.pack(side="left", padx=5)

# Load JSON button
load_button = tk.Button(top_frame, text="Load JSON", command=browse_file)
load_button.pack(side="right", pady=5)

# Search button
search_button = tk.Button(root, text="Search", command=search)
search_button.pack(pady = 5, padx=5)

#search via enter
root.bind('<Return>', lambda event: search())

# Results table with scrollbar
table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True)

scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

result_table = ttk.Treeview(table_frame, columns=("Index", "Title", "Artist", "Folder"), show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
result_table.heading("Index", text="Index", command=lambda: toggle_sort(0))
result_table.heading("Title", text="Title", command=lambda: toggle_sort(1))
result_table.heading("Artist", text="Artist", command=lambda: toggle_sort(2))
result_table.heading("Folder", text="Folder", command=lambda: toggle_sort(3))

scroll_y.config(command=result_table.yview)
scroll_x.config(command=result_table.xview)

scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
result_table.pack(fill="both", expand=True)

# Context menu for copy
context_menu = Menu(root, tearoff=0)
context_menu.add_command(label="Copy", command=copy_selected_cell)
result_table.bind("<Button-3>", show_context_menu)

# Enable cell copy with right-click or Ctrl+C
result_table.bind("<Control-c>", copy_selected_cell_ctrl) 

# Highlight the clicked cell and allow copying
def on_cell_click(event):
    selected = result_table.identify('item', event.x, event.y)
    if selected:
        column = result_table.identify_column(event.x)
        column_index = int(column[1:]) - 1
        result_table.selection_remove(result_table.selection())
        result_table.selection_add(selected)
        copy_selected_cell(event)

# Store the sort order for each column
current_sort_col = None
sort_order = {0: False, 1: False, 2: False, 3: False}

root.mainloop()
