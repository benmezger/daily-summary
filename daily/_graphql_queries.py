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
