import requests

url = 'https://upload.wikimedia.org/wikipedia/commons/5/50/Vincent_van_Gogh_-_Self-portrait_-_Google_Art_Project.jpg'
resp = requests.get(url)
with open('real_test.jpg', 'wb') as f:
    f.write(resp.content)
print('downloaded', len(resp.content))
