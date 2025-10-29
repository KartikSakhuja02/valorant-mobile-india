"""
Interactive Region Calibrator
Click on each agent icon to find the correct positions
"""

from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import json

class RegionCalibrator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Icon Region Calibrator")
        
        self.image = None
        self.photo = None
        self.canvas = None
        self.points = []
        self.rectangles = []
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="📁 Load Screenshot", command=self.load_image, 
                 bg="#667eea", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔄 Reset", command=self.reset, 
                 bg="#f59e0b", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Save Config", command=self.save_config, 
                 bg="#10b981", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(self.root, 
                               text="INSTRUCTIONS: Click on each agent icon (10 total). Click top-left, then bottom-right.",
                               bg="#fef3c7", fg="#92400e", font=("Arial", 10), padx=10, pady=10)
        instructions.pack(side=tk.TOP, fill=tk.X)
        
        # Status
        self.status_label = tk.Label(self.root, text="Load a screenshot to begin", 
                                     font=("Arial", 10), fg="#6b7280")
        self.status_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Canvas
        self.canvas = tk.Canvas(self.root, bg="#e5e7eb")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Valorant Screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        
        if not file_path:
            return
        
        self.image_path = file_path
        self.image = Image.open(file_path)
        
        # Resize to fit screen
        screen_width = self.root.winfo_screenwidth() - 100
        screen_height = self.root.winfo_screenheight() - 200
        
        img_width, img_height = self.image.size
        scale = min(screen_width / img_width, screen_height / img_height, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        self.display_image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.scale = scale
        self.original_size = (img_width, img_height)
        
        self.photo = ImageTk.PhotoImage(self.display_image)
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        self.status_label.config(text=f"Loaded: {Path(file_path).name} ({img_width}x{img_height})")
        self.reset()
        
    def on_click(self, event):
        if self.image is None:
            return
        
        x, y = event.x, event.y
        self.points.append((x, y))
        
        # Draw point
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", outline="red")
        self.canvas.create_text(x+10, y-10, text=str(len(self.points)), fill="red", font=("Arial", 10, "bold"))
        
        # Every 2 points, draw a rectangle
        if len(self.points) % 2 == 0:
            x1, y1 = self.points[-2]
            x2, y2 = self.points[-1]
            
            # Ensure correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="lime", width=2)
            self.rectangles.append((x1, y1, x2, y2))
            
            slot_num = len(self.rectangles)
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2, 
                                   text=f"Slot {slot_num}", 
                                   fill="lime", font=("Arial", 12, "bold"))
            
            self.status_label.config(text=f"✅ Slot {slot_num} marked. Total: {slot_num}/10")
            
            if slot_num == 10:
                self.status_label.config(text="✅ All 10 slots marked! Click 'Save Config' to save.")
    
    def reset(self):
        self.points = []
        self.rectangles = []
        if self.image:
            self.photo = ImageTk.PhotoImage(self.display_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.status_label.config(text="Click on each agent icon (top-left, then bottom-right)")
    
    def save_config(self):
        if len(self.rectangles) != 10:
            messagebox.showwarning("Incomplete", f"Please mark all 10 agent icons. Currently: {len(self.rectangles)}/10")
            return
        
        # Convert to original image coordinates
        regions = []
        for i, (x1, y1, x2, y2) in enumerate(self.rectangles):
            # Scale back to original size
            orig_x1 = int(x1 / self.scale)
            orig_y1 = int(y1 / self.scale)
            orig_x2 = int(x2 / self.scale)
            orig_y2 = int(y2 / self.scale)
            
            regions.append({
                'slot': i,
                'x': orig_x1,
                'y': orig_y1,
                'width': orig_x2 - orig_x1,
                'height': orig_y2 - orig_y1
            })
        
        config = {
            'image_size': {
                'width': self.original_size[0],
                'height': self.original_size[1]
            },
            'regions': regions
        }
        
        # Save to file
        config_file = Path("agent_regions_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        messagebox.showinfo("Success", 
                           f"✅ Configuration saved to: {config_file}\n\n"
                           f"Now update template_agent_detector.py to use these regions.")
        
        # Print Python code to console
        print("\n" + "="*70)
        print("📋 COPY THIS CODE INTO template_agent_detector.py")
        print("="*70)
        print("\n# Paste this into the get_agent_icon_regions() method:\n")
        print(f"# Calibrated for {self.original_size[0]}x{self.original_size[1]} screenshots")
        print("regions = [")
        for r in regions:
            print(f"    {{'x': {r['x']}, 'y': {r['y']}, 'width': {r['width']}, 'height': {r['height']}, 'slot': {r['slot']}}},")
        print("]")
        print("\nreturn regions")
        print("="*70)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RegionCalibrator()
    app.run()
