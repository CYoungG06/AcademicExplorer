import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Load the JSON data
with open('single_query_result.json', 'r') as f:
    data = json.load(f)

# Extract the user's query
user_query = data['user_query']
print(f"User Query: {user_query}")

# Extract all papers (search results and expanded papers)
all_papers = data['search_papers'] + data['expanded_papers']

# Create a dataframe with relevant paper information
papers_df = pd.DataFrame([
    {
        'title': paper['title'],
        'arxiv_id': paper['arxiv_id'],
        'relevance_score': paper.get('relevance_score', 0),
        'year': paper['arxiv_id'].split('.')[0][:2],  # First two digits of arxiv ID for year approximation
        'source': paper.get('source', 'Expanded'),
        'citation_count': len(paper.get('cited_papers', [])),
        'type': 'search' if paper in data['search_papers'] else 'expanded'
    }
    for paper in all_papers
])

# Filter papers with relevance_score > 0.5
relevant_papers = papers_df[papers_df['relevance_score'] > 0.5]
print(f"\nNumber of papers with relevance score > 0.5: {len(relevant_papers)}")

# Top 10 most relevant papers
top_relevant = relevant_papers.sort_values('relevance_score', ascending=False).head(10)

print("\nTop 10 most relevant papers:")
for i, (_, paper) in enumerate(top_relevant.iterrows(), 1):
    print(f"{i}. {paper['title']} (Score: {paper['relevance_score']:.2f})")

# Papers by type (search vs. expanded)
paper_types = papers_df['type'].value_counts()
print(f"\nPapers by source: {paper_types.to_dict()}")

# Distribution of relevance scores
plt.figure(figsize=(10, 6))
plt.hist(papers_df['relevance_score'], bins=20, alpha=0.7)
plt.axvline(x=0.5, color='r', linestyle='--', label='Threshold (0.5)')
plt.title('Distribution of Relevance Scores')
plt.xlabel('Relevance Score')
plt.ylabel('Count')
plt.legend()
plt.grid(True, alpha=0.3)

# Relevance score by paper type
plt.figure(figsize=(10, 6))
papers_df.boxplot(column='relevance_score', by='type', figsize=(10, 6))
plt.title('Relevance Score by Paper Type')
plt.suptitle('')
plt.ylabel('Relevance Score')
plt.grid(True, alpha=0.3)

# Extract common keywords from titles to identify topics
def extract_keywords(title):
    # Common stopwords specific to the domain
    stopwords = {'a', 'the', 'for', 'in', 'with', 'from', 'of', 'and', 'to', 'on', 'using', 
                'via', 'by', 'is', 'are', 'an'}
    words = title.lower().split()
    return [word for word in words if word not in stopwords and len(word) > 3]

all_keywords = []
for title in relevant_papers['title']:
    all_keywords.extend(extract_keywords(title))

keyword_counts = Counter(all_keywords)
top_keywords = pd.DataFrame(keyword_counts.most_common(15), columns=['Keyword', 'Count'])

# Analyze years of publication
if papers_df['year'].dtype == 'object' and papers_df['year'].str.contains(r'^\d+$').all():
    papers_df['year'] = papers_df['year'].astype(int) + 2000
    year_counts = papers_df['year'].value_counts().sort_index()
    
    plt.figure(figsize=(12, 6))
    year_counts.plot(kind='bar')
    plt.title('Papers by Publication Year')
    plt.xlabel('Year')
    plt.ylabel('Count')
    plt.grid(True, alpha=0.3)

# Print citation network information
avg_citations = papers_df['citation_count'].mean()
print(f"\nAverage number of citations per paper: {avg_citations:.2f}")
max_citations = papers_df['citation_count'].max()
print(f"Maximum number of citations for a paper: {max_citations}")

# Print top keywords
print("\nTop 15 keywords in relevant papers:")
print(top_keywords)

# Calculate correlation between relevance score and citation count
correlation = papers_df[['relevance_score', 'citation_count']].corr()
print(f"\nCorrelation between relevance score and citation count:\n{correlation}")

# Summary of the dataset
print("\nSummary statistics for relevance scores:")
print(papers_df['relevance_score'].describe())

# Percentage of papers that are highly relevant (score > 0.8)
highly_relevant = len(papers_df[papers_df['relevance_score'] > 0.8])
print(f"\nPercentage of papers that are highly relevant (score > 0.8): {highly_relevant/len(papers_df)*100:.2f}%")

# Output relevant papers to CSV for further analysis
relevant_papers.to_csv('relevant_papers.csv', index=False)