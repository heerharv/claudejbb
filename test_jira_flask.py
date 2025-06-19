import requests
from flask import Flask, jsonify
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# JIRA Configuration - Updated with your working token
JIRA_DOMAIN = "uncia-team-vmevzjmu.atlassian.net"
JIRA_EMAIL = "heerha@uncia.ai"
JIRA_API_TOKEN = "ATATT3xFfGF02OVl2RLVinvafOJwvPadlqht-3HJ_MgBlv5RsOyvFS4cK096yscLLJlu3FurBnJ7vdPFzcb6mcRn_PEOstXoTMFnvNu7B6yyY56sFQ7bCdJTkrWN8_4vmdFhLriUPNoHalA1RYQosGN-Hvsy2NyseSbK1zET-FR_bZ0xd7WFKa8=06DE82DA"

def get_jira_auth():
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

# ✅ FIXED: Root endpoint returns JSON (no template needed)
@app.route('/')
def index():
    """API information and available endpoints"""
    return jsonify({
        "message": "🚀 UNCIA Jira Dashboard API is Running!",
        "status": "success",
        "authentication": "working" if JIRA_API_TOKEN else "missing",
        "endpoints": {
            "test_connection": "/api/jira/test",
            "all_projects": "/api/jira-projects", 
            "project_details": "/api/jira/project/{project_key}",
            "project_issues": "/api/jira/issues/{project_key}",
            "project_dashboard": "/api/jira/dashboard/{project_key}",
            "users": "/api/jira/users"
        },
        "example_urls": [
            "http://localhost:8000/api/jira/test",
            "http://localhost:8000/api/jira-projects",
            "http://localhost:8000/api/jira/project/SCRUM",
            "http://localhost:8000/api/jira/dashboard/SCRUM"
        ],
        "your_projects": ["SCRUM (UNCIA Easy)", "KANS (kanbans)", "NEW (new)", "SKP (Sample Kanban Project)"]
    })

