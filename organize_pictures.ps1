# Create a log file path
$logFile = "$PSScriptRoot\rename_process.log"

# Step 1: Run the Python script to rename files
Write-Host "Starting picture organization workflow..."

# Run rename_files.py and capture its output
$pythonOutput = python "$PSScriptRoot\rename_files.py" "C:\Users\yshun\OneDrive\Pictures" 2>&1

# Save the output to the log file
$pythonOutput | Out-File -FilePath $logFile

# Extract and display only the simple summary lines we want
$pythonOutput | Where-Object { 
    $_ -match "Found \d+ files" -or 
    $_ -match "Renaming files in Pictures folder" -or
    $_ -match "Found \d+ media files to rename" -or 
    $_ -match "Renamed \d+ media files successfully" -or 
    $_ -match "Skipped \d+ non-media files"
} | ForEach-Object {
    Write-Host $_
}

# Function to run DeepSeek processing steps
function Run-DeepSeekProcessing {
    # Step 2: Copy Prompt to Clipboard 
    # First, clear the clipboard to prevent any accumulation
    Set-Clipboard -Value $null
    # Then, copy the content of organize_pictures.txt to clipboard
    $fileContent = Get-Content -Path "$PSScriptRoot\organize_pictures.txt" -Raw
    Set-Clipboard -Value $fileContent

    # Step 3: Open DeepSeek in default browser
    Start-Process "https://chat.deepseek.com/"

    # Step 4: Wait a moment for the page to load
    Start-Sleep -Seconds 3

    # Step 5: Send paste keyboard shortcut to paste the clipboard content
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^v")

    Write-Host "Upload your images to DeepSeek for analysis."
    Write-Host "Wait for DeepSeek to analyze the images and create a table."
    Write-Host "Save DeepSeek's output as 'pictures.md' in the current directory."

    # Pause and wait for user to confirm they're ready to continue
    $continue = Read-Host "Once you have saved pictures.md, type 'continue' to proceed with organizing pictures (or 'exit' to quit)"

    if ($continue -eq "exit") {
        Write-Host "Exiting script without organizing pictures."
        exit
    }
    
    if ($continue -ne "continue") {
        # If they didn't type continue or exit, assume they want to continue
        Write-Host "Proceeding with picture organization..."
    }
}

# Function to run the organize pictures Python script
function Run-OrganizePictures {
    # Set environment variable to indicate automated run
    $env:AUTOMATED_RUN = "true"
    
    # Run organize_pictures.py and capture exit code
    Write-Host "Running organize_pictures.py to organize the pictures..."
    $process = Start-Process -FilePath "python" -ArgumentList "$PSScriptRoot\organize_pictures.py" -Wait -PassThru -NoNewWindow
    
    # Return the exit code
    return $process.ExitCode
}

# Initial DeepSeek processing
Run-DeepSeekProcessing

# Maximum number of retries
$maxRetries = 2
$retryCount = 0
$success = $false

while (-not $success -and $retryCount -lt $maxRetries) {
    $exitCode = Run-OrganizePictures
    
    switch ($exitCode) {
        0 {
            Write-Host "Picture organization process completed successfully!" -ForegroundColor Green
            $success = $true
        }
        1 {
            Write-Host "ERROR: ExifTool is not installed or not found in PATH." -ForegroundColor Red
            Write-Host "Please install ExifTool and try again."
            exit 1  # Exit with error - can't continue without ExifTool
        }
        2 {
            Write-Host "ERROR: The pictures.md file was not found." -ForegroundColor Red
            $retry = Read-Host "Would you like to run the DeepSeek process again to create pictures.md? (y/n)"
            if ($retry -eq "y") {
                Run-DeepSeekProcessing
                $retryCount++
            } else {
                exit 2  # Exit with error
            }
        }
        3 {
            Write-Host "ERROR: Failed to parse the pictures.md file." -ForegroundColor Red
            $retry = Read-Host "Would you like to run the DeepSeek process again to create a new pictures.md? (y/n)"
            if ($retry -eq "y") {
                Run-DeepSeekProcessing
                $retryCount++
            } else {
                exit 3  # Exit with error
            }
        }
        4 {
            Write-Host "WARNING: Some files had errors during organization." -ForegroundColor Yellow
            if (Test-Path "picture_errors.txt") {
                Write-Host "Error details have been saved to picture_errors.txt"
                Get-Content "picture_errors.txt" | Select-Object -First 10  # Show first 10 errors
            }
            $retry = Read-Host "Would you like to run the DeepSeek process again to fix the errors? (y/n)"
            if ($retry -eq "y") {
                Run-DeepSeekProcessing
                $retryCount++
            } else {
                # This is a partial success, so we'll exit with success
                $success = $true
            }
        }
        default {
            Write-Host "An unexpected error occurred (Exit code: $exitCode)." -ForegroundColor Red
            if (Test-Path $logFile) {
                Write-Host "Check the log file for details: $logFile"
            }
            $retry = Read-Host "Would you like to run the DeepSeek process again? (y/n)"
            if ($retry -eq "y") {
                Run-DeepSeekProcessing
                $retryCount++
            } else {
                exit $exitCode  # Exit with the error code
            }
        }
    }
}

if ($success) {
    Write-Host "Picture organization workflow completed!" -ForegroundColor Green
} else {
    Write-Host "Picture organization workflow completed with errors after $maxRetries retries." -ForegroundColor Yellow
}