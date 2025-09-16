#!/usr/bin/env python3
"""
PNG to JPG Batch Converter
A Python script with GUI and command-line interface for batch converting PNG files to JPG format.
"""

import os
import sys
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
from pathlib import Path


class PNGtoJPGConverter:
    def __init__(self):
        self.quality = 95
        self.background_color = (255, 255, 255)  # White background for transparency
        
    def convert_single_file(self, png_path, output_dir=None, quality=None):
        """Convert a single PNG file to JPG"""
        try:
            png_path = Path(png_path)
            if not png_path.exists():
                raise FileNotFoundError(f"File not found: {png_path}")
            
            # Set output directory
            if output_dir is None:
                output_dir = png_path.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create output filename
            jpg_filename = png_path.stem + '.jpg'
            jpg_path = output_dir / jpg_filename
            
            # Open and convert image
            with Image.open(png_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', img.size, self.background_color)
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPG
                save_quality = quality if quality is not None else self.quality
                img.save(jpg_path, 'JPEG', quality=save_quality, optimize=True)
                
            return True, str(jpg_path)
            
        except Exception as e:
            return False, str(e)
    
    def batch_convert(self, input_dir, output_dir=None, quality=None, progress_callback=None):
        """Convert all PNG files in a directory"""
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise FileNotFoundError(f"Directory not found: {input_dir}")
        
        # Find all PNG files
        png_files = list(input_dir.rglob('*.png')) + list(input_dir.rglob('*.PNG'))
        
        if not png_files:
            return [], ["No PNG files found in the specified directory"]
        
        successful_conversions = []
        errors = []
        
        for i, png_file in enumerate(png_files):
            if progress_callback:
                progress_callback(i, len(png_files), str(png_file.name))
            
            success, result = self.convert_single_file(png_file, output_dir, quality)
            
            if success:
                successful_conversions.append(result)
            else:
                errors.append(f"{png_file.name}: {result}")
        
        if progress_callback:
            progress_callback(len(png_files), len(png_files), "Conversion complete!")
        
        return successful_conversions, errors


class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PNG to JPG Batch Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.converter = PNGtoJPGConverter()
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Input directory selection
        ttk.Label(main_frame, text="Input Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_input_dir).grid(row=0, column=2, padx=(10, 0), pady=5)
        
        # Output directory selection
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_output_dir).grid(row=1, column=2, padx=(10, 0), pady=5)
        
        # Quality setting
        ttk.Label(main_frame, text="JPG Quality (1-100):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.IntVar(value=95)
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=2, column=1, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        ttk.Scale(quality_frame, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(quality_frame, textvariable=self.quality_var, width=3).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Convert button
        self.convert_btn = ttk.Button(main_frame, text="Convert PNG to JPG", command=self.start_conversion)
        self.convert_btn.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=4, column=0, columnspan=3, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        # Results text area
        ttk.Label(main_frame, text="Results:").grid(row=6, column=0, sticky=(tk.W, tk.N), pady=(10, 0))
        
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=7, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.results_text = tk.Text(text_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
    def browse_input_dir(self):
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir_var.set(directory)
            # Set output directory to same as input if not set
            if not self.output_dir_var.get():
                self.output_dir_var.set(directory)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
    
    def update_progress(self, current, total, filename):
        progress = (current / total) * 100
        self.progress_bar['value'] = progress
        self.progress_var.set(f"Converting: {filename} ({current}/{total})")
        self.root.update_idletasks()
    
    def start_conversion(self):
        input_dir = self.input_dir_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        
        if not input_dir:
            messagebox.showerror("Error", "Please select an input directory")
            return
        
        if not os.path.exists(input_dir):
            messagebox.showerror("Error", "Input directory does not exist")
            return
        
        # Use input directory as output if not specified
        if not output_dir:
            output_dir = input_dir
        
        # Disable convert button during conversion
        self.convert_btn.config(state='disabled')
        self.results_text.delete(1.0, tk.END)
        
        # Start conversion in separate thread
        thread = threading.Thread(target=self.perform_conversion, args=(input_dir, output_dir))
        thread.start()
    
    def perform_conversion(self, input_dir, output_dir):
        try:
            successful, errors = self.converter.batch_convert(
                input_dir, 
                output_dir if output_dir != input_dir else None,
                self.quality_var.get(),
                self.update_progress
            )
            
            # Update UI in main thread
            self.root.after(0, self.conversion_complete, successful, errors)
            
        except Exception as e:
            self.root.after(0, self.conversion_error, str(e))
    
    def conversion_complete(self, successful, errors):
        self.convert_btn.config(state='normal')
        self.progress_bar['value'] = 0
        self.progress_var.set("Ready")
        
        # Display results
        result_text = f"Conversion Complete!\n\n"
        result_text += f"Successfully converted: {len(successful)} files\n"
        result_text += f"Errors: {len(errors)}\n\n"
        
        if successful:
            result_text += "Converted files:\n"
            for file_path in successful[:10]:  # Show first 10
                result_text += f"✓ {os.path.basename(file_path)}\n"
            if len(successful) > 10:
                result_text += f"... and {len(successful) - 10} more\n"
        
        if errors:
            result_text += "\nErrors:\n"
            for error in errors[:5]:  # Show first 5 errors
                result_text += f"✗ {error}\n"
            if len(errors) > 5:
                result_text += f"... and {len(errors) - 5} more errors\n"
        
        self.results_text.insert(tk.END, result_text)
        
        # Show summary message
        if successful and not errors:
            messagebox.showinfo("Success", f"Successfully converted {len(successful)} PNG files to JPG!")
        elif successful and errors:
            messagebox.showwarning("Partial Success", f"Converted {len(successful)} files with {len(errors)} errors. Check results for details.")
        else:
            messagebox.showerror("Error", "No files were converted. Check the results for error details.")
    
    def conversion_error(self, error_msg):
        self.convert_btn.config(state='normal')
        self.progress_bar['value'] = 0
        self.progress_var.set("Ready")
        messagebox.showerror("Error", f"Conversion failed: {error_msg}")


def main():
    parser = argparse.ArgumentParser(description='Batch convert PNG files to JPG format')
    parser.add_argument('input_dir', nargs='?', help='Input directory containing PNG files')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('-q', '--quality', type=int, default=95, help='JPG quality 1-100 (default: 95)')
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')
    
    args = parser.parse_args()
    
    # Launch GUI if requested or no arguments provided
    if args.gui or len(sys.argv) == 1:
        root = tk.Tk()
        app = ConverterGUI(root)
        root.mainloop()
        return
    
    # Command line conversion
    if not args.input_dir:
        parser.print_help()
        return
    
    converter = PNGtoJPGConverter()
    
    try:
        print(f"Converting PNG files in: {args.input_dir}")
        print(f"Output directory: {args.output or args.input_dir}")
        print(f"Quality: {args.quality}")
        print("-" * 50)
        
        successful, errors = converter.batch_convert(
            args.input_dir,
            args.output,
            args.quality,
            lambda current, total, filename: print(f"Converting ({current}/{total}): {filename}")
        )
        
        print("-" * 50)
        print(f"Conversion complete!")
        print(f"Successfully converted: {len(successful)} files")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  ✗ {error}")
        
        if successful:
            print(f"\nConverted files saved to: {args.output or args.input_dir}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()