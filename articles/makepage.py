PATH = "./test/"
HTML_FILE_NAME = PATH+'article.html'
TEMPLATE = 'template.html'
TEMPLATE_DIR = '.'
ARTICLE_FILE = PATH+'test.html'

#print(ARTICLE_FILE)

from jinja2 import Environment, FileSystemLoader
import json

pagefile = open(ARTICLE_FILE,'r')
page = json.load(pagefile)
pagefile.close()

file_loader = FileSystemLoader(TEMPLATE_DIR)
env = Environment(loader=file_loader)
template = env.get_template(TEMPLATE)

output = template.render(content=page)

file = open(HTML_FILE_NAME,'w')
file.write(output)
file.close()