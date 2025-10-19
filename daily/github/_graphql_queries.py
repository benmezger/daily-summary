#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-15 Sat 00:17>


from typing import Final

issues: Final[str] = """
{{
  search(query: "author:{username} created:{created_at}", type: ISSUE, first: 100) {{
    edges {{
      node {{
        ... on Issue {{
          id
          title
          body
          url
          repository {{
            nameWithOwner
          }}
          createdAt
          updatedAt
          state
        }}
        ... on PullRequest {{
          id
          title
          body
          url
          repository {{
            nameWithOwner
          }}
          createdAt
          updatedAt
          state
          mergedAt
        }}
      }}
    }}
  }}
}}
"""

reviews: Final[str] = """
{{
  search(
    first: 100
    query: "updated:{updated_at} type:pr reviewed-by:{username}"
    type: ISSUE
  ) {{
    edges {{
      node {{
        ... on PullRequest {{
          title
          id
          url
          state
          createdAt
          repository {{
            nameWithOwner
          }}
          reviews(last: 10) {{
            nodes {{
              author {{
                login
              }}
              state
              createdAt
              updatedAt
              url
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

tags: Final[str] = """
{{
  viewer {{
    login
    repositories(first: 100, ownerAffiliations: [OWNER]) {{
      nodes {{
        nameWithOwner
        refs(refPrefix: "refs/tags/", first: 100, orderBy: {{field: TAG_COMMIT_DATE,
             direction: ASC}}) {{
          nodes {{
            name
            target {{
              ... on Tag {{
                tagger {{
                  name
                  email
                  date
                }}
              }}
              ... on Commit {{
                committedDate
                author {{
                  name
                  email
                  date
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""
