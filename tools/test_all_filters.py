import requests

url = "http://100.86.193.4:19828/search"

# Test 1: Fresher jobs in IT
res1 = requests.get(url, params={"category": "it", "limit": 3})
print("Category IT count:", res1.json().get("count"))

# Test 2: Remote / Work from home jobs
res2 = requests.get(url, params={"q": "developer", "location": "Dhaka", "limit": 3})
print("Dhaka Developer count:", res2.json().get("count"))

# Test 3: Pagination (Page 2, 3...)
res3 = requests.get(url, params={"category": "media", "page": 2, "limit": 3})
print("Media Page 2 count:", res3.json().get("count"))
