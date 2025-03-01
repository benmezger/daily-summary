# Daily Summary

## Requirements
1. Ollama installed
2. Ollama `mistral` model
3. Python + UV

## Running

### Listing todays PR

``` sh
uv run python -m daily list-prs
```

### Listing PRs on a specific date

``` sh
uv run python -m daily list-prs --date 2025-02-28
```

### Showing account

``` sh
uv run python -m daily account
```

### Generating daily summaries based on PRs

``` sh
uv run python -m daily daily-summary
```

### Generating daily summaries based on PRs on a specific date

``` sh
uv run python -m daily daily-summary --date 2025-02-28
```
