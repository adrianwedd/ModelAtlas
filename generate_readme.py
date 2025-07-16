from jinja2 import Environment, FileSystemLoader
import json

# Load template
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('README.md.j2')

# Load data
with open('models_enriched.json') as f:
    models = json.load(f)

# Render and write
readme = template.render(models=models, date='{{DATE}}')
with open('README.md', 'w') as f:
    f.write(readme)