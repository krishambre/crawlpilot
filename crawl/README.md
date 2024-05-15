# crawlPilot

## Description

crawlPilot is a Django-based web application designed to crawl and summarise a list of URLs asynchronously. For each request, it generates a unique request ID to track the progress of their URL processing requests.

## Installation
1. Clone the repository: `git clone`
2. Navigate to the project directory: `cd crawlpilot`
3. Install the required packages: `pip install -r requirements.txt`

## Usage

To use this application, send a POST request to the `/bulkScrape` endpoint with a JSON body containing a list of URLs. The application will return a unique request ID.

You can check the status of your request by sending a GET request to the `/result` endpoint with your request ID. It returns status as "in progress" while crawling, and returns the list of responses for each url, when crawling is complete.

Use `/report` API which returns a paginated list of all URLs crawled to date, without any duplicate urls.

You can also use the `/cosine` API to create a vector embedding of the text
in each url and return a cosine distance matrix for each URL pair.

