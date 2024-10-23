import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from PIL import Image
import requests
import io


#  ---------------------------------------------------------
def create_asset(username: str, file: UploadedFile) -> dict:
    """ Create an Asset """
    
    url = f"http://uba_service:8040/asset/create"

    # Read the file content in binary mode (reset file pointer to start of file)
    file.seek(0)
    file_content = file.read()
    
    files = {"file": (file.name, file_content, file.type)}
    data = {"username": username}
    
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()  # Raise an error for bad status codes

        return {"message": "success", "asset_id": response.json().get("asset_id")}
    except requests.exceptions.RequestException as e:
        return {"message": "error", "details": str(e)}
    

# ---------------------------------------------------------
def retrieve_asset(username: str, asset_id: str):
    """
    Retrieve file data by UUID and username from the FastAPI server.
    """
    url = f"http://uba_service:8040/asset/retrieve/{asset_id}/{username}"  
    
    try:
        # Sending a GET request to the asset retrieve endpoint
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:

            # Extract the filename from the response headers
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = "unknown"
            
            return {"message": "success", "image_data": response.content, "filename": filename}
        
        elif response.status_code == 404:
            error_details = response.json().get("detail", "File not found.")
            return {"message": "error", "details": error_details}
        else:
            return {"message": "error", "details": f"Received unexpected status code {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        return {"message": "error", "details": str(e)}


#  ---------------------------------------------------------
def create_asset_tab():
    # Image uploader widget
    uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
    
    # Create two columns
    col1, col2 = st.columns(2)

    with col1:

        # Display the uploaded image
        if uploaded_image is not None:
            # Open the image file
            image = Image.open(uploaded_image)

            # Display the image
            st.image(image, caption="Uploaded Image.", use_column_width=True)

    with col2:
        if uploaded_image is not None:
            filename = uploaded_image.name
            st.markdown(f"**Filename:** {filename}")

            # When the "Create Asset" button is clicked
            if st.button("Create Asset"):

                 # Text input for username
                username = st.text_input("Enter username", value="Alice")

                # Call create-asset
                result = create_asset(username=username, file=uploaded_image)

                if result.get("message") == "success":
                    asset_id = result.get("asset_id")
                    st.write(f"Asset created successfully!")
                    st.markdown(f"**Asset ID:** {asset_id}")
                else:
                    error_details = result.get("details", "No additional details provided.")
                    st.write(f"Failed to create asset. Error: {error_details}")


#  ---------------------------------------------------------
def retrieve_asset_tab():
    """ Retrieve an Asset """

    # Text input for asset ID
    asset_id = st.text_input("Enter Asset ID")

    # Text input for username
    username = st.text_input("Enter username", value="Alice", key="retrieve_username")

    # When the "Retrieve Asset" button is clicked
    if st.button("Retrieve Asset"):

        # Call retrieve-asset
        result = retrieve_asset(username=username, asset_id=asset_id)

        if result.get("message") == "success":

            col1, col2 = st.columns(2)

            image_bytes = result.get("image_data")
            filename = result.get("filename")

            try:
                # Use io.BytesIO to wrap the byte data
                image = Image.open(io.BytesIO(image_bytes))
                col1.image(image, caption=f"Retrieved Image: {filename}", use_column_width=True)
                col2.write(f"Filename: {filename}")
            except Exception as e:
                col1.write(f"Failed to display image. Error: {str(e)}")
        else:
            error_details = result.get("details", "No additional details provided.")
            print(f"Error: {result}")
            st.write(f"Failed to retrieve asset. Error: {error_details}")
    
    
#  ---------------------------------------------------------
#  ---------------------------------------------------------
# main entry point
if __name__ == "__main__":

    # Title of the app
    st.title("Create and Retreive Assets - Helper Tool")

    tab1, tab2 = st.tabs(["Create Asset", "Retrieve Asset"])

    with tab1:
        # Create Asset Tab
        create_asset_tab()

    with tab2:

        # Retrieve Asset Tab
        retrieve_asset_tab()


