#!/bin/bash

# Directories relative to the project root
SIGMA_REPO_DIR="./sigma"
YAML_OUTPUT_DIR="./all_sigma_rules"

# Clone the Sigma repository (TODO: add update option)
git clone https://github.com/SigmaHQ/sigma.git "$SIGMA_REPO_DIR"

# Copy yml files to the output directory
declare -a directories=("rules" "rules-compliance" "rules-dfir" "rules-emerging-threats" "rules-placeholder" "rules-threat-hunting")
for dir in "${directories[@]}"; do
    find "$SIGMA_REPO_DIR/$dir" -name '*.yml' -exec cp {} "$YAML_OUTPUT_DIR" \;
done

echo "Updated .yaml files in $YAML_OUTPUT_DIR"
