#!/bin/bash

# Directories relative to the project root
SIGMA_REPO_DIR="./sigma"
YAML_OUTPUT_DIR="./all_sigma_rules"

# Ensure directories are created at the right place
mkdir -p "$SIGMA_REPO_DIR"
mkdir -p "$YAML_OUTPUT_DIR"

# Clone or update the Sigma repository
if [ ! -d "$SIGMA_REPO_DIR" ]; then
    git clone https://github.com/SigmaHQ/sigma.git "$SIGMA_REPO_DIR"
else
    cd "$SIGMA_REPO_DIR"
    git pull origin master
    cd ..
fi

# Copy yml files to the output directory
declare -a directories=("rules" "rules-compliance" "rules-dfir" "rules-emerging-threats" "rules-placeholder" "rules-threat-hunting")
for dir in "${directories[@]}"; do
    find "$SIGMA_REPO_DIR/$dir" -name '*.yml' -exec cp {} "$YAML_OUTPUT_DIR" \;
done

echo "Updated .yaml files in $YAML_OUTPUT_DIR"
