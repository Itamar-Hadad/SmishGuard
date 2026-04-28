"""
SMS Smishing Detection Model
Uses Sentence-BERT for NLP feature extraction
"""

# ============================================================================
# IMPORTS
# ============================================================================
import pandas as pd
import numpy as np
import re
import warnings
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================
# Sentence-BERT model configuration
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'  # Fast and efficient (384 dimensions)
# Alternative: 'all-mpnet-base-v2' for better quality (768 dimensions)

# Data split configuration
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Embedding generation configuration
BATCH_SIZE = 32

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def detect_url(text):
    """
    Detect if text contains a URL.
    
    Parameters:
    - text: Input text string
    
    Returns:
    - 1 if URL found, 0 otherwise
    """
    if pd.isna(text):
        return 0
    text = str(text)
    # Patterns: http://, https://, www., .com, .net, .org, etc.
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*)'
    return 1 if re.search(url_pattern, text, re.IGNORECASE) else 0


def detect_phone(text):
    """
    Detect if text contains a phone number.
    
    Parameters:
    - text: Input text string
    
    Returns:
    - 1 if phone number found, 0 otherwise
    """
    if pd.isna(text):
        return 0
    text = str(text)
    # Patterns: various phone number formats
    # Matches: 123-456-7890, (123) 456-7890, 123.456.7890, +1 123 456 7890, etc.
    # Also matches sequences of 5+ digits (SMS short codes like 87121, 81010)
    # and longer sequences (7+ digits for regular phone numbers)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{5,}\b'
    return 1 if re.search(phone_pattern, text) else 0


def detect_email(text):
    """
    Detect if text contains an email address.
    
    Parameters:
    - text: Input text string
    
    Returns:
    - 1 if email found, 0 otherwise
    """
    if pd.isna(text):
        return 0
    text = str(text)
    # Pattern: standard email format
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return 1 if re.search(email_pattern, text) else 0


# ============================================================================
# SMISH SIGNAL DETECTORS
# ============================================================================
_SHORTENED_URL_RE = re.compile(
    r'(https?://)?(bit\.ly|goo\.gl|tinyurl\.com|t\.co|ow\.ly|did\.li|'
    r'tiny\.cc|is\.gd|rb\.gy|shorturl\.at|cutt\.ly|clck\.ru|snip\.ly|'
    r'1url\.com|s2r\.co|v\.gd|clicky\.me|linkd\.in|trib\.al)/',
    re.IGNORECASE
)

def detect_shortened_url(text):
    if pd.isna(text): return 0
    return 1 if _SHORTENED_URL_RE.search(str(text)) else 0


_LOGIN_WORDS_RE = re.compile(
    r'\b(log\s?in|sign\s?in|verify\s+your\s+account|reactivate|'
    r'confirm\s+your\s+(identity|details|login|password)|please\s+log\s+in)\b',
    re.IGNORECASE
)

def detect_login_words(text):
    if pd.isna(text): return 0
    return 1 if _LOGIN_WORDS_RE.search(str(text)) else 0


_URGENCY_WORDS_RE = re.compile(
    r'\b(urgent|immediately|right\s+now|as\s+soon\s+as\s+possible|asap|'
    r'without\s+delay|action\s+required|act\s+now|expire[sd]?\s+soon|last\s+chance)\b',
    re.IGNORECASE
)

def detect_urgency_words(text):
    if pd.isna(text): return 0
    return 1 if _URGENCY_WORDS_RE.search(str(text)) else 0


_THREAT_WORDS_RE = re.compile(
    r'\b(blocked|suspended|temporarily\s+blocked|unusual\s+activity|'
    r'unauthorized\s+access|security\s+issue|account\s+suspended|'
    r'account\s+blocked|fraudulent|identity\s+theft|'
    r'illegal\s+activity|legal\s+(action|proceedings))\b',
    re.IGNORECASE
)

def detect_threat_words(text):
    if pd.isna(text): return 0
    return 1 if _THREAT_WORDS_RE.search(str(text)) else 0


_ACTION_REQUEST_RE = re.compile(
    r'\b(click\s+the\s+link|tap\s+here|click\s+here|visit\s+the\s+following|'
    r'go\s+to\s+the\s+following\s+link|log\s+in\s+via\s+the\s+following|'
    r'enter\s+the\s+link|follow\s+this\s+link|use\s+this\s+link|'
    r'access\s+the\s+link|via\s+the\s+following\s+link)\b',
    re.IGNORECASE
)

