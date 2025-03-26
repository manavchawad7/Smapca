import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import sqlite3
import io
import time
import qrcode
import threading
from Cryptodome.Cipher import AES 
import base64
import os
from ttkbootstrap import Style

# Object Detection Setup (unchanged)
classNames = []
classFile = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

configPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/Data/frozen_inference_graph.pb"

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

target_classes = ["bottle", "cell phone","scissors","eye glasses","keyboard","mouse"]

def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:  # Only process if the class is in the target list
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, objectInfo

class ShoppingCartApp:
    def __init__(self, root):
        self.root = root
        self.style = Style(theme='flatly')
        self.root.title("SMAPCA - Shopping Cart")
        self.root.geometry("800x480")
        
        # Initialize camera here so we can release it when going back to welcome screen
        self.cap = None
        
        # Show welcome screen first
        self.show_welcome_screen()

    def show_welcome_screen(self):
        # Clear any existing frames
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Welcome screen frame
        self.welcome_frame = ttk.Frame(self.root)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome label
        welcome_label = ttk.Label(
            self.welcome_frame,
            text="Welcome to SMAPCA",
            font=("Arial", 24, "bold"),
            foreground="#2c3e50"
        )
        welcome_label.pack(pady=(80, 40))
        
        # Start Shopping button
        start_button = ttk.Button(
            self.welcome_frame,
            text="Start Shopping",
            style="success.TButton",
            command=self.show_main_screen,
            width=15
        )
        start_button.pack(pady=20)
        
        # Logo at bottom
        try:
            logo_image = Image.open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/barcode/Logo3.png")
            logo_image = logo_image.resize((150, 60), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(self.welcome_frame, image=self.logo_photo)
            logo_label.pack(side=tk.BOTTOM, pady=20)
        except Exception as e:
            print(f"Error loading logo: {e}")
            logo_label = ttk.Label(self.welcome_frame, text="SMAPCA", font=("Arial", 12, "bold"))
            logo_label.pack(side=tk.BOTTOM, pady=20)

    def show_main_screen(self):
        # Clear welcome screen
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Initialize main shopping screen
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.conn = sqlite3.connect('barcode.db')
        self.cursor = self.conn.cursor()

        self.items = []
        self.quantities = []
        self.item_frames = {}
        self.last_scan_time = 0
        self.barcode_buffer = ""
        self.scanned_product = None
        self.scanned_product_data = None
        self.timer_started = False
        self.removal_mode = False
        self.detected_objects = set()

        # Header Frame (compact)
        self.header_frame = ttk.Frame(self.main_frame, padding=(5, 2))
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Smaller logo
        try:
            logo_image = Image.open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/barcode/Logo3.png")
            logo_image = logo_image.resize((100, 40), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label = ttk.Label(self.header_frame, image=self.logo_photo)
            self.logo_label.grid(row=0, column=0, padx=5, sticky="w")
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label = ttk.Label(self.header_frame, text="SMAPCA", font=("Arial", 12, "bold"))
            self.logo_label.grid(row=0, column=0, padx=5, sticky="w")

        # Smaller camera feed
        self.camera_frame = ttk.Frame(self.header_frame, borderwidth=1, relief="solid")
        self.camera_frame.grid(row=0, column=1, padx=5)
        
        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack(pady=1, padx=1)

        # Date/time (smaller font)
        self.datetime_label = ttk.Label(self.header_frame, font=("Arial", 8))
        self.datetime_label.grid(row=0, column=2, padx=5, sticky="e")
        self.update_datetime()

        # Title (smaller)
        self.title_label = ttk.Label(
            self.main_frame, 
            text="Shopping Cart", 
            font=("Arial", 14, "bold"),
            foreground="#2c3e50"
        )
        self.title_label.grid(row=1, column=0, sticky="n", pady=(0, 5))

        # Cart Items Frame (compact)
        self.cart_container = ttk.Frame(self.main_frame)
        self.cart_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 5))
        self.cart_container.grid_rowconfigure(0, weight=1)
        self.cart_container.grid_columnconfigure(0, weight=1)

        self.cart_canvas = tk.Canvas(
            self.cart_container, 
            bg=self.style.colors.get('bg'), 
            highlightthickness=0,
            width=600  # Add this to set a minimum width for the canvas
        )
        self.cart_canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self.cart_container, 
            orient=tk.VERTICAL, 
            command=self.cart_canvas.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.cart_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Cart frame inside canvas
        self.cart_frame = ttk.Frame(self.cart_canvas)
        self.cart_canvas.create_window((0, 0), window=self.cart_frame, anchor="nw", width=600)

        # Welcome message (smaller)
        self.welcome_label = ttk.Label(
            self.cart_frame, 
            text="Welcome to SMAPCA, start your smart journey", 
            font=("Arial", 12),
            foreground="#7f8c8d"
        )
        self.welcome_label.pack(pady=20, padx=100)

        # Bottom controls (compact)
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5), padx=10)
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        # Total amount (smaller)
        self.total_label = ttk.Label(
            self.bottom_frame, 
            text="Total: Rs. 0.00", 
            font=("Arial", 12, "bold"),
            foreground="#2c3e50"
        )
        self.total_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Buttons frame
        self.buttons_frame = ttk.Frame(self.bottom_frame)
        self.buttons_frame.grid(row=0, column=1, sticky="e")

        # End Shopping button
        self.end_button = ttk.Button(
            self.buttons_frame, 
            text="End Shopping", 
            style="danger.TButton",
            command=self.end_shopping,
            width=15
        )
        self.end_button.pack(side=tk.RIGHT, padx=7)

        # Remove Item button
        self.remove_button = ttk.Button(
            self.buttons_frame, 
            text="Remove", 
            style="danger.TButton",
            command=self.enable_removal_mode,
            width=8
        )
        self.remove_button.pack(side=tk.RIGHT, padx=7)

        # Pay Now button
        self.pay_button = ttk.Button(
            self.buttons_frame, 
            text="Pay Now", 
            style="success.TButton",
            command=self.process_payment,
            width=8
        )
        self.pay_button.pack(side=tk.RIGHT, padx=7)

        # Barcode scanning setup
        self.root.bind("<Key>", self.on_key_press)

        # Camera setup (smaller feed)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            exit()
        self.cap.set(3, 120)  # Smaller width
        self.cap.set(4, 90)   # Smaller height

        # Start updating the camera feed
        self.update_camera_feed()

        # Configure scroll region after UI is built
        self.cart_canvas.bind("<Configure>", lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all")))
        self.cart_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def end_shopping(self):
        # Clear all items from cart
        self.items = []
        self.quantities = []

        # Destroy all item frames
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        # Reset total
        self.total_label.config(text="Total: Rs. 0.00")

        # Release camera resources
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Close database connection
        if hasattr(self, 'conn'):
            self.conn.close()

        # Return to welcome screen
        self.show_welcome_screen()


    # [Rest of your existing methods remain exactly the same...]
    def _on_mousewheel(self, event):
        self.cart_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_datetime(self):
        if hasattr(self, 'datetime_label') and self.datetime_label.winfo_exists():
            self.datetime_label.config(text=datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
            self.root.after(1000, self.update_datetime)


    def on_key_press(self, event):
        current_time = time.time()
        if current_time - self.last_scan_time < 2:
            return

        if event.char:
            self.barcode_buffer += event.char

        if event.keysym == "Return":
            barcode = self.barcode_buffer.strip()
            self.barcode_buffer = ""
            self.last_scan_time = current_time

            if self.removal_mode:
                self.remove_item_from_cart(barcode)
            else:
                self.process_barcode(barcode)

    def process_barcode(self, barcode):
        if not barcode:
            return

        self.cursor.execute("SELECT Name, Price, Image, Description FROM Smapca WHERE barcode = ?", (barcode,))
        item = self.cursor.fetchone()

        if item:
            name, price, image_blob, desc = item
            self.scanned_product = name
            self.scanned_product_data = {"name": name, "price": price, "desc": desc, "image_blob": image_blob}
            self.timer_started = True
            self.start_timer()
        else:
            messagebox.showwarning("Not Found", "Item not found in the database.")

    def start_timer(self):
        if self.timer_started:
            self.root.after(5000, self.check_object_detection)

    def check_object_detection(self):
        if self.scanned_product:
            self.scanned_product = None
            self.scanned_product_data = None
            self.timer_started = False

    def is_object_in_database(self, object_name):
        self.cursor.execute("SELECT Name FROM Smapca WHERE Name = ?", (object_name,))
        return self.cursor.fetchone() is not None

    def update_camera_feed(self):
        if self.cap is None:
            return
        success, img = self.cap.read()
        if success:
            result, objectInfo = getObjects(img, 0.45, 0.2, objects=target_classes)

            for obj in objectInfo:
                if self.is_object_in_database(obj[1]):
                    if obj[1] not in self.detected_objects:
                        self.detected_objects.add(obj[1])
                        if not self.scanned_product:
                            messagebox.showinfo("Object Detected", f"{obj[1]} detected. Please scan its barcode.")

            if self.scanned_product and objectInfo:
                for obj in objectInfo:
                    if obj[1] == self.scanned_product:
                        self.add_item_to_cart(
                            self.scanned_product_data["name"],
                            self.scanned_product_data["price"],
                            self.scanned_product_data["desc"],
                            self.scanned_product_data["image_blob"]
                        )
                        self.scanned_product = None
                        self.scanned_product_data = None
                        self.timer_started = False
                        break

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (100, 75))  # Smaller display size
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)

            self.camera_label.config(image=img)
            self.camera_label.image = img

        self.root.after(10, self.update_camera_feed)

    def add_item_to_cart(self, name, price, desc, image_blob):
        for i, item in enumerate(self.items):
            if item["name"] == name:
                self.quantities[i] += 1
                self.update_total()
                return

        # Create the main item frame with padding
        frame = ttk.Frame(
            self.cart_frame, 
            padding=(10, 5, 10, 5),  # (left, top, right, bottom) padding inside frame
            relief="solid",
            borderwidth=1
        )
        frame.pack(pady=3, fill=tk.X, padx=40)

        # Image container with padding
        img_container = ttk.Frame(frame, padding=(0, 0, 50, 0))  # Right padding after image
        img_container.pack(side=tk.LEFT)

        try:
            image = Image.open(io.BytesIO(image_blob))
            image = image.resize((40, 40), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            img_label = ttk.Label(img_container, image=photo)
            img_label.image = photo
            img_label.pack(padx=5)  # Padding around image
        except Exception as e:
            print(f"Error loading image: {e}")
            img_label = ttk.Label(img_container, text="No Image")
            img_label.pack(padx=5)

        # Text frame with padding
        text_frame = ttk.Frame(frame, padding=(0, 0, 10, 0))  # Right padding after text
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Name label with bottom padding
        name_label = ttk.Label(
            text_frame, 
            text=name, 
            font=("Arial", 9, "bold"),
            foreground="#2c3e50"
        )
        name_label.pack(anchor='w', pady=(0, 3))  # Bottom padding

        # Description label
        desc_label = ttk.Label(
            text_frame, 
            text=desc, 
            font=("Arial", 8),
            foreground="#7f8c8d",
            wraplength=200,
            justify='left'
        )
        desc_label.pack(anchor='w')

        # Price and quantity frame with left padding
        price_qty_frame = ttk.Frame(frame, padding=(10, 0, 0, 0))  # Left padding before price
        price_qty_frame.pack(side=tk.RIGHT)

        price_label = ttk.Label(
            price_qty_frame, 
            text=f"Rs. {price:.2f}", 
            font=("Arial", 9),
            foreground="#2c3e50"
        )
        price_label.pack(anchor='e', pady=(0, 3))  # Bottom padding

        qty_label = ttk.Label(
            price_qty_frame, 
            text="Qty: 1", 
            font=("Arial", 9),
            foreground="#2c3e50"
        )
        qty_label.pack(anchor='e')

        self.items.append({"name": name, "price": price, "desc": desc, "image": image_blob, "frame": frame, "qty_label": qty_label})
        self.quantities.append(1)

        self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all"))
        self.update_total()

    def remove_item_from_cart(self, barcode):
        self.cursor.execute("SELECT Name FROM Smapca WHERE barcode = ?", (barcode,))
        item = self.cursor.fetchone()

        if not item:
            return

        name = item[0]

        for i, cart_item in enumerate(self.items):
            if cart_item["name"] == name:
                if self.quantities[i] > 1:
                    self.quantities[i] -= 1
                    cart_item["qty_label"].config(text=f"Qty: {self.quantities[i]}")
                else:
                    cart_item["frame"].destroy()
                    del self.items[i]
                    del self.quantities[i]

                self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all"))
                self.update_total()
                return

    def update_total(self):
        total = 0
        for i, item in enumerate(self.items):
            total += item["price"] * self.quantities[i]
            item["qty_label"].config(text=f"Qty: {self.quantities[i]}")

        self.total_label.config(text=f"Total: Rs. {total:.2f}")

        if len(self.items) == 0:
            self.welcome_label.pack(pady=20)
        else:
            self.welcome_label.pack_forget()

    def enable_removal_mode(self):
        self.removal_mode = True

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.geometry("120x40+400+300")  # Adjusted position
        popup.configure(bg="#e74c3c")

        label = ttk.Label(
            popup, 
            text="Scan item to remove", 
            foreground="white", 
            background="#e74c3c",
            font=("Arial", 8, "bold")  # Smaller font
        )
        label.pack(expand=True, fill=tk.BOTH)

        self.root.after(2000, popup.destroy)
        self.root.after(10000, self.disable_removal_mode)

    def disable_removal_mode(self):
        self.removal_mode = False

    AES_KEY = b"treegodbedoofchi"

    def encrypt_data(self, data):
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        encrypted_qr_data = base64.b64encode(nonce + tag + ciphertext).decode()
        return encrypted_qr_data

    def process_payment(self):
        if not self.items:
            messagebox.showinfo("Empty Cart", "Your cart is empty. Add items to proceed.")
            return

        cart_data = "Cart Details:\n"
        for item, qty in zip(self.items, self.quantities):
            cart_data += f"{item['name']} - Rs. {item['price']:.2f}\nQuantity- {qty}\n"
        cart_data += f"Total: Rs. {sum(item['price'] * qty for item, qty in zip(self.items, self.quantities)):.2f}\n"

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cart_data += f"Date & Time:{timestamp}"

        encrypted_cart_data = self.encrypt_data(cart_data)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,  # Increased box size for larger QR code
            border=2,
        )
        qr.add_data("SM01: "+encrypted_cart_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((250, 250), Image.LANCZOS)  # Larger QR code (250x250)

        # Create the QR code popup
        self.qr_window = tk.Toplevel(self.root)
        self.qr_window.title("Scan QR Code")
        self.qr_window.geometry("300x300")  # Larger window to accommodate bigger QR code
        self.qr_window.overrideredirect(True)  # Remove window decorations
        
        # Center the popup on screen
        window_width = 300
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.qr_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Display the QR code
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        qr_label = ttk.Label(self.qr_window, image=qr_img_tk)
        qr_label.image = qr_img_tk
        qr_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Add a countdown label
        self.qr_countdown = ttk.Label(
            self.qr_window, 
            text="Closing in 10 seconds...", 
            font=("Arial", 8),
            foreground="white",
            background="black"
        )
        self.qr_countdown.pack(side=tk.BOTTOM, pady=(0, 5))

        # Start the countdown
        self.qr_time_left = 10
        self.update_qr_countdown()

    def update_qr_countdown(self):
        if hasattr(self, 'qr_window') and self.qr_window.winfo_exists():
            self.qr_countdown.config(text=f"Closing in {self.qr_time_left} seconds...")
            self.qr_time_left -= 1
            
            if self.qr_time_left >= 0:
                self.root.after(1000, self.update_qr_countdown)
            else:
                self.qr_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ShoppingCartApp(root)
    root.mainloop()