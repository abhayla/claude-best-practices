# MODE 3: THREAD ANALYSIS

### Analysis Process

1. **Fetch the thread** using Mode 1 (include comments: `?limit=500&depth=10`)
2. **Parse comment tree** — map parent-child relationships, scores, and authors
3. **Run analysis** on each dimension below

### Analysis Dimensions

#### Sentiment Breakdown
| Category | Description |
|----------|-------------|
| Positive | Supportive, enthusiastic, agreeing |
| Negative | Critical, opposing, frustrated |
| Neutral | Informational, factual, asking questions |
| Mixed | Contains both positive and negative elements |

Report percentages for each category.

#### Argument Extraction
- **Top 3-5 arguments FOR** the topic (with scores and representative quotes)
- **Top 3-5 arguments AGAINST** the topic (with scores and representative quotes)
- **Most cited sources/evidence** across the thread
- **Novel arguments** (unique points not commonly made)

#### Consensus & Controversy
- **Consensus points:** Where most commenters agree (high-score comments with few rebuttals)
- **Controversial points:** Where the community is divided (comments with many replies and mixed scores)
- **Minority opinions:** Downvoted comments that still present valid arguments

#### Discussion Quality Rating
| Factor | Rating | Description |
|--------|--------|-------------|
| Depth | 1-5 | Are arguments substantive with evidence? |
| Civility | 1-5 | Is discussion respectful or hostile? |
| Diversity | 1-5 | Are multiple viewpoints represented? |
| Expertise | 1-5 | Do commenters show domain knowledge? |
| Signal/Noise | 1-5 | Ratio of substantive to low-effort comments |

### Output Format

```
