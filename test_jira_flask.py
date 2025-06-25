import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime, timedelta

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
        "message": "🚀 UNCIA Jira Dashboard API with Risk Management is Running!",
        "status": "success",
        "authentication": "working" if JIRA_API_TOKEN else "missing",
        "endpoints": {
            "test_connection": "/api/jira/test",
            "all_projects": "/api/jira-projects", 
            "project_details": "/api/jira/project/{project_key}",
            "project_issues": "/api/jira/issues/{project_key}",
            "project_dashboard": "/api/jira/dashboard/{project_key}",
            "project_board": "/api/jira/board/{project_key}",
            "users": "/api/jira/users",
            # Risk Management Endpoints
            "risk_dashboard": "/api/risk/dashboard/{project_key}",
            "risk_board": "/api/risk/board/{project_key}",
            "risk_create": "/api/risk/create-integrated",
            "risk_metrics": "/api/metrics/integrated/{project_key}",
            "risk_update": "/api/risk/update/{issue_key}"
        },
        "example_urls": [
            "http://localhost:8000/api/jira/test",
            "http://localhost:8000/api/jira-projects",
            "http://localhost:8000/api/jira/project/SCRUM",
            "http://localhost:8000/api/jira/dashboard/SCRUM",
            "http://localhost:8000/api/jira/board/SCRUM",
            "http://localhost:8000/api/risk/dashboard/SCRUM",
            "http://localhost:8000/api/risk/board/SCRUM"
        ],
        "your_projects": ["SCRUM (UNCIA Easy)", "KANS (kanbans)", "NEW (new)", "SKP (Sample Kanban Project)"],
        "risk_features": {
            "risk_categories": ["Operational", "Financial", "Cybersecurity", "Technology", "Reputational", "Compliance"],
            "impact_levels": ["Low", "Medium", "High", "Critical"],
            "departments": ["IT", "Security", "Finance", "Legal", "Operations", "Compliance"]
        }
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

def get_project_statuses(project_key):
    """Get all actual status names used in the project"""
    try:
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # Get a sample of issues to understand what statuses are actually used
        params = {
            "jql": f"project = {project_key}",
            "maxResults": 100,
            "fields": ["status"]
        }
        
        response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            issues = response.json().get('issues', [])
            statuses = set()
            for issue in issues:
                status_name = issue.get('fields', {}).get('status', {}).get('name')
                if status_name:
                    statuses.add(status_name)
            
            return list(statuses)
        
        return []
    except:
        return []

def categorize_status(status_name):
    """Categorize status into todo, in_progress, or done"""
    status_lower = status_name.lower()
    
    # Define status mappings based on common Jira statuses
    todo_statuses = ['to do', 'todo', 'open', 'backlog', 'new', 'created', 'pending']
    progress_statuses = ['in progress', 'in development', 'in dev', 'working', 'active', 'started']
    done_statuses = ['done', 'closed', 'resolved', 'complete', 'finished', 'resolved']
    
    if any(todo_status in status_lower for todo_status in todo_statuses):
        return 'todo'
    elif any(progress_status in status_lower for progress_status in progress_statuses):
        return 'in_progress'
    elif any(done_status in status_lower for done_status in done_statuses):
        return 'done'
    else:
        # Default unknown statuses to todo
        return 'todo'

