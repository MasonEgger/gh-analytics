#!/usr/bin/env python3
"""
GitHub Organization CODEOWNERS Analyzer

This script retrieves all repositories in a GitHub organization and extracts
the primary codeowner from the CODEOWNERS file (if it exists) in the .github directory.
Outputs results to a CSV file while minimizing API calls to avoid rate limits.

Requirements:
    pip install requests pandas python-dotenv

Usage:
    python github_codeowners_analyzer.py
"""

import argparse
import csv
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class GitHubCodeOwnersAnalyzer:
    def __init__(self, token: str, org: str):
        """
        Initialize the analyzer with GitHub token and organization name.

        Args:
            token: GitHub personal access token
            org: GitHub organization name
        """
        self.token = token
        self.org = org
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHub-CodeOwners-Analyzer",
            }
        )
        self.base_url = "https://api.github.com"

    def check_rate_limit(self) -> None:
        """Check current rate limit status and wait if necessary."""
        url = f"{self.base_url}/rate_limit"
        response = self.session.get(url)

        if response.status_code == 200:
            data = response.json()
            remaining = data["resources"]["core"]["remaining"]
            reset_time = data["resources"]["core"]["reset"]

            print(f"Rate limit: {remaining} requests remaining")

            if remaining < 10:  # Conservative threshold
                wait_time = reset_time - int(time.time()) + 10
                if wait_time > 0:
                    print(f"Rate limit low. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)

    def get_repositories(self, include_public: bool = True, include_private: bool = True, include_archived: bool = True) -> List[Dict]:
        """
        Get repositories for the organization using pagination with filtering options.

        Args:
            include_public: Whether to include public repositories
            include_private: Whether to include private repositories
            include_archived: Whether to include archived repositories

        Returns:
            List of repository dictionaries matching the filter criteria
        """
        repositories = []
        page = 1
        per_page = 100  # Maximum allowed by GitHub API

        print(f"Fetching repositories for organization: {self.org}")

        while True:
            self.check_rate_limit()

            url = f"{self.base_url}/orgs/{self.org}/repos"
            params = {"page": page, "per_page": per_page, "type": "all", "sort": "name"}

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                print(f"Error fetching repositories: {response.status_code}")
                print(f"Response: {response.text}")
                break

            data = response.json()

            if not data:  # No more repositories
                break

            # Filter repositories based on criteria
            filtered_repos = []
            for repo in data:
                # Check if repository matches filtering criteria
                if repo.get("archived", False) and not include_archived:
                    continue
                if repo.get("private", False) and not include_private:
                    continue
                if not repo.get("private", False) and not include_public:
                    continue
                    
                filtered_repos.append(repo)
            
            repositories.extend(filtered_repos)
            print(f"Fetched page {page}: {len(filtered_repos)} repositories (filtered from {len(data)})")

            if len(data) < per_page:  # Last page
                break

            page += 1

        print(f"Total repositories found: {len(repositories)}")
        return repositories

    def get_codeowners_content(self, repo_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Get CODEOWNERS file content from all GitHub-supported locations.
        
        GitHub searches for CODEOWNERS files in this order:
        1. .github/CODEOWNERS
        2. CODEOWNERS (root directory)
        3. docs/CODEOWNERS

        Args:
            repo_name: Repository name

        Returns:
            Tuple of (CODEOWNERS file content or None, location where found or None)
        """
        
        # GitHub-supported locations in search order
        locations = [
            ".github/CODEOWNERS",
            "CODEOWNERS", 
            "docs/CODEOWNERS"
        ]
        
        import base64
        
        for location in locations:
            url = f"{self.base_url}/repos/{self.org}/{repo_name}/contents/{location}"
            response = self.session.get(url)

            if response.status_code == 200:
                data = response.json()
                if data.get("content"):
                    # Decode base64 content
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return content, location
        
        return None, None

    def parse_primary_codeowner(self, content: str) -> Optional[str]:
        """
        Parse CODEOWNERS file content to extract the primary owner.
        
        Supports two formats:
        1. Traditional: "* @owner" or "/path @owner"
        2. Team-only: "@team" on its own line

        Args:
            content: CODEOWNERS file content

        Returns:
            Primary codeowner (usually from the first non-comment line)
        """
        if not content:
            return None

        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            
            # Case 1: Line starts with @ (team/user only format)
            if line.startswith("@") and len(parts) == 1:
                primary_owner = line[1:]  # Remove @ prefix
                return primary_owner
            
            # Case 2: Traditional CODEOWNERS format: pattern owner1 owner2 ...
            if len(parts) >= 2:
                # First part is the pattern, subsequent parts are owners
                owners = parts[1:]
                # Return the first owner, removing @ if present
                primary_owner = owners[0]
                if primary_owner.startswith("@"):
                    primary_owner = primary_owner[1:]
                return primary_owner

        return None

    def analyze_repositories(self, repositories: List[Dict]) -> List[Dict]:
        """
        Analyze repositories to extract CODEOWNERS information.

        Args:
            repositories: List of repository dictionaries

        Returns:
            List of dictionaries with repository URL and primary owner
        """
        results = []
        total_repos = len(repositories)

        print(f"\nAnalyzing CODEOWNERS for {total_repos} repositories...")

        for i, repo in enumerate(repositories, 1):
            repo_name = repo["name"]
            repo_url = repo["html_url"]

            print(f"[{i}/{total_repos}] Processing: {repo_name}")

            # Check rate limit periodically
            if i % 50 == 0:
                self.check_rate_limit()

            # Get CODEOWNERS content and location
            codeowners_content, codeowners_location = self.get_codeowners_content(repo_name)

            if codeowners_content:
                primary_owner = self.parse_primary_codeowner(codeowners_content)
                has_codeowner_file = True
            else:
                primary_owner = None
                has_codeowner_file = False
                codeowners_location = None

            results.append(
                {
                    "repository_url": repo_url,
                    "repository_name": repo_name,
                    "has_codeowner_file": has_codeowner_file,
                    "codeowners_file_location": codeowners_location,
                    "primary_owner": primary_owner or "No CODEOWNERS file",
                }
            )

            # Small delay to be respectful to the API
            time.sleep(0.1)

        return results

    def save_to_csv(self, results: List[Dict], filename: str) -> None:
        """
        Save results to CSV file.

        Args:
            results: List of result dictionaries
            filename: Output CSV filename
        """
        fieldnames = ["repository_url", "repository_name", "has_codeowner_file", "codeowners_file_location", "primary_owner"]

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\nResults saved to: {filename}")

        # Print summary
        total_repos = len(results)
        repos_with_codeowners = sum(
            1 for r in results if r["has_codeowner_file"]
        )

        print(f"Summary:")
        print(f"  Total repositories: {total_repos}")
        print(f"  Repositories with CODEOWNERS: {repos_with_codeowners}")
        print(
            f"  Repositories without CODEOWNERS: {total_repos - repos_with_codeowners}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze GitHub organization CODEOWNERS files"
    )
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument(
        "--token", help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--output", default="codeowners_analysis.csv", help="Output CSV filename"
    )
    
    # Repository type filtering arguments
    parser.add_argument(
        "--all", action="store_true", help="Include all repositories (public, private, and archived)"
    )
    parser.add_argument(
        "--public", action="store_true", help="Include public repositories"
    )
    parser.add_argument(
        "--private", action="store_true", help="Include private repositories"
    )
    parser.add_argument(
        "--archived", action="store_true", help="Include archived repositories"
    )

    args = parser.parse_args()

    # Validate repository type flags
    if not (args.all or args.public or args.private or args.archived):
        print("Error: You must specify which repositories to analyze.")
        print("Choose one of the following options:")
        print("  --all       Include all repositories (public, private, and archived)")
        print("  --public    Include public repositories")
        print("  --private   Include private repositories") 
        print("  --archived  Include archived repositories")
        print("")
        print("You can combine --public, --private, and --archived flags.")
        print("Example: --public --private (excludes archived repos)")
        return
    
    # Validate mutually exclusive flags
    if args.all and (args.public or args.private or args.archived):
        print("Error: --all flag cannot be used with --public, --private, or --archived flags.")
        print("Choose either:")
        print("  --all                        (for all repositories)")  
        print("  --public --private --archived (for specific combinations)")
        return

    # Get token from argument or environment variable
    token = args.token or os.getenv("GITHUB_TOKEN")

    if not token:
        print("Error: GitHub token is required. Either:")
        print("  1. Use --token argument")
        print("  2. Set GITHUB_TOKEN environment variable")
        print("  3. Create a .env file with GITHUB_TOKEN=your_token")
        return

    try:
        analyzer = GitHubCodeOwnersAnalyzer(token, args.org)

        # Determine repository filtering options
        if args.all:
            include_public = include_private = include_archived = True
        else:
            include_public = args.public
            include_private = args.private
            include_archived = args.archived

        # Get repositories with filtering
        repositories = analyzer.get_repositories(
            include_public=include_public,
            include_private=include_private, 
            include_archived=include_archived
        )

        if not repositories:
            print("No repositories found or error occurred")
            return

        # Analyze repositories for CODEOWNERS
        results = analyzer.analyze_repositories(repositories)

        # Save results to CSV
        analyzer.save_to_csv(results, args.output)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