def detect_action_request(text):
    if pd.isna(text): return 0
    return 1 if _ACTION_REQUEST_RE.search(str(text)) else 0


_SUSPICIOUS_URL_DOMAIN_RE = re.compile(
    r'https?://([^/\s]*'
    r'(secure|verify|login|banking|update|confirm|reward|prize|'
    r'alert|warning|urgent|account-secure|support-[a-z]+)'
    r'[^/\s]*)',
    re.IGNORECASE
)

def detect_suspicious_url_domain(text):
    if pd.isna(text): return 0
    return 1 if _SUSPICIOUS_URL_DOMAIN_RE.search(str(text)) else 0


# ============================================================================
# HAM SIGNAL DETECTORS
# ============================================================================
_REFERENCE_NUMBER_RE = re.compile(
    r'(claim\s+number\s*\d+|reference\s+number\s*\d+|'
    r'message\s+\d{3}[-]\d{3}|message\s+\d+[-]\d+|'
    r'case\s+number\s*\d+|ticket\s+(?:number\s*)?\d+|'
    r'confirmation\s+(?:number\s*)?\d{6,})',
    re.IGNORECASE
)

def detect_reference_number(text):
    if pd.isna(text): return 0
    return 1 if _REFERENCE_NUMBER_RE.search(str(text)) else 0


_OFFICIAL_DOMAIN_RE = re.compile(
    r'https?://([^/\s]*\.(co\.il|gov\.il|org\.il|muni\.il|ac\.il|'
    r'net\.il|k12\.il|idf\.il|gov\.uk|gov\.au|gouv\.fr))',
    re.IGNORECASE
)

def detect_official_domain(text):
    if pd.isna(text): return 0
    return 1 if _OFFICIAL_DOMAIN_RE.search(str(text)) else 0


# ============================================================================
# NEUTRAL DETECTOR
# ============================================================================
_EXACT_AMOUNT_RE = re.compile(
    r'(\b\d+\.\d{2}\s*(NIS|nis|\$|USD|GBP|EUR|ILS|shekels?|pounds?|dollars?|euros?)\b|'
    r'\b(fees?\s+totaling|interest\s+totaling|charged\s+(?:as\s+follows|a\s+total)|'
    r'total\s+charge[sd]?)\b)',
    re.IGNORECASE
)

def detect_exact_amount(text):
    if pd.isna(text): return 0
    return 1 if _EXACT_AMOUNT_RE.search(str(text)) else 0


def extract_features_from_text(text):
    """
    Extract URL, email, and phone features from text message.
    
    Parameters:
    - text: Input text string
    
    Returns:
    - Dictionary with 'url', 'email', 'phone' flags (1 or 0)
    """
    return {
        'url': detect_url(text),
        'email': detect_email(text),
        'phone': detect_phone(text)
    }


def preprocess_text(text):
    """
    Preprocess text for NLP: convert to lowercase and remove extra whitespace.
    
    Parameters:
    - text: Input text string
    
    Returns:
    - Preprocessed text string
    """
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    return text.strip()


def encode_flags(df):
    """
    Encode url, email, phone flags to binary (yes=1, no=0).
    Handles case-insensitive input (Yes, YES, yes all become 1).
    
    Parameters:
    - df: DataFrame containing 'url', 'email', 'phone' columns
    
    Returns:
    - Numpy array with encoded flag values
    """
    encoded = df.copy()
    for col in ['url', 'email', 'phone']:
        # Convert to lowercase first to handle any capitalization
        encoded[col] = encoded[col].str.lower().map({'yes': 1, 'no': 0}).fillna(0)
    return encoded[['url', 'email', 'phone']].values


