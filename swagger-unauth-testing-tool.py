import csv
import requests
import json
import random
import string
from urllib.parse import urlparse

def generate_random_values(data_type):
    """Generate random values based on the data type."""
    if data_type == 'string':
        return ''.join(random.choices(string.ascii_letters, k=10))
    elif data_type == 'integer':
        return random.randint(1, 100)
    elif data_type == 'boolean':
        return random.choice([True, False])
    elif data_type == 'number':
        return random.uniform(1, 100)
    elif data_type == 'array':
        return [random.randint(1, 10) for _ in range(5)]
    else:
        return None

def extract_host_from_url(swagger_url):
    """Extract host from the Swagger JSON URL."""
    parsed_url = urlparse(swagger_url)
    return parsed_url.netloc

def test_endpoints_from_csv(input_csv, output_csv):
    """Read Swagger JSON URLs from CSV and test their endpoints."""
    results = [["Method", "URL", "Version", "Status Code", "Response Body"]]

    with open(input_csv, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            swagger_url = row[0]  # Assuming the Swagger URL is in the first column
            print(f"Fetching Swagger file from: {swagger_url}")

            try:
                swagger_response = requests.get(swagger_url)
                swagger_response.raise_for_status()
                swagger_data = swagger_response.json()

                # Extract host from Swagger or fallback to Swagger URL
                host = swagger_data.get('host', extract_host_from_url(swagger_url))
                base_path = swagger_data.get('basePath', '')

                for path, methods in swagger_data.get('paths', {}).items():
                    for method, details in methods.items():
                        # Extract version dynamically from basePath or path
                        version = ''
                        if 'v' in base_path or 'v' in path:  # Look for versions like "v1", "v2"
                            version_parts = path.split('/')
                            version = next((part for part in version_parts if part.startswith('v')), '')
                            if not version:  # Fallback to basePath
                                version_parts = base_path.split('/')
                                version = next((part for part in version_parts if part.startswith('v')), '')

                        # Construct URL
                        url = f"https://{host}/{version}{path}" if version else f"https://{host}{path}"
                        print(f"Testing {method.upper()} {url} with version: {version}")

                        # Generate random parameters
                        params = {}
                        if 'parameters' in details:
                            for param in details['parameters']:
                                param_name = param['name']
                                param_type = param.get('type')
                                params[param_name] = generate_random_values(param_type)

                        try:
                            response = requests.request(method, url, params=params)
                            print(f"Status Code: {response.status_code}")
                            print(f"Response Body: {response.text}")

                            results.append([method.upper(), url, version, response.status_code, response.text])
                        except Exception as e:
                            print(f"Error while testing {method.upper()} {url}: {e}")
                            results.append([method.upper(), url, version, "Error", str(e)])
            except Exception as e:
                print(f"Error fetching Swagger file from {swagger_url}: {e}")
                results.append(["FETCH", swagger_url, "N/A", "Error", str(e)])

    # Write results to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(results)

    print(f"Results saved to {output_csv}")

# Usage
input_csv = 'swagger_urls.csv'  # Replace with your CSV containing Swagger JSON URLs
output_csv = 'swagger_test_results.csv'  # Specify the output CSV file path
test_endpoints_from_csv(input_csv, output_csv)