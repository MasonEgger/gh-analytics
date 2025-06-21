# GitHub Analytics Tool

A Python tool for gathering various GitHub analytics from organizations. Currently supports CODEOWNERS analysis with plans to expand to additional metrics and insights.

## Features

### CODEOWNERS Analysis
- Fetch repositories from GitHub organizations with filtering options (public, private, archived)
- Extract primary code owners from CODEOWNERS files
- Support multiple CODEOWNERS file formats:
  - Traditional format: `* @owner` or `/path @owner`  
  - Team-only format: `@team` on its own line
- Export results to CSV format with detailed metrics
- Rate limiting and pagination handling for large organizations
- Detailed summary statistics

### Repository Filtering
- Filter by repository type: public, private, archived
- Combine filters or analyze all repositories
- Efficient API usage with client-side filtering

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install dependencies:

```bash
uv sync
```

## Configuration

### GitHub Token

You need a GitHub personal access token to use this tool. Set it using one of these methods:

1. **Environment variable:**
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

2. **Command line argument:**
   ```bash
   uv run githubparser.py --token your_github_token_here --org your-org
   ```

3. **`.env` file** (recommended):
   Create a `.env` file in the project root:
   ```
   GITHUB_TOKEN=your_github_token_here
   ```

### Creating a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope for private repositories, or `public_repo` for public repositories only
3. Copy the token and use it as described above

## Usage

### Basic Usage

You must specify which types of repositories to analyze:

```bash
# Analyze all repositories (public, private, and archived)
uv run githubparser.py --org your-organization --all

# Analyze only public repositories
uv run githubparser.py --org your-organization --public

# Analyze public and private repositories (excluding archived)
uv run githubparser.py --org your-organization --public --private

# Analyze only archived repositories
uv run githubparser.py --org your-organization --archived
```

### Command Line Options

- `--org ORGANIZATION` (required): GitHub organization name
- `--token TOKEN` (optional): GitHub personal access token (can use GITHUB_TOKEN env var instead)
- `--output FILENAME` (optional): Output CSV filename (default: `codeowners_analysis.csv`)

**Repository Filters (choose one):**
- `--all`: Include all repositories (public, private, and archived)
- `--public`: Include public repositories
- `--private`: Include private repositories  
- `--archived`: Include archived repositories

You can combine `--public`, `--private`, and `--archived` flags, but `--all` cannot be used with other flags.

### Examples

```bash
# Analyze all repositories in the 'temporalio' organization
uv run githubparser.py --org temporalio --all

# Analyze only public repositories and save to custom file
uv run githubparser.py --org temporalio --public --output public_repos.csv

# Analyze public and private repositories (no archived)
uv run githubparser.py --org temporalio --public --private

# Use token from command line
uv run githubparser.py --org temporalio --all --token ghp_your_token_here
```

## Output

The tool generates a CSV file with the following columns:

1. `repository_url`: Direct link to the GitHub repository
2. `repository_name`: Name of the repository
3. `has_codeowner_file`: Boolean indicating if a CODEOWNERS file exists
4. `codeowners_file_location`: Location where CODEOWNERS file was found (`.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS`)
5. `primary_owner`: Primary code owner extracted from CODEOWNERS file, or "No CODEOWNERS file"

### Sample Output

```csv
repository_url,repository_name,has_codeowner_file,codeowners_file_location,primary_owner
https://github.com/temporalio/sdk-java,sdk-java,True,.github/CODEOWNERS,temporalio/java-sdk
https://github.com/temporalio/documentation,documentation,True,CODEOWNERS,temporalio/education
https://github.com/temporalio/old-repo,old-repo,False,,No CODEOWNERS file
```

The tool also prints a summary showing:
- Total repositories analyzed
- Number of repositories with CODEOWNERS files
- Number of repositories without CODEOWNERS files

## CODEOWNERS File Support

### File Locations

This tool searches for CODEOWNERS files in all GitHub-supported locations, in the same order as GitHub:

1. `.github/CODEOWNERS` 
2. `CODEOWNERS` (repository root)
3. `docs/CODEOWNERS`

The tool uses the first CODEOWNERS file it finds and records the location in the CSV output.

### File Formats

This tool supports two common CODEOWNERS file formats:

### Traditional Format
```
# Global owner
* @global-owner

# Path-specific owners  
/docs/ @documentation-team
*.py @python-team
```

### Team-Only Format
```
# This repository is maintained by the Education team
@temporalio/education
```

The tool extracts the first non-comment owner it encounters and removes the `@` prefix for cleaner output.

## Rate Limiting

The tool automatically handles GitHub API rate limiting:
- Monitors remaining API calls
- Waits when rate limit is low (< 10 requests remaining)
- Includes small delays between requests to be respectful to the API

## Error Handling

- **404 errors**: Organization not found or insufficient permissions
- **Rate limit exceeded**: Automatic waiting and retry
- **Network issues**: Error messages with response details
- **Invalid tokens**: Clear error messages with setup instructions

## Future Features

This tool is designed to be extensible for additional GitHub analytics:
- Repository activity metrics
- Contributor analysis
- License compliance checking
- Security policy analysis
- And more organizational insights
