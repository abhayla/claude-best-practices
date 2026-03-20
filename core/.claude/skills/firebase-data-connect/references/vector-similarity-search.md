# Vector Similarity Search

### Schema

```graphql
type Movie @table {
  title: String!
  description: String
  descriptionEmbedding: Vector! @col(size: 768)
}
```

### Generate Embeddings

```graphql
mutation CreateMovieWithEmbedding($title: String!, $description: String!)
  @auth(level: USER) {
  movie_insert(data: {
    title: $title,
    description: $description,
    descriptionEmbedding_embed: {
      model: "textembedding-gecko@003",
      text: $description
    }
  })
}
```

### Similarity Query

```graphql
query SearchMovies($query: String!) @auth(level: PUBLIC) {
  movies_descriptionEmbedding_similarity(
    compare_embed: { model: "textembedding-gecko@003", text: $query },
    method: COSINE,
    within: 2.0,
    limit: 5
  ) {
    id title description
    _metadata { distance }
  }
}
```

| Parameter | Description |
|-----------|-------------|
| `compare_embed` | Generate embedding from text via Vertex AI |
| `compare` | Raw Vector for pre-computed embeddings |
| `method` | `L2`, `COSINE`, or `INNER_PRODUCT` |
| `within` | Max distance threshold |

---