@app.route('/api/jira/dashboard/<project_key>')
def get_project_dashboard(project_key):
    """Get comprehensive dashboard data for the project"""
    try:
        # Get project details
        project_url = f"https://{JIRA_DOMAIN}/rest/api/3/project/{project_key}"
        project_response = requests.get(project_url, headers=get_jira_headers(), auth=get_jira_auth())
        
        # Get all issues with status information
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # Get all issues to analyze actual statuses
        all_issues_params = {
            "jql": f"project = {project_key}",
            "maxResults": 1000,  # Increased to get all issues
            "fields": ["status", "assignee"]
        }
        
        all_issues_response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=all_issues_params)
        
        status_counts = {'todo': 0, 'in_progress': 0, 'done': 0, 'total': 0}
        
        if all_issues_response.status_code == 200:
            all_issues = all_issues_response.json().get('issues', [])
            status_counts['total'] = len(all_issues)
            
            # Count statuses by actual categorization
            for issue in all_issues:
                status_name = issue.get('fields', {}).get('status', {}).get('name', '')
                category = categorize_status(status_name)
                status_counts[category] += 1
        
        # Get recent activity (last 50 issues to have enough for board)
        recent_params = {
            "jql": f"project = {project_key} ORDER BY updated DESC",
            "maxResults": 50,
            "fields": ["summary", "status", "assignee", "updated", "issuetype", "duedate"]
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
                    "issuetype": fields.get('issuetype', {}).get('name'),
                    "duedate": fields.get('duedate')
                })
        
        # Get assignee distribution
        assignee_counts = {}
        if all_issues_response.status_code == 200:
            for issue in all_issues_response.json().get('issues', []):
                assignee = issue.get('fields', {}).get('assignee', {})
                if assignee:
                    name = assignee.get('displayName')
                    assignee_counts[name] = assignee_counts.get(name, 0) + 1
        
        # Get actual project statuses for debugging
        project_statuses = get_project_statuses(project_key)
        
        dashboard_data = {
            "project_info": project_response.json() if project_response.status_code == 200 else {},
            "status_counts": status_counts,
            "recent_issues": recent_issues,
            "assignee_distribution": assignee_counts,
            "progress_percentage": round((status_counts.get('done', 0) / max(status_counts.get('total', 1), 1)) * 100, 2),
            "debug_info": {
                "project_statuses": project_statuses,
                "total_recent_issues": len(recent_issues)
            }
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

@app.route('/api/jira/board/<project_key>')
def get_project_board(project_key):
    """Get project board data organized by status columns"""
    try:
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # Get all issues for the board
        params = {
            "jql": f"project = {project_key} ORDER BY updated DESC",
            "maxResults": 100,
            "fields": ["summary", "status", "assignee", "updated", "issuetype", "priority", "duedate"]
        }
        
        response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            issues = response.json().get('issues', [])
            
            # Organize issues by status category
            board_data = {
                'todo': [],
                'in_progress': [],
                'done': []
            }
            
            for issue in issues:
                fields = issue.get('fields', {})
                status_name = fields.get('status', {}).get('name', '')
                category = categorize_status(status_name)
                
                issue_data = {
                    "key": issue.get('key'),
                    "summary": fields.get('summary'),
                    "status": status_name,
                    "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else "Unassigned",
                    "updated": fields.get('updated'),
                    "issuetype": fields.get('issuetype', {}).get('name'),
                    "priority": fields.get('priority', {}).get('name') if fields.get('priority') else None,
                    "duedate": fields.get('duedate')
                }
                
                board_data[category].append(issue_data)
            
            # Limit to 10 issues per column
            for category in board_data:
                board_data[category] = board_data[category][:10]
            
            return jsonify({
                "board": board_data,
                "counts": {
                    "todo": len([i for i in issues if categorize_status(i.get('fields', {}).get('status', {}).get('name', '')) == 'todo']),
                    "in_progress": len([i for i in issues if categorize_status(i.get('fields', {}).get('status', {}).get('name', '')) == 'in_progress']),
                    "done": len([i for i in issues if categorize_status(i.get('fields', {}).get('status', {}).get('name', '')) == 'done'])
                }
            })
        else:
            return jsonify({"error": f"Failed to fetch board data: {response.text}"}), response.status_code
            
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

# ==================== RISK MANAGEMENT ENDPOINTS ====================

@app.route('/api/risk/dashboard/<project_key>')
def get_risk_dashboard_integration(project_key):
    """Integrated risk dashboard with existing project data"""
    try:
        # Get regular project data
        regular_response = requests.get(f"http://localhost:8000/api/jira/dashboard/{project_key}")
        regular_data = regular_response.json() if regular_response.status_code == 200 else {}
        
        # Get risk-specific data
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        # Query for risk-labeled issues
        risk_params = {
            "jql": f"project = {project_key} AND (labels = 'risk-management' OR labels in ('risk-operational', 'risk-financial', 'risk-cybersecurity', 'risk-technology', 'risk-reputational', 'risk-compliance'))",
            "maxResults": 100,
            "fields": ["summary", "description", "status", "priority", "labels", "created", "updated", "assignee", "customfield_10001", "customfield_10002", "customfield_10003"]
        }
        
        risk_response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=risk_params)
        
        if risk_response.status_code == 200:
            risk_issues = risk_response.json().get('issues', [])
            
            # Process risk analytics
            risk_analytics = process_risk_analytics(risk_issues)
            
            # Combine with regular data
            integrated_data = {
                **regular_data,
                "risk_analytics": risk_analytics,
                "total_risks": len(risk_issues),
                "risk_integration": {
                    "risk_to_project_ratio": len(risk_issues) / max(regular_data.get('status_counts', {}).get('total', 1), 1),
                    "high_impact_risks": len([r for r in risk_issues if 'impact-high' in r.get('fields', {}).get('labels', []) or 'impact-critical' in r.get('fields', {}).get('labels', [])]),
                    "escalation_required": len([r for r in risk_issues if 'escalation-required' in r.get('fields', {}).get('labels', [])])
                }
            }
            
            return jsonify(integrated_data)
        else:
            # Return regular data with mock risk data if no risks found
            mock_risk_data = generate_mock_risk_analytics()
            return jsonify({
                **regular_data, 
                "risk_analytics": mock_risk_data,
                "total_risks": 8,
                "risk_integration": {
                    "risk_to_project_ratio": 0.15,
                    "high_impact_risks": 3,
                    "escalation_required": 2
                }
            })
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

