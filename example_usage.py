#!/usr/bin/env python3
"""
Example script demonstrating how to use the Insurance Document Analyzer API
"""

import requests
import json

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get('http://localhost:8000/api/v1/health')
        print("Health Check Response:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint to see API information"""
    try:
        response = requests.get('http://localhost:8000/api/v1/')
        print("\nAPI Information:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint test failed: {e}")
        return False

def analyze_coverage_example():
    """
    Example of how to analyze coverage.
    Note: This requires actual PDF files and an OpenAI API key configured.
    """
    print("\nCoverage Analysis Example:")
    print("To analyze coverage, you would:")
    print("1. Have two PDF files: Policy Disclosure Statement and Schedule of Coverage")
    print("2. Make a POST request to /api/v1/analyze-coverage with:")
    print("   - policy_disclosure: PDF file")
    print("   - schedule_coverage: PDF file") 
    print("   - insurance_type: string (e.g., 'auto', 'home', 'health')")
    print("   - question: string (your coverage question)")
    print("\nExample with curl:")
    print('curl -X POST "http://localhost:8000/api/v1/analyze-coverage" \\')
    print('  -F "policy_disclosure=@policy.pdf" \\')
    print('  -F "schedule_coverage=@schedule.pdf" \\')
    print('  -F "insurance_type=auto" \\')
    print('  -F "question=Is collision damage covered?"')
    
    # Uncomment and modify the following if you have actual PDF files:
    """
    try:
        with open('policy.pdf', 'rb') as policy_file, \
             open('schedule.pdf', 'rb') as schedule_file:
            
            response = requests.post(
                'http://localhost:8000/api/v1/analyze-coverage',
                files={
                    'policy_disclosure': policy_file,
                    'schedule_coverage': schedule_file
                },
                data={
                    'insurance_type': 'auto',
                    'question': 'Is collision damage covered under this policy?'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Coverage likelihood: {result['percentage_score']}%")
                print(f"Ranking: {result['likelihood_ranking']}")
                print(f"Explanation: {result['explanation']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
    except FileNotFoundError:
        print("PDF files not found. Please ensure policy.pdf and schedule.pdf exist.")
    except Exception as e:
        print(f"Coverage analysis failed: {e}")
    """

if __name__ == "__main__":
    print("Insurance Document Analyzer API - Usage Example")
    print("=" * 50)
    
    # Test basic endpoints
    if test_health_endpoint():
        print("✅ Health endpoint working")
    else:
        print("❌ Health endpoint failed")
    
    if test_root_endpoint():
        print("✅ Root endpoint working")
    else:
        print("❌ Root endpoint failed")
    
    # Show coverage analysis example
    analyze_coverage_example()
    
    print("\n" + "=" * 50)
    print("For interactive API documentation, visit:")
    print("- Swagger UI: http://localhost:8000/docs")
    print("- ReDoc: http://localhost:8000/redoc")