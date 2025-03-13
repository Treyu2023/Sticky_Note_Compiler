# Check if GitHub CLI (gh) is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"
    exit 1
}

# Check if authenticated with GitHub CLI
gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "You are not logged in to GitHub CLI. Please run 'gh auth login' to authenticate."
    exit 1
}

# Set the repository path and ensure it exists
$repoPath = "C:\LocalStorage\Sticky_Note_Compiler"
if (-not (Test-Path $repoPath)) {
    New-Item -Path $repoPath -ItemType Directory
}

# Change to the repository directory
Set-Location $repoPath

# Initialize a Git repository if one is not present
if (-not (Test-Path ".git")) {
    git init
    git branch -m main  # set default branch to 'main'
}

# Check and add a remote if none exists yet
$remote = git remote get-url origin 2>$null
if (-not $remote) {
    # Attempt to create the GitHub repository (public).
    $output = gh repo create Treyu2023/Sticky_Note_Compiler --public --source="$repoPath" --remote=origin 2>&1
    if ($output -match "already exists") {
        # If the repository already exists, add it manually
        git remote add origin "https://github.com/Treyu2023/Sticky_Note_Compiler.git"
    }
    elseif ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating repository: $output"
        exit 1
    }
}

# If the repository directory is empty, create a README.md
if (-not (Get-ChildItem -Path $repoPath -Recurse | Where-Object { -not $_.PSIsContainer })) {
    New-Item -Path "$repoPath\README.md" -ItemType File -Value "# Sticky Note Compiler"
    git add README.md
    git commit -m "Initial commit: Add README.md"
    git push -u origin main
}
else {
    # If files already exist, add, commit (if there are changes) and push them
    $status = git status --porcelain
    if ($status) {
        git add .
        git commit -m "Initial commit"
        git push -u origin main
    }
    else {
        Write-Host "No changes to commit."
    }
}