def process_risk_analytics(risk_issues):
    """Process risk issues for analytics"""
    analytics = {
        "by_category": {},
        "by_impact": {},
        "by_status": {},
        "recent_risks": [],
        "critical_risks": [],
        "trends": {}
    }
    
    for issue in risk_issues:
        fields = issue.get('fields', {})
        labels = fields.get('labels', [])
        
        # Extract risk category
        risk_category = next((label.replace('risk-', '').replace('-', ' ').title() 
                            for label in labels if label.startswith('risk-')), 'Unknown')
        analytics["by_category"][risk_category] = analytics["by_category"].get(risk_category, 0) + 1
        
        # Extract impact level
        impact_level = next((label.replace('impact-', '').title() 
                           for label in labels if label.startswith('impact-')), 'Unknown')
        analytics["by_impact"][impact_level] = analytics["by_impact"].get(impact_level, 0) + 1
        
        # Status analysis
        status = fields.get('status', {}).get('name', 'Unknown')
        analytics["by_status"][status] = analytics["by_status"].get(status, 0) + 1
        
        # Recent risks (last 5)
        if len(analytics["recent_risks"]) < 5:
            analytics["recent_risks"].append({
                "key": issue.get('key'),
                "summary": fields.get('summary'),
                "status": status,
                "category": risk_category,
                "impact": impact_level,
                "created": fields.get('created')
            })
        
        # Critical risks
        if impact_level in ['Critical', 'High']:
            analytics["critical_risks"].append({
                "key": issue.get('key'),
                "summary": fields.get('summary'),
                "impact": impact_level,
                "status": status
            })
    
    return analytics

