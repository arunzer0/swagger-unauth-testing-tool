import csv
import requests
import json
import random
import string
from urllib.parse import urlencode

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
    else:
        return None

def extract_host_from_url(swagger_url):
    """Extract host from the Swagger JSON URL."""
    parsed_url = requests.utils.urlparse(swagger_url)
    return parsed_url.netloc

def collect_path_parameters(parameters):
    """Filter path-level parameters."""
    return [param for param in parameters if param.get('in') == 'path']

def fetch_and_test_apis(input_csv, output_csv):
    """Read Swagger JSON URLs from CSV, extract data, and make API calls."""
    results = [["HTTP Method", "Endpoint URL", "Path Parameters", "Query Parameters", "Response Status", "Response Body"]]

    with open(input_csv, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            swagger_url = row[0]  # Assuming the Swagger JSON URL is in the first column
            print(f"Fetching Swagger JSON from: {swagger_url}")

            try:
                swagger_response = requests.get(swagger_url)
                swagger_response.raise_for_status()
                swagger_data = swagger_response.json()

                # Extract host and basePath
                host = swagger_data.get('host', extract_host_from_url(swagger_url))
                base_path = swagger_data.get('basePath', '')

                for path, methods in swagger_data.get('paths', {}).items():
                    for method, details in methods.items():
                        if method == 'parameters':  # Skip global parameters
                            continue

                        # Collect path parameters
                        path_params = collect_path_parameters(details.get('parameters', []))
                        
                        # Replace {id}-like placeholders in the URL with generated values
                        full_path = path
                        path_param_values = {}
                        for param in path_params:
                            param_name = param['name']
                            param_type = param.get('type', 'string')
                            generated_value = generate_random_values(param_type)
                            full_path = full_path.replace(f"{{{param_name}}}", str(generated_value))
                            path_param_values[param_name] = generated_value

                        # Construct base URL
                        base_url = f"https://{host}{base_path}{full_path}"
                        print(f"Base URL: {base_url}")

                        # Collect query parameters
                        query_params = [param for param in details.get('parameters', []) if param.get('in') == 'query']

                        # Generate random values for query parameters
                        query_string = {}
                        for param in query_params:
                            param_name = param['name']
                            param_type = param.get('type', 'string')
                            query_string[param_name] = generate_random_values(param_type)

                        # Encode query parameters into URL
                        full_url = f"{base_url}?{urlencode(query_string)}" if query_string else base_url

                        try:
                            response = requests.request(method.upper(), full_url)
                            print(f"Response Status: {response.status_code}")
                            print(f"Response Body: {response.text}")

                            results.append([
                                method.upper(),
                                full_url,
                                json.dumps(path_param_values),  # Represent path parameter values as JSON
                                json.dumps(query_string),      # Represent query params as JSON
                                response.status_code,
                                response.text
                            ])
                        except Exception as e:
                            print(f"Error while testing {method.upper()} {full_url}: {e}")
                            results.append([
                                method.upper(),
                                full_url,
                                json.dumps(path_param_values),
                                json.dumps(query_string),
                                "Error",
                                str(e)
                            ])
            except Exception as e:
                print(f"Error fetching Swagger JSON from {swagger_url}: {e}")
                results.append(["FETCH", swagger_url, "N/A", "N/A", "Error", str(e)])

    # Write results to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(results)

    print(f"Results saved to {output_csv}")

# Usage
input_csv = 'swagger_urls.csv'  # Replace with your input CSV containing Swagger JSON URLs
output_csv = 'api_test_results.csv'  # Specify the output CSV file path
fetch_and_test_apis(input_csv, output_csv)
