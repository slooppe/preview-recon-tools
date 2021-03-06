import os 
import pprint
from datetime import datetime
from requests import Session, get
from bs4 import BeautifulSoup

pp = pprint.PrettyPrinter(indent=4)
headers = {'Accept':'application/vnd.github.mercy-preview+json'}
s = Session()
s.headers.update(headers)
s.auth = (os.getenv('GITHUB_USER'), os.getenv('GITHUB_TOKEN'))

def badget_md(category, target):
    badge_url = "https://badgen.net/github/{category}/{target}".format(category=category, target=target)
    return "[![{category}]({badge_url})]({badge_url})".format(category=category, badge_url=badge_url)

GITHUB_API_URL = 'https://api.github.com/'
def req_single_repo(url):
    url = GITHUB_API_URL + 'repos/' + url 
    return s.get(url).json()

def req_search_repo(query):
    url = GITHUB_API_URL + 'search/repositories?' + query 
    return s.get(url).json()

def get_daily_star(repo):
    if isinstance(repo, str):
        repo = req_single_repo(repo)

    current = datetime.now()
    created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    past_days = (current - created_at).days
    result = repo['stargazers_count'] / past_days
    print(result, repo['html_url'])
    return result

def get_famous_repos():
    duplicated = []
    req_my_repo = req_single_repo('ksg97031/preview-recon-tools')
    for topic in req_my_repo['topics']:
        repos = req_search_repo('q=topic:{}&sort=stars&order=desc'.format(topic))
        for repo in repos['items']:
            if repo['html_url'] in duplicated:
                continue 

            duplicated.append(repo['html_url'])
            print(repo['html_url'])
            if repo['stargazers_count'] < 100:
                print('No famous', repo['stargazers_count'])
                break
            if not repo['pushed_at'].startswith('2020'):
                print('Old', repo['pushed_at'])
                continue 
            if repo['stargazers_count'] < 500 and get_daily_star(repo) < 1:
                print('No hot')
                continue
            
            yield repo['html_url']

if __name__ == '__main__':
    md = '| Name | URL | Description | Preview | Popularity | Metadata |'
    md += '\n| ---------- | :---------- | :---------- | :-----------: | :---------: | :----------: |'
    preview_md = "\n"
    with open('list.txt') as f:
        data = f.read().strip()
        lines = data.split("\n")
        for famous_repo_url in get_famous_repos():
            if famous_repo_url not in data:
                lines.append(famous_repo_url)
            
        lines = sorted(lines, key=lambda x : get_daily_star(x.split()[0].split('github.com/')[1]), reverse=True)
        for line in lines:
            github_url, *preview_video_url = line.split()

            r = get(github_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            s = soup.find('span', {'itemprop':'about'})
            desc = s.text.strip()
            name = github_url.split("/")[-1]

            categories = ('contributors', 'watchers', 'last-commit', 'open-issues', 'closed-issues')

            target = github_url.split('github.com/')[1]
            popul = badget_md('stars', target)
            badges = list(map(lambda x : badget_md(x, target), categories))
            preview_link = ""
            if preview_video_url:
                preview_link = "[Watch](#{0})".format(name)
                preview_md += "## {name}  \n[![asciicast]({preview_video_url}.svg)]({preview_video_url})\n".format(name=name,preview_video_url=preview_video_url[0])
                
            md += '\n| **{name}** | [{target}]({github_url}) | {desc} | {preview_link} | {popul} | {badges} |'.format(desc=desc, target=target, github_url=github_url, name=name, preview_link=preview_link, popul=popul, badges=' '.join(badges)) 

    with open('README.md', 'w+') as f:
        f.write(md)
        f.write(preview_md)
