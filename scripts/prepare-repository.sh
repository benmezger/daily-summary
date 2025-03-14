#!/usr/bin/env bash

# Author: Ben Mezger
#
# Description: Prepares summaries repository,
# creating yearly milestones and labels.

REPOSITORY="benmezger/summaries"

echo "Creating labels"
gh label create summary \
	--description "Daily summary for particular date" \
	--color "3171BE" \
	--repo $REPOSITORY \
	--force

gh label create no-summary \
	--description "No summary available" \
	--color "f9d0c4" \
	--repo $REPOSITORY \
	--force

echo "Creating milestone"
gh api --method POST \
	-H "Accept: application/vnd.github.v3+json" \
	/repos/$REPOSITORY/milestones \
	-f title='2025' \
	-f state='open' \
	-f description='2025 daily summaries' \
	-f due_on='2025-12-31T23:59:00Z'