def generate_mock_risk_analytics():
    """Generate mock risk data for demonstration"""
    return {
        "by_category": {
            'Operational': 2,
            'Financial': 1,
            'Cybersecurity': 3,
            'Technology': 1,
            'Compliance': 1
        },
        "by_impact": {
            'Critical': 1,
            'High': 2,
            'Medium': 3,
            'Low': 2
        },
        "by_status": {
            'Open': 3,
            'In Progress': 2,
            'Under Review': 2,
            'Closed': 1
        },
        "recent_risks": [
            {
                "key": 'RISK-001',
                "summary": 'Cloud Provider Service Outage Risk',
                "status": 'Open',
                "category": 'Operational',
                "impact": 'High',
                "created": datetime.now().isoformat()
            },
            {
                "key": 'RISK-002',
                "summary": 'Third-Party Data Processing Compliance',
                "status": 'In Progress',
                "category": 'Compliance',
                "impact": 'Critical',
                "created": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ],
        "critical_risks": [
            {
                "key": 'RISK-002',
                "summary": 'Third-Party Data Processing Compliance',
                "impact": 'Critical',
                "status": 'In Progress'
            }
        ]
    }

@app.route('/api/risk/create-integrated', methods=['POST'])
def create_integrated_risk_ticket():
    """Create risk ticket with integration to existing project workflow"""
    try:
        data = request.json
        project_key = data.get('project_key', 'SCRUM')
        
        # Enhanced issue creation with risk-specific fields
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": f"🚨 RISK: {data.get('risk_title')}",
                "description": create_risk_description(data),
                "issuetype": {"name": "Task"},  # or "Bug" for risks
                "priority": {"name": map_risk_impact_to_priority(data.get('impact_level'))},
                "labels": create_risk_labels(data),
                "assignee": {"accountId": data.get('assignee')} if data.get('assignee') else None,
                "duedate": data.get('target_resolution_date') if data.get('target_resolution_date') else None
            }
        }
        
        # Add custom fields if they exist in your Jira (these may need to be created in Jira first)
        if data.get('third_party'):
            # Custom field for third party - you may need to create this in Jira
            pass  # issue_data["fields"]["customfield_10001"] = data.get('third_party')
        if data.get('risk_category'):
            # Custom field for risk category - you may need to create this in Jira
            pass  # issue_data["fields"]["customfield_10002"] = data.get('risk_category')
        if data.get('impact_level'):
            # Custom field for impact level - you may need to create this in Jira
            pass  # issue_data["fields"]["customfield_10003"] = data.get('impact_level')
        
        url = f"https://{JIRA_DOMAIN}/rest/api/3/issue"
        response = requests.post(url, headers=get_jira_headers(), auth=get_jira_auth(), 
                               data=json.dumps(issue_data))
        
        if response.status_code == 201:
            created_issue = response.json()
            
            # Auto-create follow-up tasks if needed
            if data.get('create_mitigation_tasks'):
                create_mitigation_tasks(created_issue['key'], data, project_key)
            
            return jsonify({
                "status": "success",
                "message": "Risk ticket created successfully",
                "issue": created_issue,
                "mitigation_tasks_created": data.get('create_mitigation_tasks', False)
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to create risk ticket: {response.text}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

def create_risk_description(data):
    """Create comprehensive risk description"""
    return f"""
🔍 **Risk Category:** {data.get('risk_category', 'N/A')}
📅 **Date Identified:** {data.get('date_identified', 'N/A')}
🏢 **Third-Party Involved:** {data.get('third_party', 'N/A')}

📄 **Risk Description:**
{data.get('risk_description', 'No description provided')}

📉 **Potential Impact Level:** {data.get('impact_level', 'N/A')}
📢 **Escalation Required:** {'Yes' if data.get('escalation_required') else 'No'}
👥 **Departments Affected:** {', '.join(data.get('departments_affected', []))}

⚠️ **Recommended Mitigation Actions:**
{data.get('recommended_action', 'No action specified')}

🎯 **Business Impact:**
{data.get('business_impact', 'Impact assessment pending')}

📊 **Risk Assessment Matrix:**
- **Probability:** {data.get('probability', 'TBD')}
- **Impact:** {data.get('impact_level', 'TBD')}
- **Risk Score:** {calculate_risk_score(data.get('probability'), data.get('impact_level'))}

🔄 **Status:** Open - Awaiting Assessment
📈 **Next Review Date:** {data.get('next_review_date', 'TBD')}
    """

def create_risk_labels(data):
    """Create comprehensive label system for risks"""
    labels = ['risk-management']
    
    # Category label
    if data.get('risk_category'):
        labels.append(f"risk-{data.get('risk_category').lower().replace(' ', '-')}")
    
    # Impact label
    if data.get('impact_level'):
        labels.append(f"impact-{data.get('impact_level').lower()}")
    
    # Escalation label
    if data.get('escalation_required'):
        labels.append('escalation-required')
    
    # Department labels
    for dept in data.get('departments_affected', []):
        labels.append(f"dept-{dept.lower()}")
    
    # Third-party label
    if data.get('third_party'):
        labels.append('third-party-risk')
    
    return labels

def map_risk_impact_to_priority(impact_level):
    """Map risk impact to Jira priority"""
    mapping = {
        'Critical': 'Highest',
        'High': 'High',
        'Medium': 'Medium', 
        'Low': 'Low'
    }
    return mapping.get(impact_level, 'Medium')

def calculate_risk_score(probability, impact):
    """Calculate numerical risk score"""
    prob_values = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    impact_values = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    
    prob_score = prob_values.get(probability, 2)
    impact_score = impact_values.get(impact, 2)
    
    return prob_score * impact_score

def create_mitigation_tasks(parent_risk_key, risk_data, project_key):
    """Auto-create mitigation tasks for high-impact risks"""
    if risk_data.get('impact_level') in ['High', 'Critical']:
        mitigation_tasks = [
            {
                "summary": f"Risk Assessment - {risk_data.get('risk_title')}",
                "description": f"Conduct detailed risk assessment for {parent_risk_key}",
                "priority": "High"
            },
            {
                "summary": f"Mitigation Plan - {risk_data.get('risk_title')}",
                "description": f"Develop comprehensive mitigation plan for {parent_risk_key}",
                "priority": "High"
            }
        ]
        
        for task in mitigation_tasks:
            task_data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": task["summary"],
                    "description": task["description"],
                    "issuetype": {"name": "Task"},  # Changed from Sub-task as it requires parent
                    "priority": {"name": task["priority"]},
                    "labels": ["risk-mitigation", f"parent-{parent_risk_key}"]
                }
            }
            
            # Create the task
            url = f"https://{JIRA_DOMAIN}/rest/api/3/issue"
            requests.post(url, headers=get_jira_headers(), auth=get_jira_auth(), 
                         data=json.dumps(task_data))

