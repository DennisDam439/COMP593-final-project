import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import messagebox
import apod_desktop
from PIL import Image, ImageTk
import threading
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class APODApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Astronomy Picture of the Day Viewer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f0f0f0")

        # Main Frame
        self.main_frame = tk.Frame(root, bg="#ffffff", padx=10, pady=10, bd=1, relief="solid")
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Image Display
        self.image_label = tk.Label(self.main_frame, bg="#ffffff")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Explanation Text
        self.explanation_text = tk.Text(self.main_frame, wrap=tk.WORD, font=("Arial", 12), bg="#ffffff", fg="#333333", highlightthickness=0, bd=0, padx=5, pady=5)
        self.explanation_text.grid(row=1, column=0, sticky="nsew")

        # Configure row and column weights
        self.main_frame.grid_rowconfigure(0, weight=8)
        self.main_frame.grid_rowconfigure(1, weight=2)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Bottom Section
        self.bottom_section = tk.Frame(root, bg="#4f5d52", pady=10)
        self.bottom_section.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Select Image Label and Combobox
        self.select_image_label = tk.Label(self.bottom_section, text="Select Image:", bg="#4f5d52", font=("Arial", 12), fg="#f0f0f0")
        self.select_image_label.pack(side=tk.LEFT, padx=5)

        self.image_combobox = ttk.Combobox(self.bottom_section, font=("Arial", 12))
        self.image_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.image_combobox.bind("<<ComboboxSelected>>", self.selectimage)

        # Set Desktop Button
        self.set_bg_button = tk.Button(self.bottom_section, text="Set as Desktop", command=self.set_as_desktop, font=("Arial", 12), bg="#4f5d52", fg="#4f5d52", relief="flat", padx=5, pady=5)
        self.set_bg_button.pack(side=tk.LEFT, padx=5)

        self.select_date_label = tk.Label(self.bottom_section, text="Select Date:", bg="#4f5d52", font=("Arial", 12), fg="#f0f0f0")
        self.select_date_label.pack(side=tk.LEFT, padx=5)

        # Date Entry and Download Button
        self.date_selector = DateEntry(self.bottom_section, width=12, background='#4f5d52', foreground='#f0f0f0', borderwidth=2, font=("Arial", 12), date_pattern='yyyy-mm-dd')
        self.date_selector.pack(side=tk.LEFT, padx=5)

        self.download_button = tk.Button(self.bottom_section, text="Download", command=self.downloadImage, font=("Arial", 12), bg="#4f5d52", fg="#4f5d52", relief="flat", padx=5, pady=5)
        self.download_button.pack(side=tk.LEFT, padx=5)

        # Initially disable controls
        self.disable_controls()

        # Load data from the database
        self.loadfromDB()

    def loadfromDB(self):
        threading.Thread(target=self._loadfromDB).start()

    def _loadfromDB(self):
        try:
            apod_desktop.load_data() 
            self.root.after(0, self.enable_controls) 
        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", f"Data loading failed: {err}"))

    def disable_controls(self):
        self.image_combobox.config(state=tk.DISABLED)
        self.set_bg_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)

    def enable_controls(self):
        self.image_combobox.config(state=tk.NORMAL)
        self.set_bg_button.config(state=tk.NORMAL)
        self.download_button.config(state=tk.NORMAL)
        self.listloadimages()

    def listloadimages(self):
        try:
            titles = apod_desktop.get_all_apod_titles()
            if titles:
                self.image_combobox['values'] = titles
                logging.debug(f"Titles listed: {titles}")
            else:
                logging.warning("No titles found")
        except Exception as e:
            logging.error(f"Error listing image: {e}")

    def selectimage(self, event):
        selected_title = self.image_combobox.get()
        logging.debug(f"Selected title: {selected_title}")
        if selected_title:
            threading.Thread(target=self.loadimages_display, args=(selected_title,)).start()
        else:
            logging.warning("No title selected")

    def downloadImage(self):
        selected_date = self.date_selector.get_date()
        threading.Thread(target=self.cachedownload, args=(selected_date,)).start()

    def cachedownload(self, date):
        apod_id = apod_desktop.add_apod_to_cache(date)
        if apod_id != 0:
            self.root.after(0, self.listloadimages)
        else:
            self.root.after(0, lambda: messagebox.showerror("Error", " download failed"))

    def loadimages_display(self, title):
        try:
            apod_info = apod_desktop.get_apod_info_by_title(title)
            logging.debug(f"APOD Info for {title}: {apod_info}")
            if apod_info:
                file_path = apod_info.get('file_path')
                logging.debug(f"File path: {file_path}")
                if file_path and os.path.exists(file_path):
                    try:
                        image = Image.open(file_path)
                        width, height = self.image_label.winfo_width(), self.image_label.winfo_height()
                        if width == 0 or height == 0:
                            width, height = image.size
                        logging.debug(f"Image size: {width}x{height}")
                        image = image.resize((width, height), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self.root.after(0, self.updateImages, photo, apod_info.get('explanation'))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load image: {e}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Image file does not exist"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to get image information"))
        except Exception as e:
            logging.error(f"Error loading images: {e}")

    def updateImages(self, photo, explanation):
        if photo:
            self.image_label.config(image=photo)
            self.image_label.image = photo

        if explanation:
            self.explanation_text.config(state=tk.NORMAL)
            self.explanation_text.delete(1.0, tk.END)
            self.explanation_text.insert(tk.END, explanation)
            self.explanation_text.config(state=tk.DISABLED)

    def set_as_desktop(self):
        current_title = self.image_combobox.get()
        if current_title:
            try:
                apod_desktop.set_as_desktop(current_title)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set as desktop background: {e}")
        else:
            messagebox.showerror("Error", "No image selected to set as desktop background.")

if __name__ == "__main__":
    root = tk.Tk()
    app = APODApp(root)
    root.mainloop()
