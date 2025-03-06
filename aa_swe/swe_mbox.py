#!/usr/bin/env python3
import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import mailbox
from glob import glob
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from tkinterhtml import HtmlFrame  # You need to install tkinterhtml

FONT_SIZE = 18  # Define a constant for the font size
FONT_SIZE_BODY = 28  # Define a constant for the email body font size

class EmailViewer:
    def __init__(self, root, mbox_file=None):
        self.root = root
        self.root.title("Email Viewer")
        
        # Define a font configuration
        self.font = ('TkDefaultFont', FONT_SIZE)
        
        # Create a PanedWindow for the left and right panels
        self.main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Create the left frame with a PanedWindow for trace and email subjects
        self.left_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.left_paned, weight=1)
        
        self.trace_frame = ttk.Frame(self.left_paned)
        self.email_frame = ttk.Frame(self.left_paned)
        self.left_paned.add(self.trace_frame, weight=1)
        self.left_paned.add(self.email_frame, weight=2)
        
        # Create a frame for the search box and listbox
        self.trace_search_frame = ttk.Frame(self.trace_frame)
        self.trace_search_frame.pack(fill=tk.X)

        # Create an entry widget for search input
        self.trace_search_entry = ttk.Entry(self.trace_search_frame, font=self.font)
        self.trace_search_entry.pack(fill=tk.X)
        self.trace_search_entry.bind('<KeyRelease>', self.filter_trace_files)

        # Create a listbox to display trace files
        self.trace_listbox = tk.Listbox(self.trace_frame, font=self.font)
        self.trace_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Create a listbox to display email subjects
        self.email_listbox = tk.Listbox(self.email_frame, font=self.font)
        self.email_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Create the right frame with a PanedWindow for email headers and content
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_paned, weight=3)
        
        self.header_frame = ttk.Frame(self.right_paned)
        self.content_frame = ttk.Frame(self.right_paned)
        
        # Add frames to the PanedWindow with weights
        self.right_paned.add(self.header_frame, weight=1)
        self.right_paned.add(self.content_frame, weight=3)
        
        # Create a text widget to display email headers with a small initial height
        self.email_headers = tk.Text(self.header_frame, wrap=tk.WORD, state='disabled', font=self.font, height=5)
        self.email_headers.pack(fill=tk.X)
        
        # Create a Text widget to display email content as plain text with a fixed-width font
        self.email_content = tk.Text(self.content_frame, wrap=tk.WORD, state='normal', font=('Courier', FONT_SIZE_BODY))
        self.email_content.pack(fill=tk.BOTH, expand=True)
        
        # Load trace files
        self.load_trace_files()
        
        # Bind the listbox selection events
        self.email_listbox.bind('<<ListboxSelect>>', self.display_email_content)
        self.trace_listbox.bind('<<ListboxSelect>>', self.load_selected_trace_file)
        # Load emails from the mbox file if provided
        if mbox_file:
            self.load_emails(mbox_file)
        
        
    def load_trace_files(self):
        self.all_trace_files = glob("*.trace.*")
        self.update_trace_listbox(self.all_trace_files)
    
    def update_trace_listbox(self, files):
        self.trace_listbox.delete(0, tk.END)
        for trace_file in files:
            self.trace_listbox.insert(tk.END, trace_file)
    
    def filter_trace_files(self, event):
        import re
        pattern = self.trace_search_entry.get()
        try:
            regex = re.compile(pattern)
            filtered_files = [f for f in self.all_trace_files if regex.search(f)]
            self.update_trace_listbox(filtered_files)
        except re.error:
            # If the regex is invalid, do not update the list
            pass
    
    def load_selected_trace_file(self, event):
        selected_index = self.trace_listbox.curselection()
        if not selected_index:
            return
        
        trace_file = self.trace_listbox.get(selected_index[0])
        self.load_emails(trace_file)
    
    def load_emails(self, mbox_file):
        self.mbox = mailbox.mbox(mbox_file)
        self.emails = list(self.mbox)
        
        self.email_listbox.delete(0, tk.END)
        selected_index = None
        for i, message in enumerate(self.emails):
            subject = message['subject'] or "No Subject"
            self.email_listbox.insert(tk.END, f"{i+1}: {subject}")
            
            # Check if the subject starts with "New ticket"
            if selected_index is None:
                if subject.lower().startswith("aa_ticket"):
                    selected_index = i + 2
                elif subject.lower().startswith("new ticket"):
                    selected_index = i
        # Select and display the first email with the subject starting with "New ticket"
        if selected_index is not None:
            self.email_listbox.selection_set(selected_index)
            self.email_listbox.see(selected_index)
            self.display_email_content(None)  # Call the method to display the email content
        
    def display_email_content(self, event):
        selected_index = self.email_listbox.curselection()
        if not selected_index:
            return
        
        index = selected_index[0]
        message = self.emails[index]
        
        # Display headers
        headers = f"From: {message['from']}\nTo: {message['to']}\nSubject: {message['subject']}\nDate: {message['date']}\n"
        self.email_headers.config(state='normal')
        self.email_headers.delete(1.0, tk.END)
        self.email_headers.insert(tk.END, headers)
        self.email_headers.config(state='disabled')
        
        # Display content as plain text
        content = message.get_payload(decode=True)
        if isinstance(content, bytes):
            content = content.decode(errors='ignore')
        
        self.email_content.config(state='normal')
        self.email_content.delete(1.0, tk.END)
        self.email_content.insert(tk.END, content)
        self.email_content.config(state='disabled')

def main():
    mbox_file = sys.argv[1] if len(sys.argv) == 2 else None
    
    root = tk.Tk()
    app = EmailViewer(root, mbox_file)
    root.mainloop()

if __name__ == "__main__":
    main()
