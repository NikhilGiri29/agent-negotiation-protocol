#!/usr/bin/env python3
"""
Test health endpoints
"""
import requests

def test_health():
    # Test health endpoints
    services = [
        ('Registry', 'http://localhost:8005/health'),
        ('Credit Bureau', 'http://localhost:8006/health'),
        ('ESG Regulator', 'http://localhost:8007/health'),
        ('Market Info', 'http://localhost:8008/health'),
        ('Bank A', 'http://localhost:9000/a2a/health'),
        ('Company A', 'http://localhost:4000/a2a/health')
    ]

    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            status = "OK" if response.status_code == 200 else "ERROR"
            print(f'{name}: {response.status_code} - {status}')
        except Exception as e:
            print(f'{name}: ERROR - {e}')

if __name__ == "__main__":
    test_health()
