# NeuroForge - Phase 1: Local Proof of Concept (PoC)

This is Phase 1 of the NeuroForge project - a simple, local proof of concept that demonstrates the complete pipeline from data ingestion to semantic search.

## 🎯 Goal

Get a single piece of data from a source, process it, and retrieve it using semantic search. This is a bare-bones implementation focused on functionality over scale.

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Scrape Some Data

```bash
python scraper.py https://example.com
```

This will create a JSON file like `scraped_data_example_com.json` with the webpage content.

### 3. Build Vector Store

```bash
python vector_store.py
```

This will:
- Load all `scraped_data_*.json` files
- Split text into chunks
- Generate embeddings using sentence-transformers
- Create a FAISS index
- Save the index as `faiss_index` and metadata as `metadata.pkl`

### 4. Query Your Data

```bash
# Single query
python query.py "What is this website about?"

# Interactive mode
python query.py --interactive
```

## 📁 Project Structure

```
neuroforge/
├── requirements.txt      # Python dependencies
├── scraper.py           # Web scraper for HTML pages
├── vector_store.py      # Creates FAISS vector store
├── query.py            # Semantic search engine
├── README.md           # This file
└── scraped_data_*.json # Generated data files
```

## 🔧 Components

### 1. Scraper (`scraper.py`)

- Fetches HTML pages using `requests`
- Extracts and cleans text using `BeautifulSoup`
- Saves data to JSON files with metadata

**Usage:**
```bash
python scraper.py <url>
```

### 2. Vector Store (`vector_store.py`)

- Reads JSON files created by the scraper
- Splits text into overlapping chunks
- Generates embeddings using `sentence-transformers`
- Creates a FAISS index for fast similarity search

**Usage:**
```bash
python vector_store.py
```

### 3. Query Engine (`query.py`)

- Loads the FAISS index and metadata
- Generates embeddings for user queries
- Finds the most relevant text chunks
- Supports both single queries and interactive mode

**Usage:**
```bash
# Single query
python query.py "Your question here"

# Interactive mode
python query.py --interactive
```

## 🧪 Example Workflow

1. **Scrape a webpage:**
   ```bash
   python scraper.py https://en.wikipedia.org/wiki/Machine_learning
   ```

2. **Build the vector store:**
   ```bash
   python vector_store.py
   ```

3. **Query the data:**
   ```bash
   python query.py "What are the main types of machine learning?"
   ```

## 📊 What You'll Get

- **JSON files** with cleaned text and metadata
- **FAISS index** for fast similarity search
- **Semantic search** that finds relevant text chunks
- **Interactive querying** for exploring your data

## 🎉 Success Criteria

✅ You can scrape a webpage and save it locally  
✅ You can process the text and create embeddings  
✅ You can build a vector store with FAISS  
✅ You can query the data and get relevant results  

This is your first win! 🏆

## 🔮 Next Steps (Future Phases)

- **Phase 2**: Scale to multiple data sources
- **Phase 3**: Add Spark for distributed processing
- **Phase 4**: Deploy with Kubernetes
- **Phase 5**: Add advanced features (summarization, Q&A, etc.)

## 🐛 Troubleshooting

**"No module named 'faiss'"**
- Make sure you installed `faiss-cpu` (not `faiss`)

**"No JSON files found"**
- Run the scraper first to create some data files

**"Failed to load index"**
- Make sure you ran `vector_store.py` before querying

**Memory issues with large documents**
- The current chunk size is 500 words. You can modify this in `vector_store.py`

## 📝 Notes

- This is a **local PoC** - everything runs on your machine
- No external databases or cloud services required
- Uses `all-MiniLM-L6-v2` model for embeddings (fast and effective)
- FAISS index uses cosine similarity for search
- Text is chunked with 50-word overlap for better context 