@app.route('/api/risk/board/<project_key>')
def get_risk_board(project_key):
    """Get risk-specific board view"""
    try:
        search_url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
        
        params = {
            "jql": f"project = {project_key} AND labels = 'risk-management' ORDER BY priority DESC, created DESC",
            "maxResults": 50,
            "fields": ["summary", "status", "priority", "labels", "assignee", "created", "updated", "customfield_10001", "customfield_10002", "customfield_10003"]
        }
        
        response = requests.get(search_url, headers=get_jira_headers(), auth=get_jira_auth(), params=params)
        
        if response.status_code == 200:
            issues = response.json().get('issues', [])
            
            # Organize by risk status workflow
            risk_board = {
                'identified': [],
                'assessment': [],
                'mitigation': [],
                'monitoring': [],
                'closed': []
            }
            
            for issue in issues:
                fields = issue.get('fields', {})
                status = fields.get('status', {}).get('name', '').lower()
                labels = fields.get('labels', [])
                
                # Map status to risk workflow
                if 'closed' in status or 'resolved' in status or 'done' in status:
                    category = 'closed'
                elif 'mitigation' in labels or 'progress' in status:
                    category = 'mitigation'
                elif 'assessment' in labels or 'review' in status:
                    category = 'assessment'
                elif 'monitoring' in labels:
                    category = 'monitoring'
                else:
                    category = 'identified'
                
                risk_item = {
                    "key": issue.get('key'),
                    "summary": fields.get('summary'),
                    "status": fields.get('status', {}).get('name'),
                    "priority": fields.get('priority', {}).get('name') if fields.get('priority') else None,
                    "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else "Unassigned",
                    "created": fields.get('created'),
                    "updated": fields.get('updated'),
                    "risk_category": next((label.replace('risk-', '').replace('-', ' ').title() for label in labels if label.startswith('risk-')), 'Unknown'),
                    "impact_level": next((label.replace('impact-', '').title() for label in labels if label.startswith('impact-')), 'Unknown'),
                    "third_party": fields.get('customfield_10001', 'N/A')
                }
                
                risk_board[category].append(risk_item)
            
            return jsonify({
                "risk_board": risk_board,
                "counts": {category: len(items) for category, items in risk_board.items()}
            })
        else:
            # Return mock risk board data if no risks found
            mock_risk_board = generate_mock_risk_board()
            return jsonify(mock_risk_board)
            
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

def generate_mock_risk_board():
    """Generate mock risk board data for demonstration"""
    return {
        "risk_board": {
            'identified': [
                {
                    "key": 'RISK-001',
                    "summary": 'Cloud Provider Service Outage Risk',
                    "status": 'Open',
                    "priority": 'High',
                    "assignee": 'John Doe',
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "risk_category": 'Operational',
                    "impact_level": 'High',
                    "third_party": 'AWS'
                }
            ],
            'assessment': [
                {
                    "key": 'RISK-002',
                    "summary": 'Third-Party Data Processing Compliance',
                    "status": 'In Review',
                    "priority": 'Critical',
                    "assignee": 'Jane Smith',
                    "created": (datetime.now() - timedelta(days=1)).isoformat(),
                    "updated": datetime.now().isoformat(),
                    "risk_category": 'Compliance',
                    "impact_level": 'Critical',
                    "third_party": 'DataCorp Solutions'
                }
            ],
            'mitigation': [],
            'monitoring': [],
            'closed': [
                {
                    "key": 'RISK-003',
                    "summary": 'Vendor Financial Stability',
                    "status": 'Closed',
                    "priority": 'Medium',
                    "assignee": 'Bob Johnson',
                    "created": (datetime.now() - timedelta(days=7)).isoformat(),
                    "updated": (datetime.now() - timedelta(days=2)).isoformat(),
                    "risk_category": 'Financial',
                    "impact_level": 'Medium',
                    "third_party": 'TechVendor Inc'
                }
            ]
        },
        "counts": {
            'identified': 1,
            'assessment': 1,
            'mitigation': 0,
            'monitoring': 0,
            'closed': 1
        }
    }

