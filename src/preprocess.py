import re
import pandas as pd
from sklearn.model_selection import train_test_split
import nltk
from nltk.corpus import stopwords

# Download stopwords if not already present
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = text.split()
    text = [word for word in text if word not in stop_words]
    return " ".join(text)

def load_and_preprocess(csv_path):
    df = pd.read_csv(csv_path, encoding="latin-1")
    df.columns = ["sentiment", "sentence"]

    # Apply cleaning steps from notebook
    df = df.drop_duplicates(subset="sentence")
    df = df.dropna()

    # Apply label mapping from notebook
    label_mapping = {
        "negative": 0,
        "neutral": 1,
        "positive": 2
    }
    df["label"] = df["sentiment"].map(label_mapping)

    # Apply clean_text
    df["clean_sentence"] = df["sentence"].apply(clean_text)

    # Use the cleaned sentence and mapped label for splitting
    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_sentence"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"]
    )

    return X_train, X_test, y_train, y_test
