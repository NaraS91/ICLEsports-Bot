import re
import requests

def extract_champions():
  url = 'https://na.leagueoflegends.com/en-us/champions/'

  response = requests.get(url)

  if response.status_code != 200:
    return {}

  p = re.compile(r'href="/en-us/champions/(\w*)/')
  champs = p.findall(response.text)
  return champs