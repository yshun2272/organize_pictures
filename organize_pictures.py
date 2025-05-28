import os
import subprocess
import shutil
import logging
from datetime import datetime

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('picture_organization.log'),
        logging.StreamHandler()
    ]
)

# Set the working directory to the Pictures folder
os.chdir(r"C:\\Users\\yshun\\OneDrive\\Pictures")

def check_exiftool():
    """Check if ExifTool is installed."""
    try:
        subprocess.run(['exiftool', '-ver'], capture_output=True, check=True)
        return True
    except:
        print("ERROR: ExifTool is required but not found. Please install ExifTool.")
        return False

def create_folder(folder_path):
    """Create a folder if it doesn't exist."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logging.info(f"Created folder: {folder_path}")
    return True

def parse_markdown_table(file_path):
    """Parse markdown table from pictures.md."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Skip header and separator rows
        rows = []
        for line in lines[2:]:  # Skip the header and separator
            if '|' not in line:
                continue
                
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) < 6:  # Should have empty, index, filename, date, tags, area, empty
                continue
                
            rows.append({
                "Index": cells[1],
                "Suggested File Name": cells[2],
                "Date": cells[3],
                "Tags": cells[4],
                "Area": cells[5]
            })
        
        return rows
    except Exception as e:
        logging.error(f"Error parsing markdown file: {str(e)}")
        return None

def organize_pictures():
    """Main function to organize pictures based on Markdown data."""
    print("Starting picture organization process...")
    
    # Check if ExifTool is available
    if not check_exiftool():
        return 1  # Error code 1: ExifTool not found
    
    # Get current directory
    pictures_dir = os.getcwd()
    markdown_file = os.path.join(pictures_dir, "pictures.md")
    
    # Check if Markdown file exists
    if not os.path.isfile(markdown_file):
        print(f"ERROR: Markdown file not found: {markdown_file}")
        return 2  # Error code 2: Markdown file not found
    
    try:
        # Parse markdown table
        file_data = parse_markdown_table(markdown_file)
        
        if not file_data:
            print("ERROR: Failed to parse markdown table.")
            return 3  # Error code 3: Failed to parse markdown
        
        # Process each file
        success_count = 0
        error_count = 0
        error_files = []
        
        total_files = len(file_data)
        print(f"Found {total_files} files to process")
        
        for row in file_data:
            try:
                # Get values from markdown
                index = row["Index"]
                suggested_name = row["Suggested File Name"].strip()
                area = row["Area"].strip()
                date = row["Date"]
                tags = row["Tags"]
                
                # Extract just the numeric part from index (in case it contains extension)
                if '.' in index:
                    index = index.split('.')[0]
                
                # Look for the index with any of the supported image extensions
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                current_file = None
                current_path = None
                
                for ext in image_extensions:
                    test_file = f"{index}{ext}"
                    test_path = test_file
                    if os.path.isfile(test_path):
                        current_file = test_file
                        current_path = test_path
                        break
                
                if not current_file:
                    print(f"ERROR: No image file found for index {index}")
                    error_count += 1
                    error_files.append(f"Index {index} - No matching image file found")
                    continue
                
                # Get the extension from the current file
                _, ext = os.path.splitext(current_file)
                
                # Ensure suggested name has the same extension
                if not suggested_name.lower().endswith(ext.lower()):
                    suggested_name += ext
                
                # Construct paths
                area_dir = area
                new_path = os.path.join(area_dir, suggested_name)
                
                print(f"Processing file {index}/{total_files}: {current_file} -> {suggested_name}")
                
                # Check if source file exists
                if not os.path.isfile(current_path):
                    print(f"ERROR: Source file not found: {current_path}")
                    error_count += 1
                    error_files.append(f"{current_file} - File not found")
                    continue
                
                # Create area folder
                create_folder(area_dir)
                
                # Check if destination file already exists
                if os.path.exists(new_path):
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    name_part, ext_part = os.path.splitext(suggested_name)
                    suggested_name = f"{name_part}_{timestamp}{ext_part}"
                    new_path = os.path.join(area_dir, suggested_name)
                
                # Apply metadata with ExifTool
                if date or tags:
                    exiftool_cmd = ["exiftool"]
                    if date:
                        exiftool_cmd.append(f"-DateTimeOriginal='{date}'")
                    if tags:
                        exiftool_cmd.append(f"-Keywords='{tags}'")
                    exiftool_cmd.append(current_path)
                    
                    try:
                        subprocess.run(exiftool_cmd, capture_output=True, check=True)
                        # Remove backup file created by ExifTool
                        backup_file = current_path + "_original"
                        if os.path.exists(backup_file):
                            os.remove(backup_file)
                    except:
                        print(f"WARNING: Metadata application failed for {current_file}")
                
                # Move and rename the file
                try:
                    shutil.move(current_path, new_path)
                    print(f"Successfully processed: {current_file} -> {area}/{suggested_name}")
                    success_count += 1
                except Exception as e:
                    print(f"ERROR: Failed to move file: {str(e)}")
                    error_count += 1
                    error_files.append(f"{current_file} - Failed to move file")
                
            except Exception as e:
                print(f"ERROR processing file {index}: {str(e)}")
                error_count += 1
                error_files.append(f"File {index} - Processing error")
        
        # Print summary
        print(f"\nPicture organization complete!")
        print(f"Successfully processed: {success_count} files")
        print(f"Errors: {error_count} files")
        
        # Print error details if any
        if error_count > 0:
            print("\nFiles with errors:")
            for err in error_files:
                print(f"- {err}")
            
            # Write errors to a file in the Pictures directory
            with open(error_file, 'w') as f:
                f.write(f"Picture organization errors - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for err in error_files:
                    f.write(f"- {err}\n")
            
            return 4  # Error code 4: Some files had errors
        
        return 0  # Success
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        return 5  # Error code 5: Unexpected error

if __name__ == "__main__":
    exit_code = organize_pictures()
    
    # For manual testing, wait before exiting
    if not os.environ.get('AUTOMATED_RUN'):
        input("\nPress Enter to exit...")
    
    # Return the exit code to the calling process
    exit(exit_code)