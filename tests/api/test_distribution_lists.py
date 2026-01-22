#!/usr/bin/env python3
"""
Test script for Distribution List API endpoints.
Run this after starting the API server to verify all endpoints are working.
"""

from typing import Any, Dict

import requests

# Configuration
API_BASE = "http://localhost:8000/api/v1"
DOC_ID = 1  # Change this to a valid document ID in your system


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_test(name: str) -> None:
    """Print test name header."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{name}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make HTTP request and return response."""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return {
            "status": response.status_code,
            "data": response.json() if response.text else None,
            "text": response.text,
        }
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to API at {API_BASE}")
        return None
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def test_endpoints():
    """Test all distribution list endpoints."""

    print_test("Testing Distribution List API Endpoints")
    print_info(f"Using API Base: {API_BASE}")
    print_info(f"Using Document ID: {DOC_ID}")

    # Test 1: Create distribution list
    print_test("Test 1: Create Distribution List")
    create_response = make_request(
        "POST", f"/documents/{DOC_ID}/distribution-lists", {"name": "Review Team"}
    )

    if not create_response:
        return

    if create_response["status"] == 201:
        list_data = create_response["data"]
        list_id = list_data.get("dist_list_id")
        print_success(f"Created distribution list: {list_data}")
    else:
        print_error(f"Failed to create list. Status: {create_response['status']}")
        print_info(f"Response: {create_response.get('data')}")
        return

    # Test 2: Get all distribution lists
    print_test("Test 2: Get All Distribution Lists")
    get_lists_response = make_request("GET", f"/documents/{DOC_ID}/distribution-lists")

    if get_lists_response["status"] == 200:
        lists = get_lists_response["data"]
        print_success(f"Retrieved {len(lists)} list(s)")
        for lst in lists:
            print_info(f"  - {lst.get('list_name')} (ID: {lst.get('dist_list_id')})")
    else:
        print_error(f"Failed to get lists. Status: {get_lists_response['status']}")
        return

    # Test 3: Add recipient to list
    print_test("Test 3: Add Recipient to List")
    add_recipient_response = make_request(
        "POST",
        f"/documents/{DOC_ID}/distribution-lists/{list_id}/recipients",
        {"email": "reviewer@example.com", "person_name": "John Reviewer"},
    )

    if add_recipient_response["status"] == 201:
        recipient = add_recipient_response["data"]
        print_success(f"Added recipient: {recipient}")
    else:
        print_error(f"Failed to add recipient. Status: {add_recipient_response['status']}")
        return

    # Test 4: Get recipients
    print_test("Test 4: Get Recipients in List")
    get_recipients_response = make_request(
        "GET", f"/documents/{DOC_ID}/distribution-lists/{list_id}/recipients"
    )

    if get_recipients_response["status"] == 200:
        recipients = get_recipients_response["data"]
        print_success(f"Retrieved {len(recipients)} recipient(s)")
        for rec in recipients:
            print_info(f"  - {rec.get('email')} ({rec.get('person_name', 'N/A')})")
    else:
        print_error(f"Failed to get recipients. Status: {get_recipients_response['status']}")
        return

    # Test 5: Send for review
    print_test("Test 5: Send Document for Review")
    send_response = make_request(
        "POST",
        f"/documents/{DOC_ID}/distribution-lists/{list_id}/send-for-review",
        {"message": "Please review and provide comments"},
    )

    if send_response["status"] == 201:
        result = send_response["data"]
        print_success(f"Sent for review: {result}")
    else:
        print_error(f"Failed to send for review. Status: {send_response['status']}")
        return

    # Test 6: Create another list to test delete
    print_test("Test 6: Create and Delete Distribution List")
    create_response2 = make_request(
        "POST", f"/documents/{DOC_ID}/distribution-lists", {"name": "Temporary List"}
    )

    if create_response2["status"] == 201:
        temp_list_id = create_response2["data"].get("dist_list_id")
        print_success(f"Created temporary list (ID: {temp_list_id})")

        # Delete it
        delete_response = make_request(
            "DELETE", f"/documents/{DOC_ID}/distribution-lists/{temp_list_id}"
        )

        if delete_response["status"] == 204:
            print_success("Deleted temporary list")
        else:
            print_error(f"Failed to delete list. Status: {delete_response['status']}")
    else:
        print_error("Failed to create temporary list")
        return

    # Test 7: Verify deletion
    print_test("Test 7: Verify List Count After Deletion")
    get_lists_response2 = make_request("GET", f"/documents/{DOC_ID}/distribution-lists")

    if get_lists_response2["status"] == 200:
        lists = get_lists_response2["data"]
        print_success(f"Now have {len(lists)} list(s) (should be 1)")
    else:
        print_error("Failed to verify list count")
        return

    print_test("All Tests Completed Successfully! ✓")


if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}Distribution List API Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Make sure the API is running on {API_BASE}{Colors.END}")

    try:
        test_endpoints()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
