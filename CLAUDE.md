# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python tool for analyzing GitHub organization CODEOWNERS files. The main functionality is contained in `githubparser.py`, which provides a `GitHubCodeOwnersAnalyzer` class that:

- Fetches all repositories from a GitHub organization using the GitHub API
- Retrieves CODEOWNERS files from each repository's `.github` directory  
- Parses the primary codeowner from each CODEOWNERS file
- Outputs results to CSV format with repository URLs and primary owners
- Handles GitHub API rate limiting and pagination

## Development Commands

- **Run the main script**: `uv run githubparser.py --org <organization> --token <github_token>`
- **Install dependencies**: `uv sync`
- **Add new dependencies**: `uv add <package>`

## Environment Setup

The script uses environment variables for configuration:
- `GITHUB_TOKEN`: GitHub personal access token (can also be passed via `--token` argument)
- Create a `.env` file in the project root to store the token locally

## Architecture Notes

- Single-file architecture with the main `GitHubCodeOwnersAnalyzer` class
- Uses `requests.Session` for GitHub API calls with proper headers and authentication
- Implements rate limiting checks to avoid exceeding GitHub API limits
- Parses CODEOWNERS files by finding the first non-comment line and extracting the first owner
- CSV output includes repository URL, name, and primary owner (or "No CODEOWNERS file")