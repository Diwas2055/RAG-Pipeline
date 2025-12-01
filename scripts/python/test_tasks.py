#!/usr/bin/env python3
"""
Task Management API Testing Script (Python)
Tests all task management endpoints with proper error handling
"""

import requests
import time
import sys
from typing import Optional

BASE_URL = "http://localhost:8000"

# ANSI color codes
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color


def print_header(text: str):
    """Print colored header"""
    print(f"\n{BLUE}{'=' * 50}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'=' * 50}{NC}\n")


def print_test(text: str):
    """Print test name"""
    print(f"{BLUE}{text}{NC}")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{NC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{NC}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{NC}")


def check_task_status(task_id: str, max_attempts: int = 10) -> Optional[dict]:
    """
    Poll task status until completion or timeout

    Args:
        task_id: The task ID to check
        max_attempts: Maximum number of polling attempts

    Returns:
        Task result if completed, None otherwise
    """
    for attempt in range(1, max_attempts + 1):
        print(f"{YELLOW}Checking status (attempt {attempt}/{max_attempts})...{NC}")

        try:
            response = requests.get(f"{BASE_URL}/tasks/status/{task_id}")
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "Completed":
                print_success("Task completed!")
                print(f"Result: {data.get('result')}\n")
                return data

            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print_error(f"Error checking status: {e}")
            return None

    print_warning(f"Task still pending after {max_attempts} attempts\n")
    return None


def test_process_data():
    """Test: Process Data"""
    print_test("Test 1: Process Data")
    print("POST /tasks/process")

    try:
        response = requests.post(
            f"{BASE_URL}/tasks/process", json={"data": "test data"}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}")

        if task_id := data.get("task_id"):
            check_task_status(task_id)

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_add_numbers():
    """Test: Add Numbers"""
    print_test("Test 2: Add Numbers")
    print("POST /tasks/calculate/add")
    print("Operation: 15 + 25 = 40")

    try:
        response = requests.post(
            f"{BASE_URL}/tasks/calculate/add", json={"x": 15, "y": 25}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}")

        if task_id := data.get("task_id"):
            check_task_status(task_id)

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_divide_numbers():
    """Test: Divide Numbers"""
    print_test("Test 3: Divide Numbers")
    print("POST /tasks/calculate/divide")
    print("Operation: 100 / 5 = 20")

    try:
        response = requests.post(
            f"{BASE_URL}/tasks/calculate/divide", json={"dividend": 100, "divisor": 5}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}")

        if task_id := data.get("task_id"):
            check_task_status(task_id)

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_chain_workflow():
    """Test: Chain Workflow"""
    print_test("Test 4: Chain Workflow (add then divide)")
    print("POST /tasks/workflow/chain")
    print("Operation: (10 + 20) / 5 = 6")

    try:
        response = requests.post(
            f"{BASE_URL}/tasks/workflow/chain", json={"x": 10, "y": 20, "divisor": 5}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}")

        if task_id := data.get("task_id"):
            check_task_status(task_id)

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_parallel_workflow():
    """Test: Parallel Workflow"""
    print_test("Test 5: Parallel Workflow (add + divide, then sum)")
    print("POST /tasks/workflow/parallel")
    print("Operation: (10 + 5) + (10 / 2) = 15 + 5 = 20")

    try:
        response = requests.post(
            f"{BASE_URL}/tasks/workflow/parallel", json={"x": 10, "y": 5, "z": 2}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}")

        if task_id := data.get("task_id"):
            check_task_status(task_id)

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_task_info():
    """Test: Task Info"""
    print_test("Test 6: Task Info (Available Queues and Tasks)")
    print("GET /tasks/info")

    try:
        response = requests.get(f"{BASE_URL}/tasks/info")
        response.raise_for_status()
        data = response.json()

        print("\nAvailable Queues:")
        for queue in data.get("queues", []):
            print(f"  - {queue['name']}: {queue['description']}")

        print("\nRegistered Tasks:")
        for task in data.get("tasks", []):
            print(f"  - {task['name']} → {task['queue']}")

        print()

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}\n")


def test_health_check():
    """Test: Health Check"""
    print_test("Test 7: Health Check")
    print("GET /health")

    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"Response: {data}\n")
        print_success("API is healthy!")

    except requests.exceptions.RequestException as e:
        print_error(f"Health check failed: {e}\n")


def main():
    """Run all tests"""
    print_header("Task Management API Testing")

    # Check if API is accessible
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        print_error(f"Cannot connect to API at {BASE_URL}")
        print(
            "Make sure the API is running (docker-compose up or scripts/start_api.sh)"
        )
        sys.exit(1)

    # Run all tests
    test_process_data()
    test_add_numbers()
    test_divide_numbers()
    test_chain_workflow()
    test_parallel_workflow()
    test_task_info()
    test_health_check()

    # Summary
    print(f"\n{GREEN}{'=' * 50}{NC}")
    print(f"{GREEN}Testing Complete!{NC}")
    print(f"{GREEN}{'=' * 50}{NC}\n")
    print(f"View Flower dashboard at: http://localhost:5555")
    print(f"View API docs at: {BASE_URL}/docs")


if __name__ == "__main__":
    main()
