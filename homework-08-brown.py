#!/usr/bin/env python
# coding: utf-8

# # Exercise 1
# Scrape the following into CSV files. Each one is broken up into multiple tiers – the more you scrape the tougher it is!
# Scrape https://www.congress.gov/members
# * Tier 1: Scrape their name and full profile URL, and additional
# * Tier 2: Separate their state/party/etc into separate columns
# * Advanced: Scrape each person's actual data from their personal project

# In[2]:


from bs4 import BeautifulSoup
import pandas as pd
import requests

url = 'https://www.congress.gov/members'
r = requests.get(url)
bs = BeautifulSoup(r.text)

last_page = bs.select_one('a.last')['href']
last_page = last_page.split('page=')[1]
last_page = int(last_page)

all_members = []

page_no = 1

while page_no <= last_page:

    url = f'https://www.congress.gov/members?pageSize=100&page={page_no}'
    print(f'Scraping {url}')

    r = requests.get(url)
    bs = BeautifulSoup(r.text)


    members = bs.select('ol.basic-search-results-lists li.expanded')

    for member in members:

        member_dict = {}

        name = member.select_one('span.result-heading').text
        member_dict['name'] = name

        profile_url = member.select_one('a')['href']
        profile_url = f'https://www.congress.gov{profile_url}'
        member_dict['url'] = profile_url

        member_details = member.select('span.result-item')

        for detail in member_details:
            heading = detail.select_one('strong').text[:-1]
            content = detail.select_one('span').text.strip()
            member_dict[heading] = content

        all_members.append(member_dict)

    page_no += 1


# In[3]:


df = pd.DataFrame(all_members)
df


# # Exercise 2
# 
# Scrape https://www.marylandpublicschools.org/stateboard/Pages/Meetings-2018.aspx
# * Tier 1: Scrape the date, URL to agenda, URL to board minutes
# * Tier 2: Download agenda items to an "agendas" folder and board minutes to a "minutes" folder

# In[5]:


from bs4 import BeautifulSoup
from datetime import datetime
import requests

url = 'https://www.marylandpublicschools.org/stateboard/Pages/Meetings-2018.aspx'

r = requests.get(url)
bs = BeautifulSoup(r.text)

meetings = bs.select('table tr')

all_meetings = []

for meeting in meetings[-12:]:
    
    date = meeting.select('td')[0].select_one('strong').text.strip()
    date = datetime.strptime(date, '%B %d, %Y')
    
    agenda_url = meeting.select('td')[1].select_one('a')['href']
    agenda_url = f'https://www.marylandpublicschools.org{agenda_url}'
    
    minutes_url = meeting.select('td')[2].select_one('a')['href']
    minutes_url = f'https://www.marylandpublicschools.org{minutes_url}'
    
    meeting_dict = {
        'date': date,
        'agenda_url': agenda_url,
        'minutes_url': minutes_url
    }
    
    all_meetings.append(meeting_dict)
    
all_meetings


# **Download agendas**

# In[6]:


agenda_pdfs = []

for meeting in all_meetings:
    agenda_url = meeting['agenda_url']
    
    r = requests.get(agenda_url)
    bs = BeautifulSoup(r.text)
    
    agenda_pdf = bs.select_one('div#ctl00_PlaceHolderMain_ctl02__ControlWrapper_RichHtmlField a[href$=".pdf"]')['href']
    agenda_pdf = f'https://www.marylandpublicschools.org/{agenda_pdf}'
    agenda_pdfs.append(agenda_pdf)
    
file_content = '\n'.join(agenda_pdfs)

with open("agenda_pdfs.txt", "w") as f:
    f.write(file_content)
    
get_ipython().system('wget -P agendas/ -i agenda_pdfs.txt')


# **Download minutes**

# In[8]:


minutes_urls = []

for meeting in all_meetings:
    minutes_url = meeting['minutes_url']
    minutes_urls.append(minutes_url)

file_content = '\n'.join(minutes_urls)

with open("minutes_urls.txt", "w") as f:
    f.write(file_content)
    
get_ipython().system('wget -P minutes/ -i minutes_urls.txt')


# # Exercise 3
# Scrape http://www.nvmcsd.org/our-school-board/meetings/agendas
# * Tier 1: Scrape the name of the link and the URL
# * Tier 2: Add a column for the date (you'll need to manually edit some, probably [but using pandas!])
# * Tier 3: Download the PDFs but name them after the date

# In[ ]:


from bs4 import BeautifulSoup
import datetime
import re
import requests

url = 'http://www.nvmcsd.org/our-school-board/meetings/agendas'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
}

r = requests.get(url, headers=headers, verify=False)

bs = BeautifulSoup(r.text)

links = bs.select('.wp-block-kadence-pane a[href$=".pdf"]')

urls = []

for link in links:
    url_info = {}
    
    url_info['name'] = link.text
    url_info['url'] = link['href']
    
    date = re.search("^(\w*) (\d*), (202\d) *.", link.text)
    if date:
        month = date.group(1)
        day = date.group(2)
        year = date.group(3)
        url_info['date'] = f'{month}, {day}, {year}'

    urls.append(url_info)
    
df = pd.DataFrame(urls)


# **Manual cleanup of dates**

# In[12]:


df.loc[(df.name.str.startswith('Item #')), 'date'] = 'May 31, 2022'
df.loc[(~df.name.str.startswith('Item #')) & (df.name.str.startswith('Item ')), 'date'] = 'August 10, 2021'
df.loc[df.name.str.startswith('8-10-21'), 'date'] = 'August 10, 2021'
df.loc[df.url.str.contains('4.19.22'), 'date'] = 'April 19, 2022'
df.loc[df.url.str.contains('2.4.22'), 'date'] = 'February 4, 2022'
df.loc[df.url.str.contains('9.21.21'), 'date'] = 'September 21, 2021'
df.loc[df.url.str.contains('10.5.21'), 'date'] = 'October 5, 2021'
df.loc[df.url.str.contains('10.16.21'), 'date'] = 'October 16, 2021'


# **Downloading files**
# 
# This works, but there has to be a better way!
# 
# Looking forward to learning what I should have done!

# In[ ]:


get_ipython().system('mkdir school_board')

def download_file(name, date, url):
    filename = f'school_board/{date}-{name}.pdf'.replace(' ', '_')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
    }
 
    with open(filename, 'wb') as file:
        r = requests.get(url, headers=headers, verify=False)
        file.write(r.content)

df.apply(lambda x: download_file(x['name'], x['date'], x['url']), axis = 1)


# # Exercise 4
# 
# Scrape https://rocktumbler.com/blog/rock-and-mineral-clubs/
# * Tier 1: Scrape all of the name and city
# * Tier 2: Scrape the name, city, and URL
# * Tier 3: Scrape the name, city, URL, and state name (you'll probably need to learn about "parent" nodes)

# In[54]:


url = 'https://rocktumbler.com/blog/rock-and-mineral-clubs/'

r = requests.get(url)

bs = BeautifulSoup(r.text)

clubs = bs.find_all('tr', {'bgcolor': '#FFFFFF'})

all_clubs = []

for club in clubs:
    
    info = club.find_all('td')
    name = info[0].text
    url = info[0].find('a')['href']
    city = info[1].text

    state = club.parent.parent.find('h3').text
    state = state.split(' Rock and Mineral Clubs')[0]
    
    data = {
        'name': name,
        'city': city,
        'state': state,
        'url': url
    }
    
    all_clubs.append(data)
    
df = pd.DataFrame(all_clubs)

df


# In[ ]:




