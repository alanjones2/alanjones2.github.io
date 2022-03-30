HTML_FILE_NAME ='index.html'
TEMPLATE = 'index3template.html'
TEMPLATE_DIR = 'templates'
ARTICLES_FILE = 'pages.json'

from jinja2 import Environment, FileSystemLoader
import json

pagefile = open(ARTICLES_FILE,'r')
pages = json.load(pagefile)
pagefile.close()

file_loader = FileSystemLoader(TEMPLATE_DIR)
env = Environment(loader=file_loader)
template = env.get_template(TEMPLATE)

output = template.render(pages=pages)

file = open(HTML_FILE_NAME,'w')
file.write(output)
file.close()