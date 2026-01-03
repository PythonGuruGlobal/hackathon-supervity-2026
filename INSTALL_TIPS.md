# Faster Installation Tips

## Why Installation is Slow

The main culprit is **`chromadb`** - it has many dependencies and can take 5-10 minutes to install.

## Faster Installation Methods

### Option 1: Install in Stages (Recommended)

Install the heavy packages separately to see progress:

```powershell
# Install core packages first (fast)
pip install fastapi uvicorn pydantic requests

# Install LangChain packages (medium speed)
pip install langchain-core langchain langchain-community langchain-openai langchain-chroma langchain-text-splitters

# Install ChromaDB last (slowest - this is where it hangs)
pip install chromadb

# Install remaining packages
pip install python-multipart pydantic-settings ijson
```

### Option 2: Use Pre-built Wheels

Make sure pip is up to date to get pre-built wheels:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Option 3: Install ChromaDB with Specific Backend

ChromaDB can be faster if you specify the backend:

```powershell
pip install chromadb[server]
```

Or for client-only (lighter):

```powershell
pip install chromadb-client
```

### Option 4: Skip Optional Dependencies

If `ijson` is causing issues and you're not streaming large JSON files, you can remove it temporarily:

```powershell
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn langchain langchain-community langchain-chroma langchain-openai chromadb pydantic python-multipart requests langchain-text-splitters pydantic-settings
```

## Check What's Installing

To see what's taking time:

```powershell
pip install -r requirements.txt -v
```

The `-v` flag shows verbose output so you can see which package is hanging.

## Alternative: Use Docker (If Available)

If you have Docker, you can use a pre-built image that already has everything installed.

## Expected Installation Times

- FastAPI, Uvicorn, Pydantic: ~10 seconds
- LangChain packages: ~1-2 minutes
- ChromaDB: **5-10 minutes** (this is the bottleneck)
- Everything else: ~30 seconds

**Total: ~7-13 minutes** (mostly ChromaDB)

