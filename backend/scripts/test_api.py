#!/usr/bin/env python
"""
Test API endpoints for the educational platform.
"""

import requests
import json
import sys
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Admin credentials (for testing)
USERNAME = "santhanam"
PASSWORD = "Vajjiram@79"  # Change this to your actual admin password


def print_response(response, endpoint):
    """Print API response with color coding."""
    try:
        # Try to parse as JSON
        data = response.json()
        formatted_json = json.dumps(data, indent=2)

        if response.status_code >= 200 and response.status_code < 300:
            status = Fore.GREEN + f"✓ {response.status_code}" + Style.RESET_ALL
        elif response.status_code >= 400:
            status = Fore.RED + f"✗ {response.status_code}" + Style.RESET_ALL
        else:
            status = Fore.YELLOW + \
                f"! {response.status_code}" + Style.RESET_ALL

        print(f"{status} {endpoint}")
        print(f"Response Time: {response.elapsed.total_seconds():.3f}s")

        # Print a sample of the response (not the entire response if it's too large)
        if len(formatted_json) > 500:
            print(formatted_json[:500] + "...\n(response truncated)")
        else:
            print(formatted_json)

    except ValueError:
        # Not JSON, print the text
        print(f"{Fore.YELLOW}! {response.status_code}{Style.RESET_ALL} {endpoint}")
        print(f"Response is not JSON. Text: {response.text[:200]}")


def get_auth_token():
    """Get JWT auth token for API calls."""
    try:
        response = requests.post(
            f"{BASE_URL}/token/",
            json={"username": USERNAME, "password": PASSWORD}
        )

        if response.status_code == 200:
            token = response.json().get("access")
            print(f"{Fore.GREEN}✓ Authentication successful{Style.RESET_ALL}")
            return token
        else:
            print(
                f"{Fore.RED}✗ Authentication failed: {response.status_code}{Style.RESET_ALL}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}✗ Connection error: {e}{Style.RESET_ALL}")
        return None


def test_api_endpoints(token=None):
    """Test key API endpoints."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # List of endpoints to test (GET requests)
    endpoints = [
        "/courses/",
        "/categories/",
        "/courses/software-testing/",  # Replace with a real course slug if different
        "/user/enrollments/",  # Requires auth
    ]

    print(f"\n{Fore.CYAN}=== TESTING API ENDPOINTS ==={Style.RESET_ALL}")

    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, headers=headers)
            print("\n" + "="*50)
            print_response(response, endpoint)
        except requests.exceptions.RequestException as e:
            print(
                f"\n{Fore.RED}✗ Error connecting to {endpoint}: {e}{Style.RESET_ALL}")


def main():
    print(f"{Fore.CYAN}=== API ENDPOINT TESTING ==={Style.RESET_ALL}")

    # First test without authentication
    print(f"\n{Fore.CYAN}Testing public endpoints (no auth):{Style.RESET_ALL}")
    test_api_endpoints()

    # Then test with authentication
    token = get_auth_token()
    if token:
        print(f"\n{Fore.CYAN}Testing authenticated endpoints:{Style.RESET_ALL}")
        test_api_endpoints(token)


if __name__ == "__main__":
    main()
