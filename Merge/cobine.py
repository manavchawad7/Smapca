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
import ttkbootstrap as tb

# Object Detection Setup
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
        self.root.title("SMAPCA - Shopping Cart")
        self.root.geometry("800x480")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.style = tb.Style(theme="cosmo")  # Apply a modern theme

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

        # Welcome Page
        self.show_welcome_page()

    def show_welcome_page(self):
        # Clear the current page
        for widget in self.root.winfo_children():
            widget.destroy()

        # Welcome Page Frame
        self.welcome_frame = ttk.Frame(self.root)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        # Welcome Message
        welcome_label = ttk.Label(self.welcome_frame, text="Welcome to SMAPCA", font=("Arial", 24, "bold"))
        welcome_label.pack(pady=50)

        # Start Shopping Button
        start_button = tb.Button(self.welcome_frame, text="Start Shopping", bootstyle="success", command=self.show_shopping_page)
        start_button.pack(pady=20)

    def show_shopping_page(self):
        # Clear the current page
        for widget in self.root.winfo_children():
            widget.destroy()

        # Header Frame
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(fill=tk.X)

        # Logo on the left
        try:
            logo_image = Image.open("C:/datda manav/Manav/College/SMAPCA/Object_Detection_Files/barcode/Logo3.png")
            logo_image = logo_image.resize((150, 60), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label = ttk.Label(self.header_frame, image=self.logo_photo)
            self.logo_label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label = ttk.Label(self.header_frame, text="SMAPCA", font=("Arial", 16, "bold"))
            self.logo_label.pack(side=tk.LEFT, padx=10)

        # Spacer to push the camera to the middle
        self.left_spacer = ttk.Frame(self.header_frame)
        self.left_spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Camera Feed in the middle of the header
        self.camera_frame = ttk.Frame(self.header_frame)
        self.camera_frame.pack(side=tk.LEFT, padx=10, pady=5)

        # Label to display the camera feed
        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack(pady=5, padx=5)

        # Spacer to push the date/time to the right
        self.right_spacer = ttk.Frame(self.header_frame)
        self.right_spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Date and Time on the right
        self.datetime_label = ttk.Label(self.header_frame, font=("Arial", 10))
        self.datetime_label.pack(side=tk.RIGHT, padx=10)
        self.update_datetime()

        # Title
        self.title_label = ttk.Label(self.root, text="Shopping Cart", font=("Arial", 18, "bold"))
        self.title_label.pack(pady=20)

        # Cart Items Frame with Scrollbar
        self.cart_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.cart_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10, padx=20)

        self.scrollbar = ttk.Scrollbar(self.cart_canvas, orient=tk.VERTICAL, command=self.cart_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.cart_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the cart items
        self.cart_frame = ttk.Frame(self.cart_canvas)
        self.cart_canvas.create_window((0, 0), window=self.cart_frame, anchor="nw")

        # Bind the canvas to the mousewheel for scrolling
        self.cart_canvas.bind("<Configure>", lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all")))
        self.cart_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Welcome message label
        self.welcome_label = ttk.Label(self.cart_frame, text="Welcome to SMAPCA, start your smart journey", font=("Arial", 12))
        self.welcome_label.pack(pady=20, padx=200)

        # Total Amount
        self.total_label = ttk.Label(self.root, text="Total Amount: Rs. 0.00", font=("Arial", 16, "bold"))
        self.total_label.pack(pady=10)

        # Pay Now Button, Cart Sign, and QR Code Frame
        self.pay_qr_frame = ttk.Frame(self.root)
        self.pay_qr_frame.pack(pady=20)

        # Cart Sign (🛒)
        #self.cart_sign_label = ttk.Label(self.pay_qr_frame, text="🛒", font=("Arial", 24))
        #self.cart_sign_label.pack(side=tk.LEFT, padx=10)

        # Pay Now Button
        self.pay_button = tb.Button(self.pay_qr_frame, text="Pay Now", bootstyle="success", command=self.process_payment)
        self.pay_button.pack(side=tk.LEFT, padx=10)

        # Remove Item Button
        self.remove_button = tb.Button(self.pay_qr_frame, text="Remove Item", bootstyle="danger", command=self.enable_removal_mode)
        self.remove_button.pack(side=tk.RIGHT, padx=10)

        # End Shopping Button
        self.end_shopping_button = tb.Button(self.pay_qr_frame, text="End Shopping", bootstyle="warning", command=self.end_shopping)
        self.end_shopping_button.pack(side=tk.RIGHT, padx=10)

        # Placeholder for QR code
        self.qr_label = ttk.Label(self.pay_qr_frame)
        self.qr_label.pack(side=tk.LEFT, padx=10)

        # Barcode scanning setup
        self.root.bind("<Key>", self.on_key_press)

        # Start object detection in a separate thread
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            exit()
        self.cap.set(3, 160)
        self.cap.set(4, 120)

        # Start updating the camera feed in the main window
        self.update_camera_feed()

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
            #messagebox.showinfo("Timeout", "Object not detected within 5 seconds.")
            self.scanned_product = None
            self.scanned_product_data = None
            self.timer_started = False

    def is_object_in_database(self, object_name):
        self.cursor.execute("SELECT Name FROM Smapca WHERE Name = ?", (object_name,))
        return self.cursor.fetchone() is not None

    def update_camera_feed(self):
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

            # Convert and update image if camera_label still exists
            if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (120, 90))
                img = Image.fromarray(img)
                img = ImageTk.PhotoImage(image=img)

                self.camera_label.config(image=img)
                self.camera_label.image = img

        # Continue only if camera_label exists (prevents errors on destroyed widgets)
        if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
            self.root.after(10, self.update_camera_feed)

    def add_item_to_cart(self, name, price, desc, image_blob):
        for i, item in enumerate(self.items):
            if item["name"] == name:
                self.quantities[i] += 1
                self.update_total()
                return

        frame = ttk.Frame(self.cart_frame, padding=10)
        frame.pack(pady=5, fill=tk.X, padx=80)

        try:
            image = Image.open(io.BytesIO(image_blob))
            image = image.resize((60, 60), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.pack(side=tk.LEFT, padx=80)
        except Exception as e:
            print(f"Error loading image: {e}")
            img_label = ttk.Label(frame, text="No Image")
            img_label.pack(side=tk.LEFT, padx=50)

        text_frame = ttk.Frame(frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_label = ttk.Label(text_frame, text=name, font=("Arial", 10, "bold"))
        name_label.pack(anchor='w')

        desc_label = ttk.Label(text_frame, text=desc, font=("Arial", 9), wraplength=300, justify='left')
        desc_label.pack(anchor='w', pady=2)

        price_qty_frame = ttk.Frame(frame)
        price_qty_frame.pack(side=tk.RIGHT, padx=100)

        price_label = ttk.Label(price_qty_frame, text=f"Rs. {price:.2f}", font=("Arial", 10))
        price_label.pack(anchor='e', pady=2)

        qty_label = ttk.Label(price_qty_frame, text="Qty: 1", font=("Arial", 10))
        qty_label.pack(anchor='e', pady=2)

        self.items.append({"name": name, "price": price, "desc": desc, "image": image_blob, "frame": frame, "qty_label": qty_label})
        self.quantities.append(1)

        # Update the scroll region of the canvas
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
                    (cart_item["qty_label"].config(text=f"Qty: {self.quantities[i]}"))
                else:
                    cart_item["frame"].destroy()
                    del self.items[i]
                    del self.quantities[i]

                self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all"))
                self.update_total()
                
                # ✅ Disable removal mode after successful removal
                self.disable_removal_mode()
                return
        
    def update_total(self):
        total = 0
        for i, item in enumerate(self.items):
            total += item["price"] * self.quantities[i]  # No .get(), use integer directly
            (item["qty_label"].config(text=f"Qty: {self.quantities[i]}"))  # Update quantity label

        (self.total_label.config(text=f"Total Amount: Rs. {total:.2f}"))

        if len(self.items) == 0:
            self.welcome_label.pack(pady=20)
        else:
            self.welcome_label.pack_forget()

    def enable_removal_mode(self):
        """Enables removal mode and shows a temporary notification."""
        self.removal_mode = True

        # Show a temporary notification (disappears after 2 seconds)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)  # No title bar
        popup.geometry("100x50+500+400")  # Adjust position
        popup.configure(bg="red")

        label = ttk.Label(popup, text="Scan item to remove", foreground="white", background="red", font=("Arial", 7, "bold"))
        label.pack(expand=True)

        # Close the popup after 2 seconds
        self.root.after(2000, popup.destroy)

        # Auto-disable removal mode after 5 seconds
        self.root.after(5000, self.disable_removal_mode)

    def disable_removal_mode(self):
        """Automatically exits removal mode after timeout."""
        self.removal_mode = False

    AES_KEY = b"treegodbedoofchi"  # Ensure this key is kept secret in the mobile app

    def encrypt_data(self, data):
        cipher = AES.new(self.AES_KEY, AES.MODE_GCM)  # Using AES-GCM mode
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())

        # Concatenate nonce + tag + ciphertext and encode as Base64
        encrypted_qr_data = base64.b64encode(nonce + tag + ciphertext).decode()
        return encrypted_qr_data

    def process_payment(self):
        if not self.items:
            messagebox.showinfo("Empty Cart", "Your cart is empty. Add items to proceed.")
            return

        # Convert cart details to string
        cart_data = "Cart Details:\n"
        for item, qty in zip(self.items, self.quantities):
            cart_data += f"{item['name']} - Rs. {item['price']:.2f}\nQuantity- {qty}\n"
        cart_data += f"Total: Rs. {sum(item['price'] * qty for item, qty in zip(self.items, self.quantities)):.2f}\n"

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cart_data += f"Date & Time:{timestamp}"

        # Encrypt the cart data
        encrypted_cart_data = self.encrypt_data(cart_data)

        # Generate QR code with encrypted data
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=2,
        )
        qr.add_data("SM01: "+encrypted_cart_data)
        qr.make(fit=True)

        # Convert QR to an image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((200, 200), Image.LANCZOS)

        # Create a new window to display the QR code
        self.qr_window = tk.Toplevel(self.root)
        self.qr_window.title("Scan QR Code")
        self.qr_window.geometry("250x250")
        self.qr_window.overrideredirect(True)  # Remove window decorations
        self.qr_window.geometry("+500+300")  # Position the window

        # Make the window semi-transparent
        self.qr_window.attributes("-alpha", 0.95)

        # Display the QR code in the new window
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        qr_label = ttk.Label(self.qr_window, image=qr_img_tk)
        qr_label.image = qr_img_tk
        qr_label.pack(pady=10, padx=10)

        # Countdown label
        self.countdown_label = ttk.Label(self.qr_window, text="Closing in 10 seconds...", font=("Arial", 8))
        self.countdown_label.pack()

        # Start countdown
        self.countdown_seconds = 10
        self.update_qr_countdown()

    def update_qr_countdown(self):
        if hasattr(self, 'countdown_label') and self.countdown_label.winfo_exists():
            self.countdown_label.config(text=f"Closing in {self.countdown_seconds} seconds...")
            self.countdown_seconds -= 1
            
            if self.countdown_seconds >= 0:
                self.root.after(1000, self.update_qr_countdown)
            else:
                if hasattr(self, 'qr_window') and self.qr_window.winfo_exists():
                    self.qr_window.destroy()

    def end_shopping(self):
        # Clear the cart
        self.items = []
        self.quantities = []

        # Return to the welcome page before calling update_total (which depends on widgets)
        self.show_welcome_page()

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")  # Apply the modern theme
    app = ShoppingCartApp(root)
    root.mainloop()