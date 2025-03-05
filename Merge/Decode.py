from Cryptodome.Cipher import AES
import base64

AES_KEY = b"treegodbedoofchi"  # Use the same key as in Python script

def decrypt_data(encrypted_qr_data):
    decoded_data = base64.b64decode(encrypted_qr_data)
    nonce = decoded_data[:16]  # First 16 bytes are the nonce
    ciphertext = decoded_data[16:]

    cipher = AES.new(AES_KEY, AES.MODE_EAX, nonce=nonce)
    decrypted_data = cipher.decrypt(ciphertext)

    return decrypted_data.decode()

# Example usage:
qr_scanned_data = "6sACCFd8Y7i1q9UB6yU+PB+RdFLSt2x5W/83tmea+mlnsjA5Fnco/2FVMk0RfAQHebcmZrXfgBcDTyAukMg2TtjFt/e39U377dRdLTub4WFXfe6aapB51wWHAswScA/KIvNKf/RYdPJ4laiLZLFVCb7ZiqUd"  # Replace with scanned QR code data
decrypted_text = decrypt_data(qr_scanned_data)
print("Decrypted Data:", decrypted_text)