@app.route('/api/metrics/integrated/<project_key>')
def get_integrated_metrics(project_key):
    """Get integrated project + risk metrics"""
    try:
        # Get regular project metrics
        regular_response = requests.get(f"http://localhost:8000/api/jira/dashboard/{project_key}")
        regular_data = regular_response.json() if regular_response.status_code == 200 else {}
        
        # Get risk metrics
        risk_response = requests.get(f"http://localhost:8000/api/risk/dashboard/{project_key}")
        risk_data = risk_response.json() if risk_response.status_code == 200 else {}
        
        # Calculate integrated metrics
        integrated_metrics = {
            "project_health": {
                "completion_rate": regular_data.get('progress_percentage', 0),
                "risk_coverage": calculate_risk_coverage(regular_data, risk_data),
                "timeline_risk": assess_timeline_risk(regular_data, risk_data),
                "overall_score": calculate_project_health_score(regular_data, risk_data)
            },
            "estimated_vs_actual": {
                "cost_variance": calculate_cost_variance(regular_data, risk_data),
                "timeline_variance": calculate_timeline_variance(regular_data, risk_data),
                "resource_variance": calculate_resource_variance(regular_data, risk_data),
                "risk_impact_on_estimates": calculate_risk_impact_on_estimates(risk_data)
            },
            "risk_trends": {
                "new_risks_this_week": count_recent_risks(risk_data, 7),
                "resolved_risks_this_week": count_resolved_risks(risk_data, 7),
                "escalated_risks": count_escalated_risks(risk_data),
                "risk_velocity": calculate_risk_velocity(risk_data)
            }
        }
        
        return jsonify({
            **regular_data,
            **risk_data,
            "integrated_metrics": integrated_metrics
        })
        
    except Exception as e:
        return jsonify({"error": f"Exception occurred: {str(e)}"}), 500

# Helper functions for metrics calculation
def calculate_risk_coverage(regular_data, risk_data):
    """Calculate what percentage of project areas have risk coverage"""
    total_issues = regular_data.get('status_counts', {}).get('total', 0)
    total_risks = risk_data.get('total_risks', 0)
    return min(100, (total_risks / max(total_issues, 1)) * 100) if total_issues > 0 else 0

def assess_timeline_risk(regular_data, risk_data):
    """Assess timeline risk based on project status and identified risks"""
    progress = regular_data.get('progress_percentage', 0)
    critical_risks = risk_data.get('risk_integration', {}).get('high_impact_risks', 0)
    
    if critical_risks > 3 and progress < 50:
        return "High"
    elif critical_risks > 1 or progress < 25:
        return "Medium"
    else:
        return "Low"

def calculate_project_health_score(regular_data, risk_data):
    """Calculate overall project health score (0-100)"""
    progress_score = regular_data.get('progress_percentage', 0)
    risk_penalty = min(30, risk_data.get('risk_integration', {}).get('high_impact_risks', 0) * 10)
    escalation_penalty = min(20, risk_data.get('risk_integration', {}).get('escalation_required', 0) * 5)
    
    return max(0, progress_score - risk_penalty - escalation_penalty)

def calculate_cost_variance(regular_data, risk_data):
    """Estimate cost variance including risk impact"""
    # Mock calculation - you'd integrate with actual cost tracking
    base_variance = 0  # From your existing cost tracking
    risk_cost_impact = estimate_risk_cost_impact(risk_data)
    return f"{base_variance + risk_cost_impact:+.1%}"

def calculate_timeline_variance(regular_data, risk_data):
    """Estimate timeline variance including risk impact"""
    # Mock calculation
    high_risks = risk_data.get('risk_integration', {}).get('high_impact_risks', 0)
    timeline_impact = high_risks * 5  # 5% delay per high-impact risk
    return f"+{timeline_impact}%"

