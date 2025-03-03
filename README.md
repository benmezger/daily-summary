# Daily Summary

## Requirements
1. Ollama installed
2. Ollama `mistral` model
3. Python + UV

## Running

### Listing todays PR

``` sh
uv run python -m daily list-issues
```

### Listing PRs from a specific date

``` sh
uv run python -m daily list-issues --date 2025-02-28
```

### Listing commits from a specific date

``` sh
uv run python -m daily list-commits --date 2025-02-28
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

## Using the Action cronjob

1. Fork the repository
2. Create a Github [token](https://github.com/settings/tokens/new) with the
   following permissions:
    1. `repo`
        1. Check all
    2. `admin:org`
        1. Check `read:org`
    3. `user`
        1. Check all
3. Add your newly created token to your CI secrets with the name `GH_TOKEN`. See
   [guide](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository)
   for more information on how to do that
4. Replace value of `SUMMARY_REPOSITORY` and `SUMMARY_ASSIGNEE` in the [daily
   action's](./.github/workflows/daily.yaml) env with your summary repository
   and assignee.
