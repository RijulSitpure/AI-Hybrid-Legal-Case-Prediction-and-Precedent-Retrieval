# PBL: Legal Case Prediction & Precedent System

A comprehensive system for predicting legal case outcomes and retrieving relevant precedents using hybrid retrieval methods (BM25 + Semantic Search). Built with a Python/Flask backend and a modern React TypeScript frontend.

## 🎯 Overview

This project leverages the Indian Supreme Court judgment dataset to:
- **Predict** case outcomes (Allowed/Dismissed) using machine learning
- **Retrieve** relevant precedent cases using hybrid retrieval (keyword + semantic)
- **Analyze** legal text and compare multiple retrieval methods
- **Schedule** case reviews intelligently based on predictions

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Dataset](#dataset)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- 🎯 **Case Outcome Prediction** - Random Forest model trained on 18,000+ Indian Supreme Court cases
- 🔍 **Hybrid Precedent Retrieval** - Combines BM25 (keyword-based) and Semantic Search (embedding-based)
- 📊 **Comparative Analysis** - Compare different retrieval methods side-by-side
- 📄 **Text Analysis** - Extract and analyze legal text from uploaded documents
- 📅 **Smart Scheduler** - Intelligent case scheduling based on prediction confidence
- 🎨 **Modern UI** - React TypeScript frontend with Tailwind CSS
- 🔌 **RESTful API** - Well-documented Flask API with CORS support
- 📈 **PDF Processing** - Extract text from PDF judgments for full-text analysis

## 📂 Project Structure

```
PBL/
├── backend/                          # Python/Flask API backend
│   ├── app.py                       # Main Flask application
│   ├── legal_prediction_system.py   # Model training script
│   ├── siamese_lstm.py              # Siamese LSTM architecture
│   ├── contextual_retrieval.py      # Retrieval logic
│   ├── smart_scheduler.py           # Scheduling system
│   ├── build_indian_dataset.py      # Dataset building (with PDF extraction)
│   ├── build_faiss_index.py         # FAISS index construction
│   ├── requirements.txt             # Python dependencies
│   ├── indian_data/                 # Indian Supreme Court dataset
│   │   ├── train.jsonl
│   │   └── test.jsonl
│   └── models/                      # Trained models directory
├── frontend/                         # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx                 # Main app component
│   │   ├── components/             # React components
│   │   ├── lib/                    # Utilities and API client
│   │   ├── pages/                  # Page components
│   │   └── index.css               # Styles
│   ├── package.json
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.ts          # Tailwind CSS config
│   └── tsconfig.json
├── models/                           # Trained model files
│   ├── faiss_index/                # FAISS semantic search index
│   ├── word2vec_model.model        # Word2Vec embeddings
│   └── *.pkl                       # Pickled models
├── data/                             # Raw training data
│   ├── train.jsonl
│   └── test.jsonl
├── .gitignore
├── README.md
└── venv/                             # Python virtual environment
```

## 🔧 Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** with npm or bun
- **macOS/Linux/Windows** (tested on macOS)
- **4GB+ RAM** recommended for model training
- **AWS credentials** (unsigned access for S3 public bucket)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/PBL.git
cd PBL
```

### 2. Backend Setup

```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

**Key dependencies:**
- Flask: Web framework
- pandas: Data processing
- scikit-learn: Machine learning models
- pdfplumber: PDF text extraction
- boto3: AWS S3 access
- pydantic: Data validation
- FAISS: Semantic search indexing
- Word2Vec: Text embeddings

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies using npm (or bun)
npm install
# OR
bun install
```

### 4. Download/Build Models

The system expects pre-built FAISS indexes and models. To build them from scratch:

```bash
cd backend

# Build the dataset (downloads from S3, extracts PDFs, cleans text)
python build_indian_dataset.py

# Build FAISS semantic search index
python build_faiss_index.py

# Train the prediction model
python legal_prediction_system.py
```

> Note: These steps download data from S3 public bucket and may take significant time/bandwidth.

## 🚀 Quick Start

### Run Backend API

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python app.py
```

API runs on `http://localhost:5000`

### Run Frontend Development Server

```bash
cd frontend
npm run dev
# OR
bun run dev
```

Frontend runs on `http://localhost:5173`

### Access the Application

Open browser to `http://localhost:5173` and the frontend will automatically connect to the backend API.

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
python -m flask run --reload

# Run tests
python -m pytest

# Lint code
pylint *.py
```

### Frontend Development

```bash
cd frontend

# Dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint TypeScript
npm run lint
```

## 📡 API Documentation

### Endpoints

#### 1. Predict Case Outcome

```http
POST /predict
Content-Type: application/json

{
  "case_facts": "A dispute between two parties regarding contract breach..."
}
```

**Response:**
```json
{
  "prediction": "allowed",
  "confidence": 0.87,
  "precedents": [
    {
      "title": "Case Title",
      "date": "2020-01-15",
      "similarity": 0.92,
      "relevance_score": 0.85
    }
  ]
}
```

#### 2. Get Sample Cases

```http
GET /sample_cases?count=5
```

Returns sample cases from the training dataset for testing.

#### 3. Analyze Text

```http
POST /analyze_text
Content-Type: application/json

{
  "text": "Legal text to analyze..."
}
```

#### 4. Compare Retrieval Methods

```http
POST /compare_methods
Content-Type: application/json

{
  "case_facts": "Case description...",
  "methods": ["bm25", "semantic", "hybrid"]
}
```

Returns comparison of different retrieval methods.

#### 5. Schedule Cases

```http
POST /schedule
Content-Type: application/json

{
  "cases": [
    {
      "case_id": "2020_1_123_456",
      "urgency": 0.8,
      "predicted_outcome": "allowed"
    }
  ]
}
```

## 📊 Dataset

The project uses the **Indian Supreme Court Judgment Dataset** from a public S3 bucket:

- **Bucket:** `indian-supreme-court-judgments`
- **Format:** Parquet metadata + TAR archives with PDF files
- **Coverage:** 1950-2024 decisions
- **Cases:** 18,000+ balanced dataset (Allowed/Dismissed)
- **Data Points:** Year, title, facts, judgment date, disposal nature

### Dataset Building Process

1. **Metadata Extraction**: Downloads parquet files from S3 metadata store
2. **PDF Retrieval**: Identifies and downloads relevant PDFs from yearly TAR archives
3. **Text Extraction**: Uses `pdfplumber` to extract text from PDFs
4. **Cleaning**: Removes HTML artifacts, OCR errors, and non-essential text
5. **Balancing**: Creates balanced train/test split (80/20)

### Building Custom Dataset

```bash
cd backend

# Download and process data from S3
python build_indian_dataset.py

# Output: indian_data/train.jsonl and indian_data/test.jsonl
```

## 🏗️ Architecture

### Backend Architecture

```
Flask API
├── Legal Prediction System
│   └── Random Forest Classifier
├── Contextual Retrieval
│   ├── BM25 Indexer
│   └── Semantic Search (FAISS)
├── Smart Scheduler
└── PDF Processor
    └── Pdfplumber
```

### Frontend Architecture

```
React App
├── Pages
│   ├── Index (Home/Predict)
│   ├── NotFound
├── Components
│   ├── CaseInput
│   ├── PredictionResult
│   ├── PrecedentsList
│   ├── CompareView
│   ├── SchedulerStatus
│   └── SampleCases
└── Lib
    ├── API Client
    └── Utils
```

### Data Flow

```
User Input
    ↓
Frontend UI (React)
    ↓
API Request (axios)
    ↓
Flask Backend
    ├─→ Prediction Model → Outcome
    ├─→ BM25 Search → Keywords Results
    └─→ FAISS Search → Semantic Results
    ↓
Hybrid Ranking
    ↓
Response → Frontend
    ↓
Display Results
```

## 🔐 Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

Backend uses unsigned AWS S3 access (public bucket).

## 📝 Development Notes

- **Python Version:** 3.12+ recommended
- **Node Version:** 18+ recommended
- **Package Manager:** npm or bun (bun is faster)
- **Frontend Build Tool:** Vite
- **CSS Framework:** Tailwind CSS
- **Component Library:** shadcn/ui

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes and commit: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open a Pull Request

### Code Style

- **Python:** PEP 8 (use `pylint` or `black`)
- **TypeScript/React:** ESLint configuration included
- Follow existing code patterns and conventions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Authors

- Created as part of Problem-Based Learning (PBL) project

## 🙏 Acknowledgments

- Indian Supreme Court for providing the judgment dataset
- Open source community for excellent tools and libraries

## 📞 Support

For issues, questions, or contributions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include error logs and reproduction steps

---

**Last Updated:** April 21, 2026