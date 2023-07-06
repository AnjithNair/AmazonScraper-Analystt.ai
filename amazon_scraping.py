import re
import time

import pandas as pd
import requests
import argparse
import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs
from tqdm import tqdm


def get_product_details(url, driver):
    """
    Scrapes product details from a given URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        dict: A dictionary containing the scraped product details.
    """

    driver.get(url)

    # Retrieve the HTML content
    html_content = driver.page_source
    soup = bs(html_content, "html.parser")

    # Retrieve details from one type of element selector
    details = soup.select("#detailBullets_feature_div > ul > li")

    if details:
        responses = {}

        # Process each detail
        for detail in details:
            text = re.sub(" +", " ", detail.text.strip("\n"))
            text = (
                text.encode("utf-8", errors="ignore").decode("utf-8").replace("\n", " ")
            )
            text = re.sub(r"[\n\u200f\u200e]", "", text)
            text = re.sub(" +", " ", text).strip()
            text = text.split(" : ", maxsplit=1)

            if len(text) == 2:  # ensuring key, value pairs
                resp = {text[0]: text[1]}
                responses.update(resp)
    else:
        # If details are not found, try another type of element selector
        details = soup.select("#productDetails_detailBullets_sections1")

        if details:
            # Parse details using Pandas if found
            responses = pd.read_html(str(details[0]))[0].set_index(0)[1].to_dict()

            # Remove unwanted key
            if "Customer Reviews" in responses:
                responses.pop("Customer Reviews")
        else:
            responses = {}

    # Retrieve product description
    description = soup.select("#feature-bullets > ul > li")
    description = {"Description": "\n".join([i.text for i in description])}

    # Retrieve additional product description
    product_description = {
        "ProductDescription": re.sub(
            r"\s+", " ", soup.select("#aplus_feature_div")[0].text
        ).strip()
    }

    # Merge all the responses into a single dictionary
    responses.update(product_description)
    responses.update(description)

    return responses


def get_data(page_no: int, more_info: bool = True) -> pd.DataFrame:
    """
    Fetches data from Amazon search results for bags.

    Args:
        page_no (int): The page number of search results to fetch.
        more_info (bool, optional): Whether to fetch additional product details. Defaults to True.

    Returns:
        pd.DataFrame: DataFrame containing the fetched data.
    """
    # Headers for the HTTP request
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Dnt": "1",
        "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }

    # Construct the URL for the search page
    url = f"https://www.amazon.in/s?k=bags&page={page_no}&crid=2M096C61O4MLT&qid=1688625292&sprefix=ba%2Caps%2C283&ref=sr_pg_{page_no}"
    print(url)

    # initialized patched selenium chrome driver
    driver = uc.Chrome(headless=True, use_subprocess=False)

    # Send HTTP GET request to the URL with headers
    response = requests.get(url, headers=headers)

    # Check if the response was successful
    if response.status_code != 200:
        raise Exception(f"The response code is {response.status_code}")

    # Parse the HTML content of the response
    soup = bs(response.content, "html.parser")

    # Find all search results on the page
    search_results = soup.findAll(
        "div", attrs={"data-component-type": "s-search-result"}
    )

    responses = []  # Initialize an empty list to store the responses

    # Iterate over the search results
    for result in search_results:
        try:
            asin = result.get(
                "data-asin", ""
            )  # Get the value of "data-asin" attribute from the result
            if asin:
                # Extract product details from the result
                product_name = result.select("h2 a.a-link-normal.a-text-normal")[0].text
                product_url = f"https://www.amazon.in/dp/{asin}"
                product_rating = result.select(
                    "div.a-row.a-size-small span:nth-of-type(1)"
                )[0].get("aria-label")
                product_price = result.select("span.a-price-whole")[0].text
                product_review = result.select(
                    "div.a-row.a-size-small span:nth-of-type(2)"
                )[0].get("aria-label")

                # Create a response dictionary with the extracted product details
                response = {
                    "asin": asin,
                    "name": product_name,
                    "url": product_url,
                    "rating": product_rating,
                    "price": product_price,
                    "review": product_review,
                }

                if more_info:
                    # Retrieve additional data for the product
                    additional_data = get_product_details(product_url, driver)
                    response.update(
                        additional_data
                    )  # Add the additional data to the response dictionary

                responses.append(
                    response
                )  # Add the response dictionary to the list of responses
        except Exception as e:
            print(e)
            continue  # If there's an exception, skip to the next iteration

    driver.quit()

    # Create a pandas DataFrame from the list of responses
    return pd.DataFrame(responses)


def main(pages_to_scrape: int):
    """
    Scrapes data from multiple pages on Amazon and saves the results to a CSV file.

    Args:
        pages_to_scrape (int): The number of pages to scrape.

    Returns:
        None
    """

    dfs = []  # List to store individual dataframes from each page
    for page in tqdm(range(1, pages_to_scrape + 1)):
        df = get_data(page, more_info=True)  # Scrape data from a specific page
        dfs.append(df)  # Append the dataframe to the list

    final_data = pd.concat(dfs)  # Combine all dataframes into a single dataframe
    final_data = final_data[
        [
            "asin",
            "name",
            "url",
            "rating",
            "price",
            "review",
            "Description",
            "Manufacturer",
            "ProductDescription",
        ]
    ]  # Select specific columns in the desired order
    final_data = final_data.rename(
        columns={
            "asin": "ASIN",
            "url": "ProductUrl",
            "rating": "ProductRating",
            "price": "ProductPrice",
            "review": "ProductReview",
        }
    )  # Rename columns
    final_data.reset_index(drop=True, inplace=True)  # Reset the index
    final_data.to_csv(
        "amazon_scraped_data.csv", index=False
    )  # Save the data to a CSV file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amazon Scraping Logic.")
    parser.add_argument(
        "--page_num", type=int, default=20, help="Specify how many pages to scrape."
    )
    args = parser.parse_args()

    main(args.page_num)
