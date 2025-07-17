from jinja2 import Environment, FileSystemLoader
import json

# Load template
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('README.md.j2')

# Load data
with open('models_enriched.json', 'r', encoding='utf-8') as f:
    models = json.load(f)

# Render and write
readme = template.render(models=models, date='{{DATE}}')
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
