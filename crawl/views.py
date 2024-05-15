import json
import requests
import time
import random
import threading
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from bs4 import BeautifulSoup
from threading import Lock
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from summarizer import Summarizer
from .models import ScrapeResult
from .models import RequestMap
from .serializers import ScrapeResultSerializer

counter_lock = Lock()

request_counter = {}

#request_status_map = {}

def scrape_url(request):

    url = request.GET.get('url', None)
    if url is None:
        return JsonResponse({'error': 'Missing URL'}, status=400)
    return JsonResponse({url: scrape(url)})

@csrf_exempt
def bulk_scrape(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST method is allowed')

    try:
        data = json.loads(request.body)
        urls = data['urls']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Missing URLs in request body'}, status=400)

    # Generate a request ID based on the current time
    request_id = str(int(time.time())) + str(random.randint(1000, 9999))

    # Set the status for this request to "in progress"
    #request_status_map[request_id] = "in progress"
    request_map = RequestMap(request_id=request_id, status='pending')
    request_map.save()

    request_len = len(urls)

    request_counter[request_id] = 0

    for url in urls:
        thread = threading.Thread(target=async_scrape, args=(request_id, url, request_len))
        thread.start()

    return JsonResponse({'status': 'success', 'request_id': request_id})

def fetch(session, url):
    with session.get(url) as response:
        return response.text()
    
def async_scrape(request_id, url, request_len):
    response = requests.get(url,timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1').text if soup.find('h1') else "No title found"
    model = Summarizer()
    summary = model(soup.get_text())
    links = [a['href'] for a in soup.find_all('a', href=True)]
    links_json = json.dumps(links)  # Convert the list of links to a JSON string
    result = ScrapeResult(request_id=request_id, url=url, title=title, summary=summary, links=links_json)
    result.save()
     # After the scraping is done, increment the counter
    with counter_lock:
        request_counter[request_id] += 1
    print("Counter:", request_counter[request_id])
    # If all URLs have been processed, set the status to "complete"
    if request_counter[request_id] == request_len:
        with counter_lock:
            #request_status_map[request_id] = "complete"
            request_map = RequestMap.objects.get(request_id=request_id)
            request_map.status = 'completed'
            request_map.save()

def scrape(url):

    response = requests.get(url,timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1').text if soup.find('h1') else "No title found"
    model = Summarizer()
    summary = model(soup.get_text())
    links = [a['href'] for a in soup.find_all('a', href=True)]

    return {'title': title, 'summary': summary, 'links': links}

def get_scrape_results(request,request_id):
    if RequestMap.objects.get(request_id=request_id).status != "completed":
        return JsonResponse({'status': 'in progress'})

    results = ScrapeResult.objects.filter(request_id=request_id)
    if not results:
        return JsonResponse({'error': 'No results found for this request ID'}, status=404)

    # Create a dictionary where each key is a URL and the value is another dictionary with title and links
    result_dict = {result.url: {'title': result.title, 'summary': result.summary,'links': result.links} for result in results}

    return JsonResponse({request_id: result_dict})

def get_cosine_similarity(request, request_id):
    # Get the results for the given request_id
    results = ScrapeResult.objects.filter(request_id=request_id)
    if not results:
        return JsonResponse({'error': 'No results found for this request ID'}, status=404)

    # Extract the text and URL from each result
    texts = [result.summary for result in results]
    urls = [result.url for result in results]

    # Create a TF-IDF vectorizer and fit it to the texts
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(texts)

    # Calculate the cosine similarity between each pair of vectors
    similarity_matrix = cosine_similarity(vectors)

    url_to_similarity = {}
    for i, url1 in enumerate(urls):
        # Exclude the self-similarity row
        similarity = {urls[j]: similarity_matrix[i][j] for j in range(len(urls)) if i != j}
        url_to_similarity[url1] = similarity

    return JsonResponse({request_id: url_to_similarity})

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ReportView(generics.ListAPIView):
    queryset = ScrapeResult.objects.values('url').distinct()
    serializer_class = ScrapeResultSerializer
    pagination_class = StandardResultsSetPagination