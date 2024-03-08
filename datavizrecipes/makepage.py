from jinja2 import Environment, FileSystemLoader
import json
import markdown
from markdown.extensions.tables import TableExtension

import urllib.parse

param_file = open('params.json','r')
params = json.load(param_file)
param_file.close()

#print(params['title'])

TITLE = params['title']
SUBTITLE = params['subtitle']
IMAGE = params['image']

TEMPLATE = 'template.html'
ARTICLE_FILE = "article.md"
FILE_NAME = urllib.parse.quote(TITLE.replace(" ", "_"))+".html"



with open(f'{ARTICLE_FILE}', 'r') as reader:
    md = reader.read()
content = markdown.markdown(md, extensions=['fenced_code',TableExtension(use_align_attribute=True)])

print(content)

file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)
template = env.get_template(TEMPLATE)

output = template.render(content=content, title = TITLE, subtitle = SUBTITLE, image = IMAGE)
print(FILE_NAME)
f = FILE_NAME
print(f)
file = open(f,'w')
file.write(output)
file.close()
