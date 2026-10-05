#!/usr/bin/env bash
# Helper script to create and push a release tag to trigger GitHub Actions release pipeline
set -euo pipefail

TAG="${1:-v1.0.0}"

echo "=== Creating Release Tag: $TAG ==="
git tag -a "$TAG" -m "Release $TAG"
echo "Tag $TAG created successfully."
echo ""
echo "To trigger the automated GitHub Actions CI/CD release build, push the tag:"
echo "  git push origin $TAG"
echo ""
echo "Or push to release branch:"
echo "  git push origin release"