@app.route('/api/jira/test')
def test_jira_connection():
    """Test Jira API connection"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/myself"
        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth(), timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                "status": "success",
                "message": "🎉 Connected to Jira successfully!",
                "user": {
                    "displayName": user_data.get('displayName'),
                    "emailAddress": user_data.get('emailAddress'),
                    "accountType": user_data.get('accountType'),
                    "accountId": user_data.get('accountId')
                },
                "domain": JIRA_DOMAIN,
                "token_status": "working"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Connection failed with status {response.status_code}",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Connection test failed: {str(e)}"
        }), 500

@app.route('/api/data')
def get_data():
    return jsonify({'message': 'Hello from Flask API'})

@app.route('/api/jira/project/<project_key>')
def get_project_details(project_key):
    """Get detailed project information"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/project/{project_key}"
        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        
        if response.status_code == 200:
            project_data = response.json()
            
            # Get additional project statistics
            stats_url = f"https://{JIRA_DOMAIN}/rest/api/3/project/{project_key}/statuses"
            stats_response = requests.get(stats_url, headers=get_jira_headers(), auth=get_jira_auth())
            
            result = {
                "project_info": project_data,
                "statuses": stats_response.json() if stats_response.status_code == 200 else []
            }
            
            return jsonify(result)
        else:
            return jsonify({"error": f"Failed to fetch project details: {response.text}"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

@app.route('/api/jira/issues/<project_key>')
def get_project_issues(project_key):
    """Get all issues for a specific project with detailed information"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # JQL query to get all issues from the specific project
        jql_query = f"project = {project_key} ORDER BY created DESC"
        
        params = {
            "jql": jql_query,
            "maxResults": 100,
            "fields": [
                "summary",
                "description", 
                "status",
                "assignee",
                "reporter",
                "priority",
                "issuetype",
                "created",
                "updated",
                "labels",
                "components",
                "fixVersions",
                "resolution",
                "resolutiondate",
                "worklog",
                "comment",
                "progress",
                "timeestimate",
                "timespent",
                "duedate"
            ]
        }
        
        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            issues_data = response.json()
            
            # Process and structure the data
            processed_issues = []
            for issue in issues_data.get('issues', []):
                fields = issue.get('fields', {})
                
                processed_issue = {
                    "key": issue.get('key'),
                    "id": issue.get('id'),
                    "summary": fields.get('summary'),
                    "description": fields.get('description'),
                    "status": {
                        "name": fields.get('status', {}).get('name'),
                        "category": fields.get('status', {}).get('statusCategory', {}).get('name')
                    },
                    "assignee": {
                        "name": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else "Unassigned",
                        "email": fields.get('assignee', {}).get('emailAddress') if fields.get('assignee') else None
                    },
                    "reporter": {
                        "name": fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
                        "email": fields.get('reporter', {}).get('emailAddress') if fields.get('reporter') else None
                    },
                    "priority": {
                        "name": fields.get('priority', {}).get('name') if fields.get('priority') else None,
                        "iconUrl": fields.get('priority', {}).get('iconUrl') if fields.get('priority') else None
                    },
                    "issuetype": {
                        "name": fields.get('issuetype', {}).get('name'),
                        "iconUrl": fields.get('issuetype', {}).get('iconUrl')
                    },
                    "created": fields.get('created'),
                    "updated": fields.get('updated'),
                    "labels": fields.get('labels', []),
                    "components": [comp.get('name') for comp in fields.get('components', [])],
                    "fixVersions": [version.get('name') for version in fields.get('fixVersions', [])],
                    "resolution": fields.get('resolution', {}).get('name') if fields.get('resolution') else None,
                    "resolutiondate": fields.get('resolutiondate'),
                    "progress": fields.get('progress', {}),
                    "timeestimate": fields.get('timeestimate'),
                    "timespent": fields.get('timespent'),
                    "duedate": fields.get('duedate')
                }
                processed_issues.append(processed_issue)
            
            return jsonify({
                "total": issues_data.get('total'),
                "issues": processed_issues
            })
        else:
            return jsonify({"error": f"Failed to fetch issues: {response.text}"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

@app.route('/api/jira/dashboard/<project_key>')
def get_project_dashboard(project_key):
    """Get comprehensive dashboard data for the project"""
    try:
        # Get project details
        project_url = f"https://{JIRA_DOMAIN}/rest/api/3/project/{project_key}"
        project_response = requests.get(project_url, headers=get_jira_headers(), auth=get_jira_auth())
        
        # Get issues summary by status
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # Query for issue counts by status
        status_queries = {
            "todo": f"project = {project_key} AND status in ('To Do', 'Open', 'Backlog')",
            "in_progress": f"project = {project_key} AND status in ('In Progress', 'In Development')",
            "done": f"project = {project_key} AND status in ('Done', 'Closed', 'Resolved')",
            "total": f"project = {project_key}"
        }
        
        status_counts = {}
        for status_type, jql in status_queries.items():
            params = {
                "jql": jql,
                "maxResults": 0  # We only want the count
            }
            response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
            if response.status_code == 200:
                status_counts[status_type] = response.json().get('total', 0)
            else:
                status_counts[status_type] = 0
        
        # Get recent activity (last 10 issues)
        recent_params = {
            "jql": f"project = {project_key} ORDER BY updated DESC",
            "maxResults": 10,
            "fields": ["summary", "status", "assignee", "updated", "issuetype"]
        }
        recent_response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=recent_params)
        
        recent_issues = []
        if recent_response.status_code == 200:
            for issue in recent_response.json().get('issues', []):
                fields = issue.get('fields', {})
                recent_issues.append({
                    "key": issue.get('key'),
                    "summary": fields.get('summary'),
                    "status": fields.get('status', {}).get('name'),
                    "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else "Unassigned",
                    "updated": fields.get('updated'),
                    "issuetype": fields.get('issuetype', {}).get('name')
                })
        
        # Get assignee distribution
        assignee_params = {
            "jql": f"project = {project_key} AND assignee is not EMPTY",
            "maxResults": 100,
            "fields": ["assignee"]
        }
        assignee_response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=assignee_params)
        
        assignee_counts = {}
        if assignee_response.status_code == 200:
            for issue in assignee_response.json().get('issues', []):
                assignee = issue.get('fields', {}).get('assignee', {})
                if assignee:
                    name = assignee.get('displayName')
                    assignee_counts[name] = assignee_counts.get(name, 0) + 1
        
        dashboard_data = {
            "project_info": project_response.json() if project_response.status_code == 200 else {},
            "status_counts": status_counts,
            "recent_issues": recent_issues,
            "assignee_distribution": assignee_counts,
            "progress_percentage": round((status_counts.get('done', 0) / max(status_counts.get('total', 1), 1)) * 100, 2)
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

@app.route('/api/jira/users')
def get_project_users():
    """Get all users in the project"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/users/search"
        params = {
            "maxResults": 50
        }
        
        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            users = response.json()
            processed_users = []
            
            for user in users:
                processed_users.append({
                    "accountId": user.get('accountId'),
                    "displayName": user.get('displayName'),
                    "emailAddress": user.get('emailAddress'),
                    "active": user.get('active'),
                    "avatarUrls": user.get('avatarUrls', {})
                })
            
            return jsonify(processed_users)
        else:
            return jsonify({"error": f"Failed to fetch users: {response.text}"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

# Legacy endpoints for backward compatibility
@app.route('/api/jira-projects')
def get_jira_projects():
    """Get all projects"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/project/search"
        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch Jira projects", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

@app.route('/api/jira/issues')
def get_jira_issues():
    """Get all issues (legacy endpoint)"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        params = {
            "maxResults": 100,
            "jql": "project is not EMPTY ORDER BY created DESC"
        }

        response = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Failed to fetch Jira issues: {response.text}"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting UNCIA Jira Dashboard Flask App...")
    print(f"📧 Email: {JIRA_EMAIL}")
    print(f"🏢 Domain: {JIRA_DOMAIN}")
    print(f"🔑 Token: {JIRA_API_TOKEN[:15]}...")
    print("🌐 Test connection: http://localhost:8000/api/jira/test")
    print("📋 All projects: http://localhost:8000/api/jira-projects")
    print("📊 SCRUM dashboard: http://localhost:8000/api/jira/dashboard/SCRUM")
    app.run(debug=True, port=8000)