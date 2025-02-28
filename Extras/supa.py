from supabase import create_client, Client
import os

# Supabase credentials
supabase_url = "https://kggqrbpgungvwnlonxny.supabase.co"
supabase_key = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtnZ3FyYnBndW5ndndubG9ueG55Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg2NDk4NjMsImV4cCI6MjA1NDIyNTg2M30.GJGP3rK1yPSs42vQw-4S7AlCUDVzdcf7YH5ZfvfSQkM")  # Make sure this environment variable is set

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Function to fetch data from 'Smapca' table
def fetch_data():
    response = supabase.table("Smapca").select("id, name, image, price, quantity, description").execute()

    if response.get("error"):
        print("Error fetching data:", response["error"])
        return None

    data = response["data"]
    print("Fetched data:", data)
    return data

# Call the function
fetch_data()
