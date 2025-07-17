# Usage Examples

The CLI provides quick access to search and metadata enrichment features.

```bash
# Fetch the latest metadata
python enrich/main.py --limit 10

# Search for models matching a term
atlas-cli search llama
```

## Command Help

```bash
$ python -m atlas_cli.main --help
Usage: python -m atlas_cli.main [OPTIONS] COMMAND [ARGS]...

 ModelAtlas CLI

Options:
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or customize the installation.
  --help                Show this message and exit.

Commands:
  trace  Run the enrichment and trust score trace.
  init   Bootstrap local environment by creating a .env file.
```

```bash
$ python -m atlas_cli.main trace --help
Usage: python -m atlas_cli.main trace [OPTIONS]

Run the enrichment and trust score trace.

Options:
  --input PATH      Input file path
  --output PATH     Output file path
  --tasks-yml PATH  Tasks YAML file path
  --help            Show this message and exit.
```

```bash
$ python -m atlas_cli.main init --help
Usage: python -m atlas_cli.main init [OPTIONS]

Bootstrap local environment by creating a .env file.

Options:
  --help  Show this message and exit.
```

