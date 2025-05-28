import os
import sys
import shutil
import tempfile
import re

def rename_files_by_number(folder_path):
    # Define media file extensions to be renamed
    media_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    # Get all files in the folder
    all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Filter for only media files
    media_files = [f for f in all_files if os.path.splitext(f)[1].lower() in media_extensions]
    
    # Sort by creation time instead of filename
    media_files.sort(key=lambda f: os.path.getctime(os.path.join(folder_path, f)))
    
    # Limit to 20 files if needed
    if len(media_files) > 20:
        media_files = media_files[:20]
    
    print(f"Found {len(media_files)} media files to rename")
    
    # Create temp directory with unique name
    temp_dir = os.path.join(folder_path, f"temp_rename_{os.getpid()}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Rename files
        counter = 1
        for file in media_files:
            _, ext = os.path.splitext(file)
            new_name = f"{counter}{ext}"
            
            # Copy to temp
            shutil.copy2(os.path.join(folder_path, file), os.path.join(temp_dir, new_name))
            counter += 1
        
        # Delete originals
        for file in media_files:
            os.remove(os.path.join(folder_path, file))
        
        # Move renamed files back
        for file in os.listdir(temp_dir):
            shutil.move(os.path.join(temp_dir, file), os.path.join(folder_path, file))
            
        print(f"Renamed {len(media_files)} files successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        rename_files_by_number(sys.argv[1])
    else:
        folder_path = input("Enter folder path: ")
        rename_files_by_number(folder_path)