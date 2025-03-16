
# OCG  
**Open Candidate Generation for Narrative Recommendation**  

## Overview  
OCG (Open Candidate Generation) is a framework for narrative recommendation. It leverages AI search techniques and large language models (LLMs) to generate open domain candidates for narrative-driven recommendations based on LLMs.

## File Structure  

### **Folders**  
- **`AI_search_content/`** – Stores intermediate results generated during the narrative recommendation process.  
- **`logs/`** – Contains error logs from LLM operations.  
- **`prompt/`** – Includes all prompt templates used in the recommendation process.  
- **`span_example/`** – Stores annotated AI search results for comparison.  

### **Main Scripts**  
- **`AISearch.py`** – Implements the AI-powered search engine for content retrieval.  
- **`ask.py`** – A simple front-end entry point for user queries.  
- **`exp1.py`** – Temporary script (can be ignored for now).  
- **`file_database.py`** – Handles webpage reading and data extraction.  
- **`prompt.py`** – Loads prompt templates from the `prompt/` folder.  
- **`rec.py`** – Defines the narrative recommendation pipeline.  
- **`utils.py`** – Contains utility functions, including project path definitions.  
- **`config.py`** – Stores configuration settings such as API keys and file paths.  

## Usage  
1. Configure necessary settings in `config.py`.  
2. Run `rec.py` to execute the narrative recommendation pipeline.  

## Notes  
- Ensure all dependencies are installed before running the scripts.  
- Logs and intermediate results are stored in their respective folders for debugging and evaluation.  

---
