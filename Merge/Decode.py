from Cryptodome.Cipher import AES
import base64

AES_KEY = b"treegodbedoofchi"  # Use the same key as in Python script

def decrypt_data(encrypted_qr_data):
    decoded_data = base64.b64decode(encrypted_qr_data)
    nonce = decoded_data[:16]  # First 16 bytes are the nonce
    ciphertext = decoded_data[16:]

    cipher = AES.new(AES_KEY, AES.MODE_GCM, nonce=nonce)
    decrypted_data = cipher.decrypt(ciphertext)

    return decrypted_data.decode()

# Example usage:
qr_scanned_data = "Llv3VjHRJPBcu+KU1cYaGu/UFR6+6Z6RR9q2JR9JENs2fJzMwezLlMMI/DS+ZOwAgNJ2kqlge8UGl4qJTRo/IKHAEeDiGh1u7FqR2x/vJJ3IKGnsL1Un3hvoBFEt6mvmOjhNNp428QOe/hz+aJP3HcZqtZBXeZsEA4yZ6XdiwBeIQidwRD8P/HbNQRQ1UUkVRPCAoxYxooyLIhnTkPGFB7EvgHCBr4E="  # Replace with scanned QR code data
decrypted_text = decrypt_data(qr_scanned_data)
print("Decrypted Data:", decrypted_text)
