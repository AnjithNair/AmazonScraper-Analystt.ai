## Amazon Scraper

### Prerequisites

Before running the script, make sure you have the following dependencies installed:

- Python 3.x
- pandas
- requests
- BeautifulSoup
- tqdm
- undetected_chromedriver

You can install these dependencies using:

```
pip install -r requirements.txt
```

### Usage

To use the script, follow these steps:

1. Install the required dependencies.
2. Run the script with the desired number of pages to scrape as an argument. For example, to scrape 10 pages, use the following command:

```
python amazon_scraper.py --page_num 10
```

3. The script will start scraping the data from Amazon search results. It will display a progress bar indicating the progress of the scraping process.
4. Once the scraping is complete, the script will save the scraped data to a CSV file named "amazon_scraped_data.csv" in the same directory.
