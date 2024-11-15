# Blackboard Ultra to Canvas Import Fixer
This Python script addresses issues when importing Blackboard course export packages into Canvas. Its main purpose is to re-label Blackboard assignments, ensuring they import correctly as assignments rather than quizzes.

## Features
- Processes Blackboard export packages (ExportFile_*.zip) to ensure Blackboard Assignments are correctly recognized as assignments in Canvas.
- Bulk processing of multiple archive files.
- Option to add placeholders for omitted LTI content, ensuring visual representation.
- Option to Prettify XML for easier manual inspection.

## Requirements
- Python 3.x
- `lxml` library: Install with `pip install lxml`

## Installation
1. Clone the repository: `git clone <repository-url>`
2. Navigate to the project directory: `cd <repository-name>`
3. Install required libraries: `pip install -r requirements.txt`

## Usage
1. Place Blackboard course export files (`ExportFile_*.zip`) in the `IN` folder.
2. Run the script: `python main.py`
3. Processed files will be saved in the `OUT` folder with a `PATCHED_` prefix.

### Considerations
- **Input files remain unmodified:** The script generates new output files, which will occupy additional storage space equal to the size of the input files. Ensure you have sufficient disk space available before processing.  
- **Synchronous processing:** Files are processed one at a time. For large batches (e.g., thousands of files), the script may take a significant amount of time to complete.
- **Error handling not yet implemented:** The script may fail if it encounters a badly formatted export package. However, all files written to the output directory should be valid and properly processed.

### Options

#### Prettifies XML output for easier manual inspection.
- `-p` or `--pretty`: Makes XML output more readable by formatting it with proper indentation and spacing.

#### Adds placeholders for LTI content to ensure it is included during the Canvas import process.
- `-l` or `--lti`: Re-labels LTI content in the export package with placeholders so that the items are included during the Canvas import process. Without this option, LTI content is omitted entirely during import.
  - The placeholders allow the LTI content to be visually represented after migration, helping you identify where the links were originally placed.
  - **Note:** The migrated LTI links are not functional and will need to be deleted and recreated manually in Canvas.


### Example:
Run the script with both options:
```bash
python main.py -p -l
```

## Future Updates
- Implement asynchronous processing to reduce runtime for large batches.
- Enhance modularity for easier extension.
- Add error handling for malformed export packages.



