from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import os

use_proxy = False  # Set to True to use proxy, False to use your host IP

if use_proxy:
    from seleniumwire import webdriver
    import getProxy
else:
    from selenium import webdriver

url = "https://pimeyes.com/en"

class PimeyesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pimeyes Face Search")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set icon if you have one
        # self.root.iconbitmap("icon.ico")
        
        # Variables
        self.image_path = None
        self.search_thread = None
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Pimeyes Face Search", 
                                font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # Image frame
        image_frame = tk.Frame(self.root)
        image_frame.pack(pady=20)
        
        # Image preview
        self.image_label = tk.Label(image_frame, text="No image selected", 
                                     font=("Arial", 12), fg="gray")
        self.image_label.pack()
        
        # Upload button
        self.upload_btn = tk.Button(self.root, text="📁 Select Image from Gallery", 
                                     command=self.select_image,
                                     font=("Arial", 12), bg="#4CAF50", fg="white",
                                     padx=20, pady=10, cursor="hand2")
        self.upload_btn.pack(pady=10)
        
        # Selected file label
        self.file_label = tk.Label(self.root, text="", font=("Arial", 9), fg="blue")
        self.file_label.pack()
        
        # Search button
        self.search_btn = tk.Button(self.root, text="🔍 Search on Pimeyes", 
                                     command=self.start_search,
                                     font=("Arial", 12), bg="#2196F3", fg="white",
                                     padx=20, pady=10, cursor="hand2", state="disabled")
        self.search_btn.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate', length=400)
        self.progress.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Ready", font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=5)
        
        # Results text area
        results_frame = tk.Frame(self.root)
        results_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        results_label = tk.Label(results_frame, text="Results:", font=("Arial", 12, "bold"))
        results_label.pack(anchor="w")
        
        self.results_text = tk.Text(results_frame, height=10, width=70, wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(self.results_text)
        scrollbar.pack(side="right", fill="y")
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)
        
        # URL label
        self.url_label = tk.Label(self.root, text="", font=("Arial", 9), fg="blue", cursor="hand2")
        self.url_label.pack(pady=5)
        self.url_label.bind("<Button-1>", self.open_url)
        
    def select_image(self):
        # Open file dialog to select image
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.image_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Selected: {filename}")
            self.search_btn.config(state="normal")
            
            # Try to show image preview
            try:
                from PIL import Image, ImageTk
                img = Image.open(file_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo, text="")
                self.image_label.image = photo  # Keep a reference
            except:
                self.image_label.config(text="Preview not available", fg="gray")
    
    def start_search(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please select an image first")
            return
        
        # Disable buttons during search
        self.upload_btn.config(state="disabled")
        self.search_btn.config(state="disabled")
        self.progress.start()
        self.status_label.config(text="Searching on Pimeyes...")
        self.results_text.delete(1.0, tk.END)
        
        # Start search in separate thread
        self.search_thread = threading.Thread(target=self.perform_search)
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def perform_search(self):
        results, result_url = self.upload_to_pimeyes(self.image_path)
        
        # Update GUI in main thread
        self.root.after(0, self.update_results, results, result_url)
    
    def upload_to_pimeyes(self, path):
        driver = None
        results = None
        currenturl = None
        
        try:
            if use_proxy:
                prox = getProxy.fetchsocks5()
                options = {
                    'proxy': {
                        'http': prox,
                        'https': prox,
                        'no_proxy': 'localhost,127.0.0.1'
                    }
                }
                driver = webdriver.Chrome(seleniumwire_options=options)
            else:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')  # Uncomment if you want no GUI
                driver = webdriver.Chrome(options=chrome_options)
            
            self.update_status("Opening Pimeyes...")
            driver.get(url)
            
            self.update_status("Clicking upload button...")
            upload_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="hero-section"]/div/div[1]/div/div/div[1]/button[2]'))
            )
            upload_button.click()
            
            self.update_status("Selecting image...")
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=file]'))
            )
            file_input.send_keys(os.path.abspath(path))
            
            self.update_status("Accepting agreements...")
            agreement1_xpath = '#app > div.wrapper.mobile-fullscreen-mode.mobile-full-height > div > div > div > div > div > div > div.permissions > div:nth-child(1) > label > input[type=checkbox]'
            agreement2_xpath = '#app > div.wrapper.mobile-fullscreen-mode.mobile-full-height > div > div > div > div > div > div > div.permissions > div:nth-child(2) > label > input[type=checkbox]'
            agreement3_xpath = '#app > div.wrapper.mobile-fullscreen-mode.mobile-full-height > div > div > div > div > div > div > div.permissions > div:nth-child(3) > label > input[type=checkbox]'
            submit_xpath = '#app > div.wrapper.mobile-fullscreen-mode.mobile-full-height > div > div > div > div > div > div > button'
            
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, agreement1_xpath))).click()
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, agreement2_xpath))).click()
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, agreement3_xpath))).click()
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_xpath))).click()
            
            self.update_status("Waiting for results...")
            time.sleep(5)
            currenturl = driver.current_url
            
            resultsXPATH = '//*[@id="results"]/div/div/div[3]/div/div/div[1]/div/div[1]/button/div/span/span'
            results = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, resultsXPATH))
            ).text
            
        except Exception as e:
            results = f"Error: {str(e)}"
            print(f"An exception occurred: {e}")
        
        finally:
            if driver:
                driver.quit()
        
        return results, currenturl
    
    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def update_results(self, results, result_url):
        # Stop progress bar
        self.progress.stop()
        
        # Re-enable buttons
        self.upload_btn.config(state="normal")
        self.search_btn.config(state="normal")
        
        if results:
            self.status_label.config(text="Search completed!")
            self.results_text.insert(1.0, results)
            
            if result_url:
                self.url_label.config(text=f"View full results: {result_url}")
        else:
            self.status_label.config(text="Search failed or no results found")
            self.results_text.insert(1.0, "No results found or an error occurred.")
        
        # Show completion message
        messagebox.showinfo("Search Complete", "Pimeyes search has completed!")
    
    def open_url(self, event):
        import webbrowser
        url_text = self.url_label.c_str()
        if url_text and "http" in url_text:
            url = url_text.replace("View full results: ", "")
            webbrowser.open(url)

def main():
    root = tk.Tk()
    app = PimeyesGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
