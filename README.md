# 📊 Financial News Sentiment Classifier

 Problem Statement
The objective of this project is to classify financial news headlines or sentences into  
**Positive**, **Negative**, or **Neutral** sentiment to understand market context.

Financial sentiment analysis plays an important role in:
- Stock market analysis
- Risk assessment
- Investment decision support systems



 Dataset
- **Dataset Name:** Sentiment Analysis for Financial News  
- **Source:** Kaggle  
- **Link:** https://www.kaggle.com/datasets/ankurzing/sentiment-analysis-for-financial-news  

 Dataset Description
The dataset contains short financial news sentences manually labeled into three sentiment categories:
- Positive
- Negative
- Neutral

---

🧰 Tech Stack
- **Programming Language:** Python  
- **Libraries & Tools:**
  - Pandas, NumPy
  - Scikit-learn
  - HuggingFace Transformers (FinBERT – optional)
  - Matplotlib / Seaborn
  - LangChain (for evaluation prompts)
- **Development Environment:** Google Colab

---

 Methodology

 1️⃣ Data Preprocessing
- Loaded and explored the dataset
- Analyzed sentiment class distribution
- Split data into training and testing sets (80:20)

 2️⃣ Baseline Classical Model
- Applied **TF-IDF vectorization** for text representation
- Trained a **Logistic Regression** classifier
- Evaluated performance using accuracy, precision, recall, and F1-score

 3️⃣ LLM Zero-Shot Sentiment Classification
- Used a pretrained **FinBERT** model from HuggingFace
- Performed zero-shot sentiment classification without fine-tuning
- Compared predictions with the classical model

---

 🤖 Models Used

| Model Type | Description |
|-----------|------------|
| Classical ML | TF-IDF + Logistic Regression |
| LLM | FinBERT (Zero-Shot Transformer Model) |

---

 Evaluation & Results

- Generated **classification report**
- Visualized **confusion matrix** for sentiment classes
- Compared classical ML model with LLM zero-shot predictions

Key Observations:
- Classical ML model performed strongly on structured financial text
- LLM struggled slightly with **neutral sentiment detection**
- Neutral and short headlines caused most misclassifications

---