def process_new_message(message_text, auto_detect=True, has_url='no', has_email='no', has_phone='no', sbert_model=None):
    """
    Process a new message for prediction using Sentence-BERT.
    Automatically detects URLs, emails, and phone numbers from the message text.
    
    Parameters:
    - message_text: The SMS message text
    - auto_detect: If True (default), automatically detect URL/email/phone from text
    - has_url: 'yes' or 'no' (optional, only used if auto_detect=False)
    - has_email: 'yes' or 'no' (optional, only used if auto_detect=False)
    - has_phone: 'yes' or 'no' (optional, only used if auto_detect=False)
    - sbert_model: SentenceTransformer model (if None, will use global model)
    
    Returns:
    - Processed feature vector ready for model prediction (numpy array)
    """
    if sbert_model is None:
        sbert_model = globals().get('sbert_model')
        if sbert_model is None:
            raise ValueError("Sentence-BERT model not initialized. Please run the main processing first.")
    
    # Preprocess text
    processed_text = preprocess_text(message_text)
    
    # Generate Sentence-BERT embedding
    text_embedding = sbert_model.encode(
        [processed_text],
        show_progress_bar=False,
        convert_to_numpy=True
    )
    
    # Extract features from text or use provided flags
    if auto_detect:
        # Automatically detect URL, email, phone from message text (already in 1/0 format)
        features = extract_features_from_text(message_text)
        flags_vector = np.array([[features['url'], features['email'], features['phone']]])
    else:
        # Use provided flags (convert 'yes'/'no' to 1/0)
        flags_vector = np.array([[1 if has_url.lower() == 'yes' else 0,
                                 1 if has_email.lower() == 'yes' else 0,
                                 1 if has_phone.lower() == 'yes' else 0]])
    
    # Combine features
    combined_features = np.hstack([text_embedding, flags_vector])
    
    return combined_features


# ============================================================================
# HELPER FUNCTION FOR DEBUGGING
# (defined at module level so it can be imported by MLsmish)
# ============================================================================
def print_feature_summary(features, message_text=None):
    """
    Print a summary of the feature vector instead of the full long vector.

    Parameters:
    - features: Feature vector from process_new_message()
    - message_text: Optional message text to show
    """
    if message_text:
        print(f"Message: {message_text}")
    print(f"\nFeature Vector Summary:")
    print(f"  Shape: {features.shape}")
    print(f"  Total dimensions: {features.shape[1]}")
    print(f"  - Sentence-BERT embedding: {features.shape[1] - 3} dimensions")
    print(f"  - Flags (URL, Email, Phone): 3 dimensions")
    print(f"\n  First 5 values (Sentence-BERT): {features[0, :5]}")
    print(f"  Last 3 values (Flags): {features[0, -3:]}")
    print(f"  URL flag: {features[0, -3]}, Email flag: {features[0, -2]}, Phone flag: {features[0, -1]}")


