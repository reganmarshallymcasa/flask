import requests
from flask import current_app

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'


def _headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def get_user_profile(token):
    """Fetch profile for the signed-in user."""
    resp = requests.get(f"{GRAPH_API_ENDPOINT}/me", headers=_headers(token))
    if resp.status_code == 200:
        return resp.json()
    current_app.logger.error('Graph API error: %s %s', resp.status_code, resp.text)
    return None


def add_users_bulk(token, users):
    """Create multiple users via Graph API."""
    created = []
    for user in users:
        resp = requests.post(f"{GRAPH_API_ENDPOINT}/users", json=user, headers=_headers(token))
        if resp.status_code in (200, 201):
            created.append(resp.json())
        else:
            current_app.logger.error('Failed to create user: %s %s', resp.status_code, resp.text)
    return created


def update_users_bulk(token, users):
    """Update multiple users via Graph API."""
    updated = []
    for user in users:
        user_id = user.get('id')
        if not user_id:
            continue
        resp = requests.patch(f"{GRAPH_API_ENDPOINT}/users/{user_id}", json=user, headers=_headers(token))
        if resp.status_code == 204:
            updated.append(user_id)
        else:
            current_app.logger.error('Failed to update user %s: %s %s', user_id, resp.status_code, resp.text)
    return updated


def last_login_report(token):
    """Get last sign-in report for all users."""
    url = f"{GRAPH_API_ENDPOINT}/reports/getAzureADSignInLogs"
    resp = requests.get(url, headers=_headers(token))
    if resp.status_code == 200:
        return resp.json()
    current_app.logger.error('Failed to get sign-in logs: %s %s', resp.status_code, resp.text)
    return None
