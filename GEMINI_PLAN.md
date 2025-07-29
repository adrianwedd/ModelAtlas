# ⏺ 🧹 ModelAtlas Repository Cleanup Tasklist

  🚨 High Priority - Remove Immediately

  Debug & Temporary Files

- Delete debug HTML files
  - debug_deepseek-r1.html
  - debug_deepseek-r1_tags.html
  - temp_ollama_page.html
  - ollama_debug_dumps/llama2_tags_page.html
- Remove debug directory
  - ollama_debug_dumps/ (entire directory)

  Log Files (Choose retention policy)

- Clean log files - Choose approach:
  - Option A: Delete all: *.log files (enrichment.log, hf_scraper.log, ollama_scraper.log)
  - Option B: Keep recent, archive old
  - Option C: Add to .gitignore and remove from tracking

  🧽 Medium Priority - Consolidate & Organize

  Unused/Orphaned Scripts

- Review unused scripts
  - similarity_engine.py (296 lines, not referenced anywhere)
  - generate_readme.py (mentioned in tasks.yml/CONTRIBUTING but may be legacy)
  - generate_visuals.py (mentioned in tasks.yml/CONTRIBUTING but may be legacy)

  Empty Directories

- Remove empty directory
  - codex/ (completely empty)

  Migration Artifact

- Remove migration script (after migration complete)
  - migrate_tasks_to_issues.py (one-time use script)

  📋 Documentation & Organization

  File Structure Optimization

- Consider consolidating prompt files
  - LLM_ENRICHMENT_PROMPTS.md
  - LLM_PROMPTS.md
  - enhanced_enrichment_prompts.md
  - (May contain duplicate/overlapping content)

  Data File Review

- Audit root-level data files
  - models_enriched.json (may duplicate data in enriched_outputs/)
  - models_raw.json (may duplicate data in data/ or models/)

  🔄 Git Housekeeping

  Update .gitignore

- Add common ignores
  *.log
  *debug*.html
  temp_*.html
  **debug**
  ollama_debug_dumps/

  LFS Review

- Verify large files are in LFS
  - Check if any JSON files >100MB should be tracked via LFS
  - Confirm enriched_outputs/ and data/ are properly tracked

  🎯 Quick Commands for Gemini

## Remove debug files

  rm debug_deepseek-r1*.html temp_ollama_page.html
  rm -rf ollama_debug_dumps/

## Remove empty directory

  rmdir codex/

## Clean logs (choose one approach)

  rm *.log  # OR move to archive directory

## Review unused scripts (check if they're actually used)

  grep -r "similarity_engine\|generate_readme\|generate_visuals" . --exclude-dir=.git

## Remove migration script (after confirming migration is complete)

  rm migrate_tasks_to_issues.py

  📊 Impact Assessment

- Immediate space savings: ~2-5MB (debug files, logs)
- Organization benefit: Cleaner repository structure
- Risk level: Low (mostly temp/debug files)
- Estimated time: 15-30 minutes