# ============================================================================
# DATA LOADING & NLP PREPROCESSING
# Only runs when this file is executed directly (not when imported as a module).
# MLsmish.py imports the helper functions above without triggering this block.
# ============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("LOADING DATASET")
    print("=" * 70)

    df = pd.read_csv('SMSSmishCollection_with_flags.csv')

    print(f"Dataset shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nLabel distribution:")
    print(df['label'].value_counts())
    print(f"\nLabel distribution (percentage):")
    print(df['label'].value_counts(normalize=True) * 100)

    # ============================================================================
    # DATA SPLITTING
    # ============================================================================
    print("\n" + "=" * 70)
    print("SPLITTING DATA INTO TRAIN AND TEST SETS")
    print("=" * 70)

    # Prepare features and target
    X = df[['message', 'url', 'email', 'phone']]  # Features (text messages and flags)
    y = df['label']  # Target variable (ham/smish)

    # Split with stratify to ensure equal distribution of labels
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"Train set size: {len(X_train)} ({len(X_train)/len(df)*100:.1f}%)")
    print(f"Test set size: {len(X_test)} ({len(X_test)/len(df)*100:.1f}%)")
    print(f"\nTrain set label distribution:")
    print(y_train.value_counts())
    print(f"\nTrain set label distribution (percentage):")
    print(y_train.value_counts(normalize=True) * 100)
    print(f"\nTest set label distribution:")
    print(y_test.value_counts())
    print(f"\nTest set label distribution (percentage):")
    print(y_test.value_counts(normalize=True) * 100)

    # ============================================================================
    # NLP PREPROCESSING WITH SENTENCE-BERT
    # ============================================================================
    print("\n" + "=" * 70)
    print("NLP PREPROCESSING WITH SENTENCE-BERT")
    print("=" * 70)

    # Preprocess text data
    print("\n1. Preprocessing text data...")
    X_train_text = X_train['message'].apply(preprocess_text).tolist()
    X_test_text = X_test['message'].apply(preprocess_text).tolist()

    # Initialize Sentence-BERT model
    print(f"\n2. Loading Sentence-BERT model: {SBERT_MODEL_NAME}...")
    print("   (First run will download the model, subsequent runs will use cached version)")
    sbert_model = SentenceTransformer(SBERT_MODEL_NAME)

    # Generate embeddings for training data
    print(f"\n3. Generating embeddings for training text ({len(X_train_text)} messages)...")
    print("   This may take a few minutes...")
    X_train_sbert = sbert_model.encode(
        X_train_text,
        show_progress_bar=True,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True
    )

    # Generate embeddings for test data
    print(f"\n4. Generating embeddings for test text ({len(X_test_text)} messages)...")
    X_test_sbert = sbert_model.encode(
        X_test_text,
        show_progress_bar=True,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True
    )

    # Extract features from message text (auto-detect URL, email, phone)
    print("\n5. Extracting features from message text (auto-detecting URL, email, phone)...")
    X_train_extracted = X_train['message'].apply(extract_features_from_text)
    X_test_extracted = X_test['message'].apply(extract_features_from_text)

    # Convert extracted features to DataFrame format
    X_train_extracted_df = pd.DataFrame(list(X_train_extracted))
    X_test_extracted_df = pd.DataFrame(list(X_test_extracted))

    # Use extracted features from text (more reliable for new messages)
    X_train_flags = X_train_extracted_df[['url', 'email', 'phone']].values
    X_test_flags = X_test_extracted_df[['url', 'email', 'phone']].values

    print(f"   Extracted features from training set:")
    print(f"   - URLs found: {X_train_flags[:, 0].sum()} ({X_train_flags[:, 0].sum()/len(X_train_flags)*100:.1f}%)")
    print(f"   - Emails found: {X_train_flags[:, 1].sum()} ({X_train_flags[:, 1].sum()/len(X_train_flags)*100:.1f}%)")
    print(f"   - Phones found: {X_train_flags[:, 2].sum()} ({X_train_flags[:, 2].sum()/len(X_train_flags)*100:.1f}%)")

    # Combine Sentence-BERT embeddings with flag features
    print("\n6. Combining features...")
    X_train_combined = np.hstack([X_train_sbert, X_train_flags])
    X_test_combined = np.hstack([X_test_sbert, X_test_flags])

    print(f"\n{'='*70}")
    print("FEATURE SUMMARY")
    print(f"{'='*70}")
    print(f"Training features shape: {X_train_combined.shape}")
    print(f"Test features shape: {X_test_combined.shape}")
    print(f"Number of Sentence-BERT features: {X_train_sbert.shape[1]}")
    print(f"Number of flag features: {X_train_flags.shape[1]}")
    print(f"Total features: {X_train_combined.shape[1]}")

    # ============================================================================
    # COMPLETION MESSAGE
    # ============================================================================
    print(f"\n{'='*70}")
    print("✓ NLP PREPROCESSING COMPLETE!")
    print(f"{'='*70}")
    print("✓ Ready to train a model with:")
    print("  - X_train_combined: Training features")
    print("  - y_train: Training labels")
    print("  - X_test_combined: Test features")
    print("  - y_test: Test labels")
    print("\n✓ Use process_new_message() function to process future customer messages")
    print("  The function automatically detects URLs, emails, and phone numbers from message text")
    print("\nNote: Make sure to install sentence-transformers: pip install sentence-transformers")

    # ============================================================================
    # EXAMPLE USAGE
    # ============================================================================
    # Example 1: Process a new message with automatic feature detection (recommended)
    new_message = "Free entry! Visit www.example.com or call 123-456-7890"
    new_features = process_new_message(
        new_message,
        auto_detect=True,  # Automatically detects URL, email, phone from text
        sbert_model=sbert_model
    )
    # Print summary instead of full vector
    print_feature_summary(new_features, new_message)
    # Or print full vector: print(new_features)
    # Features will be automatically extracted: URL=1, Phone=1, Email=0
    #
    # Example 2: Process a new message with manual flags (if auto_detect=False)
    # new_message = "Free entry in 2 a wkly comp to win FA Cup final tkts!"
    # new_features = process_new_message(
    #     new_message,
    #     auto_detect=False,
    #     has_url='no',
    #     has_email='no',
    #     has_phone='yes',
    #     sbert_model=sbert_model
    # )
    #
    # After training your model:
    # prediction = model.predict(new_features)
    # probability = model.predict_proba(new_features)
