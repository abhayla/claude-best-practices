# SDK Generation

### Configuration (connector.yaml)

```yaml
connectorId: my-connector
generate:
  javascriptSdk:
    outputDir: "../web-app/src/lib/dataconnect"
    package: "@movie-app/dataconnect"
  kotlinSdk:
    outputDir: "../android-app/app/src/main/kotlin/com/example/dataconnect"
    package: "com.example.dataconnect"
  swiftSdk:
    outputDir: "../ios-app/DataConnect"
```

Generate: `npx -y firebase-tools@latest dataconnect:sdk:generate`

### Web SDK Usage

```typescript
import { listMovies, createMovie, getMovie } from '@movie-app/dataconnect';
import { listMoviesRef, subscribe } from '@movie-app/dataconnect';

// Query
const result = await listMovies();
console.log(result.data.movies);

// Mutation
const newMovie = await createMovie({ title: 'New Movie', genre: 'Action' });

// Realtime subscription
const unsubscribe = subscribe(listMoviesRef(), {
  onNext: (result) => console.log(result.data),
  onError: (error) => console.error(error),
});
```

---