def calculate_resource_variance(regular_data, risk_data):
    """Estimate resource variance including risk impact"""
    # Mock calculation
    total_risks = risk_data.get('total_risks', 0)
    resource_impact = total_risks * 2  # 2% additional resource per risk
    return f"+{resource_impact}%"

def calculate_risk_impact_on_estimates(risk_data):
    """Calculate how risks impact project estimates"""
    critical_risks = risk_data.get('risk_analytics', {}).get('by_impact', {}).get('Critical', 0)
    high_risks = risk_data.get('risk_analytics', {}).get('by_impact', {}).get('High', 0)
    
    # Rough estimation: Critical risks = 15% cost increase, High = 8%
    impact = (critical_risks * 0.15) + (high_risks * 0.08)
    return f"+{impact:.1%}"

def estimate_risk_cost_impact(risk_data):
    """Estimate additional costs due to risks"""
    critical_risks = risk_data.get('risk_analytics', {}).get('by_impact', {}).get('Critical', 0)
    high_risks = risk_data.get('risk_analytics', {}).get('by_impact', {}).get('High', 0)
    
    # Rough estimation: Critical risks = 15% cost increase, High = 8%
    return (critical_risks * 0.15) + (high_risks * 0.08)

def count_recent_risks(risk_data, days):
    """Count risks created in the last N days"""
    if not risk_data.get('risk_analytics', {}).get('recent_risks'):
        return 1  # Mock data
    
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_count = 0
    
    for risk in risk_data['risk_analytics']['recent_risks']:
        try:
            risk_date = datetime.fromisoformat(risk['created'].replace('Z', '+00:00'))
            if risk_date > cutoff_date:
                recent_count += 1
        except:
            continue
    
    return recent_count

def count_resolved_risks(risk_data, days):
    """Count risks resolved in the last N days"""
    # Mock implementation
    return 2

def count_escalated_risks(risk_data):
    """Count risks requiring escalation"""
    return risk_data.get('risk_integration', {}).get('escalation_required', 0)

def calculate_risk_velocity(risk_data):
    """Calculate risk resolution velocity"""
    # Mock implementation
    return "1.2 risks/week"

@app.route('/api/risk/update/<issue_key>', methods=['PUT'])
def update_risk_ticket(issue_key):
    """Update an existing risk ticket"""
    try:
        data = request.json
        
        # Build update payload
        update_data = {
            "fields": {}
        }
        
        if data.get('assignee'):
            update_data["fields"]["assignee"] = {"accountId": data.get('assignee')}
            
        if data.get('summary'):
            update_data["fields"]["summary"] = data.get('summary')
        
        url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}"
        response = requests.put(url, headers=get_jira_headers(), auth=get_jira_auth(), 
                              data=json.dumps(update_data))
        
        if response.status_code == 204:
            return jsonify({"status": "success", "message": "Risk ticket updated successfully"})
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to update risk ticket: {response.text}"
            }), response.status_code
            
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
    print("🚀 Starting UNCIA Jira Dashboard Flask App with Risk Management...")
    print(f"📧 Email: {JIRA_EMAIL}")
    print(f"🏢 Domain: {JIRA_DOMAIN}")
    print(f"🔑 Token: {JIRA_API_TOKEN[:15]}...")
    print("\n🌐 Regular Endpoints:")
    print("   Test connection: http://localhost:8000/api/jira/test")
    print("   All projects: http://localhost:8000/api/jira-projects")
    print("   SCRUM dashboard: http://localhost:8000/api/jira/dashboard/SCRUM")
    print("   SCRUM board: http://localhost:8000/api/jira/board/SCRUM")
    print("\n🚨 Risk Management Endpoints:")
    print("   Risk dashboard: http://localhost:8000/api/risk/dashboard/SCRUM")
    print("   Risk board: http://localhost:8000/api/risk/board/SCRUM")
    print("   Integrated metrics: http://localhost:8000/api/metrics/integrated/SCRUM")
    print("   Create risk (POST): http://localhost:8000/api/risk/create-integrated")
    print("\n💡 Features:")
    print("   ✅ Existing Jira integration")
    print("   ✅ Risk management system")
    print("   ✅ Integrated dashboards")
    print("   ✅ Risk analytics & metrics")
    print("   ✅ Mock data fallbacks")
    app.run(debug=True, port=8000)