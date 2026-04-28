"""
SMS Smishing Detection - Exploratory Data Analysis Graphs
Generates 6 EDA plots from the smishing dataset.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ============================================================================
# CONFIGURATION
# ============================================================================
DATASET_PATH = 'dataset/dataset_with_new_smish_without_spam.csv'
OUTPUT_DIR   = 'graphs'

# Urgency keywords common in phishing messages
URGENCY_WORDS = [
    'free', 'win', 'prize', 'claim', 'click', 'verify', 'urgent',
    'account', 'bank', 'password', 'confirm', 'expire', 'limited',
    'offer', 'reward', 'cash', 'selected', 'congratulations'
]

# Common English stopwords to exclude from word-frequency charts
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'he', 'him', 'his', 'she', 'her', 'hers',
    'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'this',
    'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'should', 'can', 'could', 'may', 'might', 'shall', 'must',
    'a', 'an', 'the', 'and', 'but', 'if', 'or', 'as', 'of', 'at', 'by',
    'for', 'with', 'about', 'to', 'from', 'in', 'on', 'up', 'so', 'no',
    'not', 'u', 'r', 'ur', '2', '4', 'get', 'just', 'now', 'got', 'go',
    'know', 'like', 'one', 'come', 'good', 'want', 'im', 'dont', 'ill',
    'ok', 'yeah', 'hi', 'hey', 'lol', 'ya', 'da', 'na', 'oh', 'gt', 'lt'
}

# ============================================================================
# SETUP
# ============================================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style='whitegrid')
PALETTE = {'ham': '#2196F3', 'smish': '#F44336'}

# ============================================================================
# LOAD DATA
# ============================================================================
df = pd.read_csv(DATASET_PATH)

# Normalize flag columns: yes/Yes/no/No → 1/0
for col in ['url', 'email', 'phone']:
    df[col] = df[col].str.lower().map({'yes': 1, 'no': 0}).fillna(0).astype(int)

# Binary label for numeric operations
df['label_binary'] = (df['label'] == 'smish').astype(int)

# Derived text features
df['msg_length']         = df['message'].str.len()
df['word_count']         = df['message'].str.split().str.len()
df['uppercase_ratio']    = df['message'].apply(
    lambda m: sum(c.isupper() for c in str(m)) / max(len(str(m)), 1))
df['digit_count']        = df['message'].apply(lambda m: sum(c.isdigit() for c in str(m)))
df['special_char_count'] = df['message'].apply(lambda m: sum(c in '!$#*@' for c in str(m)))
df['urgency_score']      = df['message'].str.lower().apply(
    lambda m: sum(w in m.split() for w in URGENCY_WORDS))
df['exclamation_count']  = df['message'].str.count('!')

print(f"Dataset loaded: {df.shape[0]:,} rows")
print(f"Label distribution:\n{df['label'].value_counts().to_string()}\n")

# ============================================================================
# GRAPH 1 — Label Distribution
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 5))

counts = df['label'].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=[PALETTE['ham'], PALETTE['smish']],
              edgecolor='white', linewidth=1.2, width=0.5)

for bar, (label, count) in zip(bars, counts.items()):
    pct = count / len(df) * 100
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 60,
            f'{count:,}\n({pct:.1f}%)',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('SMS Label Distribution: Ham vs Smish', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Label', fontsize=12)
ax.set_ylabel('Number of Messages', fontsize=12)
ax.set_ylim(0, counts.max() * 1.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/01_label_distribution.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/01_label_distribution.png")

# ============================================================================
# GRAPH 2 — Message Length KDE by Class
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 5))

for label, color in PALETTE.items():
    subset = df[df['label'] == label]['msg_length']
    sns.kdeplot(subset, ax=ax, label=label.capitalize(),
                color=color, fill=True, alpha=0.35, linewidth=2)
    ax.axvline(subset.median(), color=color, linestyle='--', linewidth=1.5,
               label=f'{label.capitalize()} median ({int(subset.median())} chars)')

ax.set_title('Message Length Distribution by Class', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Message Length (characters)', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.legend(fontsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/02_message_length_kde.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/02_message_length_kde.png")

# ============================================================================
# GRAPH 3 — URL / Email / Phone Flag Rates by Class
# ============================================================================
flag_rates = df.groupby('label')[['url', 'email', 'phone']].mean() * 100

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
flags_info = [('url', 'URL Present'), ('email', 'Email Present'), ('phone', 'Phone Present')]

for ax, (flag, flag_label) in zip(axes, flags_info):
    vals = [flag_rates.loc['ham', flag], flag_rates.loc['smish', flag]]
    bars = ax.bar(['Ham', 'Smish'], vals,
                  color=[PALETTE['ham'], PALETTE['smish']],
                  edgecolor='white', width=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.set_title(flag_label, fontsize=12, fontweight='bold')
    ax.set_ylabel('Messages with flag (%)', fontsize=10)
    ax.set_ylim(0, max(vals) * 1.4 + 2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

fig.suptitle('Binary Flag Rates by Class (URL / Email / Phone)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/03_flag_rates_by_class.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/03_flag_rates_by_class.png")

# ============================================================================
# GRAPH 4 — Top 20 Words per Class
# ============================================================================
def top_words(text_series, n=20):
    """Count word frequencies, excluding stopwords and short words."""
    words = []
    for msg in text_series.dropna():
        for w in str(msg).lower().split():
            w = ''.join(c for c in w if c.isalpha())
            if w and w not in STOPWORDS and len(w) > 2:
                words.append(w)
    return pd.Series(words).value_counts().head(n)

ham_words   = top_words(df[df['label'] == 'ham']['message'])
smish_words = top_words(df[df['label'] == 'smish']['message'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

ax1.barh(ham_words.index[::-1], ham_words.values[::-1],
         color=PALETTE['ham'], edgecolor='white', alpha=0.9)
ax1.set_title('Top 20 Words — Ham Messages', fontsize=13, fontweight='bold')
ax1.set_xlabel('Frequency', fontsize=11)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

ax2.barh(smish_words.index[::-1], smish_words.values[::-1],
         color=PALETTE['smish'], edgecolor='white', alpha=0.9)
ax2.set_title('Top 20 Words — Smish Messages', fontsize=13, fontweight='bold')
ax2.set_xlabel('Frequency', fontsize=11)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

fig.suptitle('Most Frequent Words by Class (stopwords removed)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/04_top_words_per_class.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/04_top_words_per_class.png")

# ============================================================================
# GRAPH 5 — Message Length Boxplot by Class
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

ham_len   = df[df['label'] == 'ham']['msg_length']
smish_len = df[df['label'] == 'smish']['msg_length']

bp = ax.boxplot([ham_len, smish_len],
                patch_artist=True,
                tick_labels=['Ham', 'Smish'],
                medianprops=dict(color='white', linewidth=2.5),
                whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5),
                flierprops=dict(marker='o', markersize=3, alpha=0.25))

bp['boxes'][0].set_facecolor(PALETTE['ham'])
bp['boxes'][1].set_facecolor(PALETTE['smish'])

for i, lengths in enumerate([ham_len, smish_len], 1):
    med = lengths.median()
    ax.text(i, med + 8, f'Median: {int(med)}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_title('Message Length Distribution by Class (with Outliers)',
             fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Class', fontsize=12)
ax.set_ylabel('Message Length (characters)', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/05_message_length_boxplot.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/05_message_length_boxplot.png")

# ============================================================================
# GRAPH 6 — Correlation Heatmap of Engineered Features vs Label
# ============================================================================
feature_cols = [
    'msg_length', 'word_count', 'uppercase_ratio',
    'digit_count', 'special_char_count', 'urgency_score',
    'exclamation_count', 'url', 'email', 'phone', 'label_binary'
]

corr = df[feature_cols].corr()

fig, ax = plt.subplots(figsize=(12, 9))
sns.heatmap(corr, ax=ax, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, linewidths=0.5, linecolor='white',
            square=True, cbar_kws={'shrink': 0.8})

ax.set_title('Feature Correlation Heatmap\n(label_binary: 0 = ham, 1 = smish)',
             fontsize=13, fontweight='bold', pad=15)
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(rotation=0, fontsize=9)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/06_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Saved: {OUTPUT_DIR}/06_correlation_heatmap.png")

print(f"\nAll graphs saved to {OUTPUT_DIR}/")
