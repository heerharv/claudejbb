// Extracted JavaScript from dashboard.html

const API_BASE = 'http://localhost:8000';
let currentProject = 'SCRUM';
let dashboardData = null;
let riskData = null;
let integratedMetrics = null;
let allIssuesData = [];
let currentCalendarDate = new Date();
let selectedDate = new Date();
let showRiskBoard = false;

// Example: Dates with tasks (format: 'YYYY-MM-DD')
const taskDates = ["2025-06-03", "2025-06-23"];

// Page detection
const bodyId = document.body.id;

function getSavedProject() {
    return localStorage.getItem('currentProject') || 'SCRUM';
}
function saveProject(key) {
    localStorage.setItem('currentProject', key);
}

window.addEventListener('DOMContentLoaded', function() {
    if (bodyId === 'dashboard-page') {
        loadProjects();
        initializeCalendar();
        setupIntersectionObserver();
        setupRiskModal();
        openSettingsModal(); // Open settings modal on load
    } else if (bodyId === 'kanban-page') {
        loadProjectsForKanban();
    } else if (bodyId === 'timeline-page') {
        // Timeline-specific logic if needed
    } else if (bodyId === 'risk-page') {
        loadProjects(); // if risk page needs project data
        setupRiskModal();
    } else if (bodyId === 'settings-page') {
        openSettingsModal();
    }
});

async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/api/jira-projects`);
        const data = await response.json();
        const select = document.getElementById('projectSelect');
        if (!select) return;
        select.innerHTML = '';
        data.values.forEach(project => {
            const option = document.createElement('option');
            option.value = project.key;
            option.textContent = `${project.key} - ${project.name}`;
            select.appendChild(option);
        });
        const saved = getSavedProject();
        select.value = saved;
        currentProject = saved;
        loadDataWithRisks();
        select.addEventListener('change', function() {
            currentProject = this.value;
            saveProject(currentProject);
            if (currentProject) {
                loadDataWithRisks();
            }
        });
    } catch (error) {
        showError('Failed to load projects: ' + error.message);
    }
}

async function loadProjectsForKanban() {
    try {
        const response = await fetch(`${API_BASE}/api/jira-projects`);
        const data = await response.json();
        const select = document.getElementById('projectSelect');
        if (!select) return;
        select.innerHTML = '';
        data.values.forEach(project => {
            const option = document.createElement('option');
            option.value = project.key;
            option.textContent = `${project.key} - ${project.name}`;
            select.appendChild(option);
        });
        const saved = getSavedProject();
        select.value = saved;
        currentProject = saved;
        updateBoard(); // Show board for saved project
        select.addEventListener('change', function() {
            currentProject = this.value;
            saveProject(currentProject);
            if (currentProject) {
                updateBoard(); // Update board on project change
            }
        });
    } catch (error) {
        showError('Failed to load projects: ' + error.message);
    }
}

async function loadDataWithRisks() {
    if (!currentProject) return;
    document.getElementById('loading').style.display = 'block';
    // CHANGED: Use 'dashboard-section' instead of 'dashboard'
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('error-container').innerHTML = '';
    try {
        const response = await fetch(`${API_BASE}/api/jira/dashboard/${currentProject}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        dashboardData = await response.json();
        try {
            const riskResponse = await fetch(`${API_BASE}/api/risk/dashboard/${currentProject}`);
            if (riskResponse.ok) {
                const riskResponseData = await riskResponse.json();
                riskData = riskResponseData.risk_analytics || {};
                dashboardData.risk_integration = riskResponseData.risk_integration || {};
                dashboardData.total_risks = riskResponseData.total_risks || 0;
            } else {
                riskData = generateMockRiskData();
                dashboardData.risk_integration = { high_impact_risks: 3, escalation_required: 2, risk_to_project_ratio: 0.15 };
                dashboardData.total_risks = 8;
            }
        } catch (error) {
            riskData = generateMockRiskData();
            dashboardData.risk_integration = { high_impact_risks: 3, escalation_required: 2, risk_to_project_ratio: 0.15 };
            dashboardData.total_risks = 8;
        }
        updateIntegratedDashboard();
        await loadAllIssuesForCalendar();
    } catch (error) {
        showError('Failed to load dashboard data: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function generateMockRiskData() {
    return {
        by_category: { 'Operational': 2, 'Financial': 1, 'Cybersecurity': 3, 'Technology': 1, 'Compliance': 1 },
        by_impact: { 'Critical': 1, 'High': 2, 'Medium': 3, 'Low': 2 },
        by_status: { 'Open': 3, 'In Progress': 2, 'Under Review': 2, 'Closed': 1 },
        recent_risks: [
            { key: 'RISK-001', summary: 'Cloud Provider Service Outage Risk', status: 'Open', category: 'Operational', impact: 'High', created: new Date().toISOString() },
            { key: 'RISK-002', summary: 'Third-Party Data Processing Compliance', status: 'In Progress', category: 'Compliance', impact: 'Critical', created: new Date(Date.now() - 86400000).toISOString() }
        ],
        critical_risks: [
            { key: 'RISK-002', summary: 'Third-Party Data Processing Compliance', impact: 'Critical', status: 'In Progress' }
        ]
    };
}

function updateIntegratedDashboard() {
    if (!dashboardData) return;
    const { status_counts, progress_percentage, recent_issues, assignee_distribution } = dashboardData;
    const { risk_integration, total_risks } = dashboardData;
    const elTotalIssues = document.getElementById('totalIssues');
    if (elTotalIssues) elTotalIssues.textContent = status_counts.total || 0;
    const elCompletedIssues = document.getElementById('completedIssues');
    if (elCompletedIssues) elCompletedIssues.textContent = status_counts.done || 0;
    const elProgressIssues = document.getElementById('progressIssues');
    if (elProgressIssues) elProgressIssues.textContent = status_counts.in_progress || 0;
    const elTodoIssues = document.getElementById('todoIssues');
    if (elTodoIssues) elTodoIssues.textContent = status_counts.todo || 0;
    const elTotalRisks = document.getElementById('totalRisks');
    if (elTotalRisks) elTotalRisks.textContent = total_risks || 0;
    const elCriticalRisks = document.getElementById('criticalRisks');
    if (elCriticalRisks) elCriticalRisks.textContent = risk_integration?.high_impact_risks || 0;
    const elResolvedRisks = document.getElementById('resolvedRisks');
    if (elResolvedRisks) elResolvedRisks.textContent = calculateResolvedRisksThisMonth();
    const elRiskTotalDisplay = document.getElementById('riskTotalDisplay');
    if (elRiskTotalDisplay) elRiskTotalDisplay.textContent = total_risks || 0;
    const elCriticalRiskDisplay = document.getElementById('criticalRiskDisplay');
    if (elCriticalRiskDisplay) elCriticalRiskDisplay.textContent = risk_integration?.high_impact_risks || 0;
    const elEscalationDisplay = document.getElementById('escalationDisplay');
    if (elEscalationDisplay) elEscalationDisplay.textContent = risk_integration?.escalation_required || 0;
    const elRiskCoverageDisplay = document.getElementById('riskCoverageDisplay');
    if (elRiskCoverageDisplay) elRiskCoverageDisplay.textContent = Math.round((risk_integration?.risk_to_project_ratio || 0) * 100) + '%';
    const riskAdjustedProgress = calculateRiskAdjustedProgress(progress_percentage);
    const elProgressBar = document.getElementById('progressBar');
    if (elProgressBar) elProgressBar.style.width = riskAdjustedProgress + '%';
    const elProgressText = document.getElementById('progressText');
    if (elProgressText) elProgressText.textContent = `${riskAdjustedProgress}% Complete (Risk Adjusted)`;
    updateIntegratedStatusChart(status_counts, riskData);
    updateRiskDistributionChart(riskData);
    updateAssignmentChart(assignee_distribution, status_counts.total);
    updateIntegratedRecentActivity(recent_issues, riskData?.recent_risks);
    updateIntegratedInsights();
    updateRiskAwareTimeline();
    if (!showRiskBoard) {
        updateBoard();
    }
    // CHANGED: Use 'dashboard-section' instead of 'dashboard'
    const elDashboardSection = document.getElementById('dashboard-section');
    if (elDashboardSection) elDashboardSection.style.display = 'block';
}

function calculateRiskAdjustedProgress(baseProgress) {
    if (!riskData || !dashboardData.risk_integration) return baseProgress;
    const highImpactRisks = dashboardData.risk_integration.high_impact_risks || 0;
    const riskPenalty = Math.min(20, highImpactRisks * 5);
    return Math.max(0, Math.min(100, baseProgress - riskPenalty));
}

function updateIntegratedStatusChart(statusCounts, riskAnalytics) {
    const canvas = document.getElementById('statusChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (window.statusChart && typeof window.statusChart.destroy === 'function') {
        window.statusChart.destroy();
    }
    const projectData = [
        statusCounts.todo || 0,
        statusCounts.in_progress || 0,
        statusCounts.done || 0
    ];
    const riskStatusData = [
        (riskAnalytics?.by_status?.["Open"] || 0) + (riskAnalytics?.by_status?.["To Do"] || 0),
        riskAnalytics?.by_status?.["In Progress"] || 0,
        (riskAnalytics?.by_status?.["Closed"] || 0) + (riskAnalytics?.by_status?.["Done"] || 0)
    ];
    window.statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['To Do', 'In Progress', 'Done'],
            datasets: [{
                label: 'Project Tasks',
                data: projectData,
                backgroundColor: ['#F87171', '#FBBF24', '#34D399'],
                borderWidth: 3,
                borderColor: '#ffffff'
            }, {
                label: 'Risk Items',
                data: riskStatusData,
                backgroundColor: ['#FCA5A5', '#FCD34D', '#6EE7B7'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#374151', padding: 20 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const datasetLabel = context.dataset.label;
                            const value = context.parsed;
                            return `${datasetLabel} - ${context.label}: ${value}`;
                        }
                    }
                }
            }
        }
    });
}

function updateRiskDistributionChart(riskAnalytics) {
    const canvas = document.getElementById('riskChart');
    if (!canvas || !riskAnalytics?.by_category) return;
    const ctx = canvas.getContext('2d');
    if (window.riskChart && typeof window.riskChart.destroy === 'function') {
        window.riskChart.destroy();
    }
    const categories = Object.keys(riskAnalytics.by_category);
    const values = Object.values(riskAnalytics.by_category);
    if (categories.length === 0) {
        ctx.fillStyle = '#6b7280';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No risk data available', canvas.width / 2, canvas.height / 2);
        return;
    }
    window.riskChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Risk Count',
                data: values,
                backgroundColor: [
                    '#EF4444', '#F59E0B', '#8B5CF6', 
                    '#06B6D4', '#10B981', '#F97316'
                ],
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#6B7280' } },
                x: { ticks: { color: '#6B7280', maxRotation: 45 } }
            }
        }
    });
}

function updateAssignmentChart(assigneeDistribution, totalIssues) {
    const canvas = document.getElementById('assignmentChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (window.assignmentChart && typeof window.assignmentChart.destroy === 'function') {
        window.assignmentChart.destroy();
    }
    const assignedCount = Object.values(assigneeDistribution || {}).reduce((a, b) => a + b, 0);
    const unassignedCount = Math.max(0, (totalIssues || 0) - assignedCount);
    const data = [assignedCount, unassignedCount];
    if (totalIssues > 0) {
        window.assignmentChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Assigned', 'Unassigned'],
                datasets: [{
                    data: data,
                    backgroundColor: ['#60A5FA', '#F97316'],
                    borderWidth: 3,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#374151', padding: 20 }
                    }
                }
            }
        });
    } else {
        ctx.fillStyle = '#6b7280';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
    }
}

function updateIntegratedRecentActivity(projectIssues, riskIssues) {
    const container = document.getElementById('recentIssues');
    const allItems = [];
    (projectIssues || []).slice(0, 8).forEach(issue => {
        allItems.push({ ...issue, type: 'project', icon: '📋' });
    });
    (riskIssues || []).forEach(risk => {
        allItems.push({ ...risk, type: 'risk', icon: '🚨' });
    });
    allItems.sort((a, b) => new Date(b.created || b.updated) - new Date(a.created || a.updated));
    if (allItems.length === 0) {
        container.innerHTML = '<div class="no-tasks">No recent activity</div>';
        return;
    }
    container.innerHTML = allItems.slice(0, 12).map(item => {
        const statusClass = getStatusClass(item.status);
        const typeClass = item.type === 'risk' ? 'risk-activity' : 'project-activity';
        return `
            <div class="activity-item ${typeClass}">
                <div class="activity-header">
                    <span class="activity-type">${item.icon}</span>
                    <a href="#" class="issue-key-link">${item.key}</a>
                    <span class="status-badge ${statusClass}">${item.status}</span>
                    </div>
                <p class="activity-summary">${item.summary}</p>
                <div class="activity-meta">
                    <span>${item.assignee || 'Unassigned'}</span>
                    <span>•</span>
                    <span>${item.type === 'risk' ? 'Risk' : 'Task'}</span>
                    <span>•</span>
                    <span>Updated ${new Date(item.updated || item.created).toLocaleDateString()}</span>
                </div>
            </div>
        `;
    }).join('');
}

function updateIntegratedInsights() {
    const container = document.getElementById('projectInsights');
    const { status_counts, risk_integration } = dashboardData;
    let insights = [];
    if (risk_integration?.high_impact_risks > 0) {
        insights.push({
            type: 'warning',
            title: '⚠️ High-Impact Risks Detected',
            message: `${risk_integration.high_impact_risks} high-impact risks require immediate attention. Consider escalating to project stakeholders.`
        });
    }
    if (risk_integration?.escalation_required > 0) {
        insights.push({
            type: 'info',
            title: '📢 Escalation Required',
            message: `${risk_integration.escalation_required} risks require management escalation for resolution.`
        });
    }
    if (status_counts.done > 0 && risk_integration?.high_impact_risks === 0) {
        insights.push({
            type: 'success',
            title: '✅ Strong Risk Management',
            message: `Project is progressing well with ${status_counts.done} completed tasks and no critical risks.`
        });
    }
    const totalIssues = status_counts.total || 0;
    if (totalIssues > 0) {
        insights.push({
            type: 'info',
            title: '📊 Project Status',
            message: `${totalIssues} total issues with ${Math.round((dashboardData.progress_percentage || 0))}% completion rate.`
        });
    }
    container.innerHTML = insights.map(insight => `
        <div class="insight-item insight-${insight.type}">
            <h4>${insight.title}</h4>
            <p>${insight.message}</p>
        </div>
    `).join('');
}

function updateRiskAwareTimeline() {
    const { status_counts, progress_percentage } = dashboardData;
    let currentStep = 1;
    let stepText = "Take Over";
    if (progress_percentage > 0) {
        currentStep = 2;
        stepText = "Day 0";
    }
    if (status_counts.done > 0 && status_counts.done >= status_counts.total * 0.1) {
        currentStep = 3;
        stepText = "GO LIVE INTIATION";
    }
    if (status_counts.done >= status_counts.total * 0.25) {
        currentStep = 4;
        stepText = "Readiness for Day !";
    }
    if (status_counts.done >= status_counts.total * 0.4) {
        currentStep = 5;
        stepText = "Solution Design";
    }
    if (status_counts.done >= status_counts.total * 0.6) {
        currentStep = 6;
        stepText = "Reports";
    }
    if (status_counts.done >= status_counts.total * 0.8) {
        currentStep = 7;
        stepText = "Readiness for Go Live";
    }
    if (status_counts.done === status_counts.total) {
        currentStep = 8;
        stepText = "GO LIVE";
    }
    const steps = document.querySelectorAll('.timeline-step');
    const connectors = document.querySelectorAll('.timeline-connector');
    steps.forEach((step, index) => {
        const stepNumber = index + 1;
        step.classList.remove('completed', 'current');
        if (stepNumber < currentStep) {
            step.classList.add('completed');
        } else if (stepNumber === currentStep) {
            step.classList.add('current');
        }
    });
    connectors.forEach((connector, index) => {
        connector.classList.remove('completed');
        if (index + 1 < currentStep) {
            connector.classList.add('completed');
        }
    });
    document.getElementById('timelineProgressText').textContent = 
        `Step ${currentStep} of 8 - ${stepText}`;
}

async function updateBoard() {
    if (!currentProject) return;
    try {
        const response = await fetch(`${API_BASE}/api/jira/board/${currentProject}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const boardData = await response.json();
        renderProjectBoard(boardData);
    } catch (error) {
        console.error('Failed to load board data:', error);
        showBoardError('Failed to load board data: ' + error.message);
    }
}

function renderProjectBoard(boardData) {
    const board = boardData.board;
    const boardContainer = document.getElementById('mainBoard');
    boardContainer.innerHTML = '';
    const preferredOrder = [
        'Backlog',
        'TAKE OVER FORM',
        'DAY 0 INITIATION',
        'READINESS FOR ...',
        'SOLUTION DESIGN',
        'IN PROGRESS',
        'DATA MIGRATION',
        'REPORTS',
        'EXTRAS',
        'GO LIVE INITIATION',
        'GO LIVE',
        'COMPLETED',
        'Done'
    ];
    const rendered = new Set();
    preferredOrder.forEach(statusName => {
        if (board[statusName]) {
            const issues = board[statusName];
            boardContainer.innerHTML += `
                <div class="kanban-column">
                    <div class="column-header">
                        <h3>${statusName}</h3>
                        <span class="issue-count">${issues.length}</span>
                    </div>
                    <div class="column-content">
                        ${renderBoardColumn(issues, 'No tasks in this column')}
                    </div>
                </div>
            `;
            rendered.add(statusName);
        }
    });
    Object.keys(board).forEach(statusName => {
        if (!rendered.has(statusName)) {
            const issues = board[statusName];
            boardContainer.innerHTML += `
                <div class="kanban-column">
                    <div class="column-header">
                        <h3>${statusName}</h3>
                        <span class="issue-count">${issues.length}</span>
                    </div>
                    <div class="column-content">
                        ${renderBoardColumn(issues, 'No tasks in this column')}
                    </div>
                </div>
            `;
        }
    });
}

function renderBoardColumn(issues, emptyMessage) {
    if (!issues || issues.length === 0) {
        return `<div class="no-issues">${emptyMessage}</div>`;
    }
    const now = new Date();
    return issues.map(issue => {
        const startDate = issue.created ? new Date(issue.created).toLocaleDateString() : 'N/A';
        const endDate = issue.duedate ? new Date(issue.duedate).toLocaleDateString() : 'N/A';
        const assigneeName = issue.assignee_name || issue.assignee || 'Unassigned';
        let cardClass = '';
        let statusLabel = '';
        let statusLabelClass = '';
        if (issue.duedate) {
            const due = new Date(issue.duedate);
            const diffDays = (due - now) / (1000 * 60 * 60 * 24);
            if (due < now) {
                cardClass = 'task-overdue';
                statusLabel = 'Delayed';
                statusLabelClass = 'badge-delayed';
            } else if (diffDays <= 2) {
                cardClass = 'task-near-due';
                statusLabel = 'Near Deadline';
                statusLabelClass = 'badge-near-due';
            }
        }
        if (issue.status) {
            const status = issue.status.toLowerCase();
            if (status === 'done' || status === 'completed' || status === 'resolved') {
                cardClass = 'task-done';
                statusLabel = 'Done';
                statusLabelClass = 'badge-done';
            } else if (status === 'in progress' || status === 'started' || status === 'inprogress') {
                cardClass = 'task-inprogress';
                statusLabel = 'In Progress';
                statusLabelClass = 'badge-inprogress';
            }
        }
        if (!statusLabel) {
            statusLabel = 'To Do';
            statusLabelClass = 'badge-todo';
        }
        // Comment button if comments exist
        const hasComments = issue.comments && issue.comments.length > 0;
        const commentBtn = `<button class="comment-btn" title="Show Comments" data-count="${hasComments ? issue.comments.length : ''}" onclick="event.stopPropagation(); showCommentsModal('${issue.key}')">💬</button>`;
        return `
            <div class="issue-card ${cardClass}" onclick="openIssueDetails('${issue.key}')">
                <div class="issue-card-status-row">
                    <span class="issue-status-badge ${statusLabelClass}">${statusLabel}</span>
                    ${commentBtn}
                </div>
                <div class="issue-key">${issue.key}</div>
                <div class="issue-summary">${issue.summary || 'No summary'}</div>
                <div class="issue-meta">
                    <span class="issue-assignee-badge">👤 ${assigneeName}</span>
                    <span class="issue-type">${issue.issuetype || 'Task'}</span>
                    <span class="issue-dates">Start: ${startDate}</span>
                    <span class="issue-dates">End: ${endDate}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Modal for comments
function showCommentsModal(issueKey) {
    // Find the issue in the current board data
    let issue = null;
    if (window.lastBoardData && window.lastBoardData.board) {
        for (const col of Object.values(window.lastBoardData.board)) {
            issue = col.find(i => i.key === issueKey);
            if (issue) break;
        }
    }
    if (!issue || !issue.comments || issue.comments.length === 0) {
        alert('No comments for this issue.');
        return;
    }
    let modal = document.getElementById('commentsModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'commentsModal';
        modal.className = 'comments-modal';
        document.body.appendChild(modal);
    }
    modal.innerHTML = `
        <div class='comments-modal-content'>
            <div class='comments-modal-header'>
                <span>💬 Comments for ${issue.key}</span>
                <button class='close-modal-btn' onclick='closeCommentsModal()'>×</button>
            </div>
            <div class='comments-list'>
                ${issue.comments.map(c => `
                    <div class='comment-item'>
                        <div class='comment-author'><strong>${c.author}</strong> <span class='comment-date'>${new Date(c.created).toLocaleString()}</span></div>
                        <div class='comment-body'>${c.body}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    modal.style.display = 'block';
}
function closeCommentsModal() {
    const modal = document.getElementById('commentsModal');
    if (modal) modal.style.display = 'none';
}
// Store last board data for modal lookup
const _origRenderProjectBoard = window.renderProjectBoard;
window.renderProjectBoard = function(boardData) {
    window.lastBoardData = boardData;
    return _origRenderProjectBoard.call(this, boardData);
};

function toggleRiskBoard() {
    showRiskBoard = !showRiskBoard;
    const toggleBtn = document.getElementById('board-toggle-btn');
    if (showRiskBoard) {
        loadRiskBoard();
        toggleBtn.textContent = '📋 Show Project Board';
    } else {
        updateBoard();
        toggleBtn.textContent = '🚨 Show Risk Board';
    }
}

async function loadRiskBoard() {
    const boardContainer = document.getElementById('mainBoard');
    const mockRiskBoard = {
        risk_board: {
            identified: [
                {
                    key: 'RISK-001',
                    summary: 'Cloud Provider Service Outage Risk',
                    status: 'Open',
                    priority: 'High',
                    assignee: 'John Doe',
                    risk_category: 'Operational',
                    impact_level: 'High',
                    third_party: 'AWS'
                }
            ],
            assessment: [
                {
                    key: 'RISK-002',
                    summary: 'Third-Party Data Processing Compliance',
                    status: 'In Review',
                    priority: 'Critical',
                    assignee: 'Jane Smith',
                    risk_category: 'Compliance',
                    impact_level: 'Critical',
                    third_party: 'DataCorp Solutions'
                }
            ],
            mitigation: [],
            monitoring: [],
            closed: [
                {
                    key: 'RISK-003',
                    summary: 'Vendor Financial Stability',
                    status: 'Closed',
                    priority: 'Medium',
                    assignee: 'Bob Johnson',
                    risk_category: 'Financial',
                    impact_level: 'Medium',
                    third_party: 'TechVendor Inc'
                }
            ]
        },
        counts: {
            identified: 1,
            assessment: 1,
            mitigation: 0,
            monitoring: 0,
            closed: 1
        }
    };
    renderRiskBoard(mockRiskBoard);
}

function renderRiskBoard(boardData) {
    const { risk_board, counts } = boardData;
    const boardContainer = document.getElementById('mainBoard');
    boardContainer.innerHTML = `
        <div class="risk-column">
            <div class="risk-column-header identified-header">
                <h3>🆔 Identified</h3>
                <span class="issue-count">${counts.identified || 0}</span>
            </div>
            <div class="column-content">
                ${renderRiskItems(risk_board.identified || [])}
            </div>
        </div>
        <div class="risk-column">
            <div class="risk-column-header assessment-header">
                <h3>📊 Assessment</h3>
                <span class="issue-count">${counts.assessment || 0}</span>
            </div>
            <div class="column-content">
                ${renderRiskItems(risk_board.assessment || [])}
            </div>
        </div>
        <div class="risk-column">
            <div class="risk-column-header mitigation-header">
                <h3>🛡️ Mitigation</h3>
                <span class="issue-count">${counts.mitigation || 0}</span>
            </div>
            <div class="column-content">
                ${renderRiskItems(risk_board.mitigation || [])}
            </div>
        </div>
        <div class="risk-column">
            <div class="risk-column-header monitoring-header">
                <h3>👁️ Monitoring</h3>
                <span class="issue-count">${counts.monitoring || 0}</span>
            </div>
            <div class="column-content">
                ${renderRiskItems(risk_board.monitoring || [])}
            </div>
        </div>
        <div class="risk-column">
            <div class="risk-column-header closed-header">
                <h3>✅ Closed</h3>
                <span class="issue-count">${counts.closed || 0}</span>
            </div>
            <div class="column-content">
                ${renderRiskItems(risk_board.closed || [])}
            </div>
        </div>
    `;
}

function renderRiskItems(items) {
    if (!items || items.length === 0) {
        return '<div class="no-issues">No risks in this stage</div>';
    }
    return items.map(risk => `
        <div class="risk-item" onclick="openIssueDetails('${risk.key}')">
            <div class="risk-item-header">
                <span class="risk-key">${risk.key}</span>
                <span class="risk-impact-badge impact-${risk.impact_level.toLowerCase()}">${risk.impact_level}</span>
            </div>
            <div class="risk-summary">${risk.summary}</div>
            <div class="risk-meta">
                <small>${risk.risk_category} | ${risk.assignee}</small>
                <small>${risk.third_party}</small>
            </div>
        </div>
    `).join('');
}

function setupRiskModal() {
    document.querySelectorAll('.impact-level-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.impact-level-option').forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    document.getElementById('createRiskModal').addEventListener('click', function(event) {
        if (event.target === this) {
            closeRiskModal();
        }
    });
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && document.getElementById('createRiskModal').style.display === 'block') {
            closeRiskModal();
        }
    });
}

function showCreateRiskModal() {
    document.getElementById('createRiskModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeRiskModal() {
    document.getElementById('createRiskModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    document.getElementById('riskForm').reset();
    document.querySelectorAll('.impact-level-option').forEach(opt => opt.classList.remove('selected'));
}

function submitRiskForm(event) {
    event.preventDefault();
    const selectedImpact = document.querySelector('.impact-level-option.selected');
    const formData = {
        risk_title: document.getElementById('riskTitle').value,
        risk_category: document.getElementById('riskCategory').value,
        third_party: document.getElementById('thirdParty').value,
        risk_description: document.getElementById('riskDescription').value,
        impact_level: selectedImpact ? selectedImpact.dataset.value : null,
        departments_affected: Array.from(document.querySelectorAll('input[name="departments"]:checked')).map(cb => cb.value),
        escalation_required: document.getElementById('escalationRequired').checked,
        recommended_action: document.getElementById('recommendedAction').value
    };
    if (!formData.risk_title || !formData.risk_category || !formData.third_party || 
        !formData.risk_description || !formData.impact_level) {
        alert('Please fill in all required fields');
        return;
    }
    createRiskTicket(formData);
}

async function createRiskTicket(formData) {
    try {
        const response = await fetch(`${API_BASE}/api/risk/create-integrated`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...formData,
                project_key: currentProject,
                date_identified: new Date().toISOString().split('T')[0]
            })
        });
        if (response.ok) {
            const result = await response.json();
            showSuccess('Risk ticket created successfully!');
            loadDataWithRisks();
            closeRiskModal();
        } else {
            throw new Error('Backend endpoint not available');
        }
    } catch (error) {
        showSuccess('Risk ticket would be created successfully! (Mock response - implement backend endpoint)');
        closeRiskModal();
        if (riskData) {
            riskData.recent_risks.unshift({
                key: `RISK-${String(Date.now()).slice(-3)}`,
                summary: formData.risk_title,
                status: 'Open',
                category: formData.risk_category,
                impact: formData.impact_level,
                created: new Date().toISOString()
            });
            riskData.by_category[formData.risk_category] = (riskData.by_category[formData.risk_category] || 0) + 1;
            riskData.by_impact[formData.impact_level] = (riskData.by_impact[formData.impact_level] || 0) + 1;
            riskData.by_status['Open'] = (riskData.by_status['Open'] || 0) + 1;
            dashboardData.total_risks = (dashboardData.total_risks || 0) + 1;
            if (formData.impact_level === 'Critical' || formData.impact_level === 'High') {
                dashboardData.risk_integration.high_impact_risks = (dashboardData.risk_integration.high_impact_risks || 0) + 1;
            }
            if (formData.escalation_required) {
                dashboardData.risk_integration.escalation_required = (dashboardData.risk_integration.escalation_required || 0) + 1;
            }
            updateIntegratedDashboard();
        }
    }
}

function calculateResolvedRisksThisMonth() {
    if (!riskData?.recent_risks) return 2;
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    return riskData.recent_risks.filter(risk => 
        risk.status.toLowerCase().includes('closed') || 
        risk.status.toLowerCase().includes('resolved')
    ).length;
}

function getStatusClass(status) {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('done') || statusLower.includes('complete') || statusLower.includes('closed')) {
        return 'status-done';
    } else if (statusLower.includes('progress')) {
        return 'status-progress';
    } else {
        return 'status-todo';
    }
}

function openIssueDetails(issueKey) {
    const jiraUrl = `https://uncia-team-vmevzjmu.atlassian.net/browse/${issueKey}`;
    window.open(jiraUrl, '_blank');
}

function showBoardError(message) {
    const boardContainer = document.getElementById('mainBoard');
    boardContainer.innerHTML = `<div class="no-issues">Error: ${message}</div>`;
}

function showError(message) {
    const container = document.getElementById('error-container');
    if (container) container.innerHTML = `
        <div class="error">
            <strong>Error:</strong> ${message}
            <br><small>Make sure your Flask app is running on http://localhost:8000</small>
        </div>
    `;
}

function showSuccess(message) {
    const container = document.getElementById('error-container');
    if (container) container.innerHTML = `
        <div class="success">
            <strong>Success:</strong> ${message}
        </div>
    `;
    setTimeout(() => container.innerHTML = '', 3000);
}

function initializeCalendar() {
    updateCalendarDisplay();
    document.getElementById('prevMonth').addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
        updateCalendarDisplay();
    });
    document.getElementById('nextMonth').addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
        updateCalendarDisplay();
    });
    selectedDate = new Date();
    updateSelectedDateDisplay(selectedDate);
    updateDailyTasks();
}

function updateSelectedDateDisplay(date) {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const selectedDateMonth = document.getElementById('selectedDateMonth');
    if (selectedDateMonth) selectedDateMonth.textContent = monthNames[date.getMonth()];
    const selectedDateWeekday = document.getElementById('selectedDateWeekday');
    if (selectedDateWeekday) selectedDateWeekday.textContent = dayNames[date.getDay()];
    const numberEl = document.getElementById('selectedDateNumber');
    if (numberEl) numberEl.textContent = date.getDate();
    numberEl.classList.remove('pop-in');
    void numberEl.offsetWidth;
    numberEl.classList.add('pop-in');
}

function updateCalendarDisplay() {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    const calendarTitle = document.getElementById('calendarTitle');
    if (calendarTitle) calendarTitle.textContent = `${monthNames[month]} ${year}`;
    const weekdaysContainer = document.getElementById('calendarWeekdays');
    if (!weekdaysContainer) return;
    weekdaysContainer.innerHTML = '';
    const weekdays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    weekdays.forEach(day => {
        const weekdayElement = document.createElement('div');
        weekdayElement.className = 'calendar-weekday';
        weekdayElement.textContent = day;
        weekdaysContainer.appendChild(weekdayElement);
    });
    const calendarGrid = document.getElementById('calendarGrid');
    if (!calendarGrid) return;
    calendarGrid.innerHTML = '';
    calendarGrid.classList.remove('calendar-grid');
    void calendarGrid.offsetWidth;
    calendarGrid.classList.add('calendar-grid');
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    const prevMonth = new Date(year, month - 1, 0);
    for (let i = startingDay - 1; i >= 0; i--) {
        const day = prevMonth.getDate() - i;
        const dayElement = createCalendarDay(day, true, new Date(year, month - 1, day));
        calendarGrid.appendChild(dayElement);
    }
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = createCalendarDay(day, false, new Date(year, month, day));
        calendarGrid.appendChild(dayElement);
    }
    const totalCells = calendarGrid.children.length;
    const remainingCells = 42 - totalCells;
    for (let day = 1; day <= remainingCells; day++) {
        const dayElement = createCalendarDay(day, true, new Date(year, month + 1, day));
        calendarGrid.appendChild(dayElement);
    }
}

function createCalendarDay(day, isOtherMonth, date) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';
    dayElement.textContent = day;
    if (isOtherMonth) {
        dayElement.classList.add('other-month');
    }
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
        dayElement.classList.add('today');
    }
    if (date.toDateString() === selectedDate.toDateString()) {
        dayElement.classList.add('selected');
    }
    const tasksOnDate = getTasksForDate(date);
    if (tasksOnDate.length > 0) {
        dayElement.classList.add('has-tasks');
        const dot = document.createElement('span');
        dot.className = 'calendar-task-dot';
        dayElement.appendChild(dot);
    }
    dayElement.addEventListener('click', () => {
        document.querySelectorAll('.calendar-day.selected').forEach(el => {
            el.classList.remove('selected');
        });
        dayElement.classList.add('selected');
        selectedDate = new Date(date);
        updateSelectedDateDisplay(selectedDate);
        updateDailyTasks();
    });
    return dayElement;
}

// Helper to robustly parse date strings
function parseIssueDate(dateStr) {
    if (!dateStr) return null;
    // Try ISO first
    let d = new Date(dateStr);
    if (!isNaN(d)) return d;
    // Try Jira format (e.g., 2025-07-16T00:00:00.000+0000)
    if (typeof dateStr === 'string' && dateStr.length >= 10) {
        // Remove timezone if present
        const cleaned = dateStr.replace(/\+\d{4}$/, '').replace(/Z$/, '');
        d = new Date(cleaned);
        if (!isNaN(d)) return d;
    }
    return null;
}

function getTasksForDate(date) {
    if (!allIssuesData || allIssuesData.length === 0) {
        return [];
    }
    const dateString = date.toDateString();
    return allIssuesData.filter(issue => {
        let taskDate = null;
        if (issue.duedate) {
            taskDate = parseIssueDate(issue.duedate);
        } else if (issue.created) {
            taskDate = parseIssueDate(issue.created);
        }
        if (taskDate) {
            return taskDate.toDateString() === dateString;
        }
        return false;
    });
}

function isTaskOverdue(task) {
    if (!task.duedate) return false;
    const due = new Date(task.duedate);
    const now = new Date();
    // Check if due date is in the past (before today)
    return due < now && !(task.status && ["Done", "Closed", "Resolved"].includes(task.status));
}

function renderOverdueTasksCard() {
    const overdueTasks = (allIssuesData || []).filter(isTaskOverdue);
    const container = document.getElementById('overdueTasksCard');
    if (!container) return;
    if (overdueTasks.length === 0) {
        container.innerHTML = '<div class="no-tasks">No overdue tasks 🎉</div>';
        return;
    }
    container.innerHTML = overdueTasks.map(task => {
        const startDate = task.start_date ? new Date(task.start_date).toLocaleDateString() : (task.created ? new Date(task.created).toLocaleDateString() : 'N/A');
        const endDate = task.end_date ? new Date(task.end_date).toLocaleDateString() : (task.duedate ? new Date(task.duedate).toLocaleDateString() : 'N/A');
        const assigneeName = task.assignee_name || (task.assignee && task.assignee.name) || 'Unassigned';
        return `
            <div class="overdue-task-card">
                <div class="overdue-task-header">
                    <span class="overdue-task-key">${task.key}</span>
                    <button class="overdue-bell-btn" title="Announce overdue in Teams" onclick="announceOverdueTask('${task.key}', this)">🔔</button>
                </div>
                <div class="overdue-task-summary">${task.summary || 'No summary'}</div>
                <div class="overdue-task-meta">
                    <span>👤 ${assigneeName}</span>
                    <span>Start: ${startDate}</span>
                    <span>End: ${endDate}</span>
                </div>
            </div>
        `;
    }).join('');
}

async function announceOverdueTask(issueKey, btn) {
    btn.disabled = true;
    btn.innerText = '🔔...';
    try {
        const res = await fetch(`${API_BASE}/api/announce-overdue-task/${issueKey}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            btn.innerText = '✅';
            showSuccess('Teams notification sent!');
        } else {
            btn.innerText = '❌';
            showError(data.message || 'Failed to send notification');
        }
    } catch (e) {
        btn.innerText = '❌';
        showError('Failed to send notification');
    }
    setTimeout(() => { btn.innerText = '🔔'; btn.disabled = false; }, 2000);
}

function updateDailyTasks() {
    const tasksOnDate = getTasksForDate(selectedDate);
    const titleElement = document.getElementById('selectedDateTitle');
    const tasksListElement = document.getElementById('dailyTasksList');
    const dateStr = selectedDate.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    titleElement.innerHTML = `📋 Tasks for ${dateStr}`;
    if (tasksOnDate.length === 0) {
        tasksListElement.innerHTML = '<div class="no-tasks">No tasks due or created on this date</div>';
        return;
    }
    tasksListElement.innerHTML = '';
    tasksOnDate.forEach((task, idx) => {
        const dateType = task.duedate ? 'Due' : 'Created';
        const typeName = task.issuetype && task.issuetype.name ? task.issuetype.name : 'Task';
        const priorityName = task.priority && task.priority.name ? task.priority.name : '';
        const priorityClass = priorityName ? getPriorityClass(priorityName.toLowerCase()) : '';
        const overdue = isTaskOverdue(task);
        const bellBtn = overdue ? `<button class="overdue-bell-btn" title="Announce overdue in Teams" onclick="event.stopPropagation(); announceOverdueTask('${task.key}', this)">🔔</button>` : '';
        const startDate = task.start_date ? new Date(task.start_date).toLocaleDateString() : (task.created ? new Date(task.created).toLocaleDateString() : 'N/A');
        const endDate = task.end_date ? new Date(task.end_date).toLocaleDateString() : (task.duedate ? new Date(task.duedate).toLocaleDateString() : 'N/A');
        const assigneeName = task.assignee_name || (task.assignee && task.assignee.name) || 'Unassigned';
        const html = `
            <div class="task-item" style="animation-delay: ${idx * 0.07}s" onclick="openIssueDetails('${task.key}')">
                <div class="activity-header">
                    <span class="activity-key">${task.key}</span>
                    <span class="activity-status-badge">${dateType}</span>
                    ${priorityName ? `<span class=\"activity-status-badge\" style=\"background:#fef3c7;color:#b45309;\">${priorityName}</span>` : ''}
                    <span class="activity-type">${typeName}</span>
                    ${bellBtn}
                </div>
                <div class="activity-summary">${task.summary || 'No summary'}</div>
                <div class="activity-meta">
                    <span class="activity-assignee">${assigneeName}</span>
                    <span>Start: ${startDate}</span>
                    <span>End: ${endDate}</span>
                </div>
            </div>
        `;
        tasksListElement.insertAdjacentHTML('beforeend', html);
    });
}

function getPriorityClass(priority) {
    switch(priority) {
        case 'highest': return 'priority-highest';
        case 'high': return 'priority-high';
        case 'medium': return 'priority-medium';
        case 'low': return 'priority-low';
        case 'lowest': return 'priority-lowest';
        default: return 'priority-medium';
    }
}

async function loadAllIssuesForCalendar() {
    if (!currentProject) return;
    try {
        const response = await fetch(`${API_BASE}/api/jira/issues/${currentProject}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const issuesData = await response.json();
        allIssuesData = issuesData.issues || [];
        console.log('Loaded issues for calendar:', allIssuesData); // Debug
        updateCalendarDisplay();
        updateDailyTasks();
        renderOverdueTasksCard(); // <-- render overdue card
    } catch (error) {
        console.error('Failed to load issues for calendar:', error);
    }
}

function setupIntersectionObserver() {
    const options = {
        root: null,
        rootMargin: '0px',
        threshold: 0.3
    };
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, options);
    const timeline = document.querySelector('.timeline-section');
    if (timeline) {
        observer.observe(timeline);
    }
}

// Sidebar active link highlight based on hash
function setActiveSidebarLink() {
    const hash = window.location.hash || '#dashboard';
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        const link = item.querySelector('a');
        if (link && link.getAttribute('href') === hash) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    // Show/hide sections
    document.querySelectorAll('#dashboard-sections > div').forEach(section => {
        if (hash === '#dashboard' && section.id === 'dashboard-section') {
            section.style.display = '';
        } else if (section.id === hash.replace('#','')) {
            section.style.display = '';
        } else {
            section.style.display = 'none';
        }
    });
    // NEW: Trigger live data update for each section
    if (hash === '#kanban') {
        if (typeof updateBoard === 'function') updateBoard();
    } else if (hash === '#timeline') {
        if (typeof updateRiskAwareTimeline === 'function') updateRiskAwareTimeline();
    } else if (hash === '#risk') {
        if (typeof loadRiskBoard === 'function') loadRiskBoard();
    }
}
window.addEventListener('hashchange', setActiveSidebarLink);
window.addEventListener('DOMContentLoaded', function() {
    setActiveSidebarLink();
    // Enable smooth scrolling
    document.documentElement.style.scrollBehavior = 'smooth';
});

function openSettingsModal() {
  document.getElementById('settingsModal').style.display = '';
}
function closeSettingsModal() {
  document.getElementById('settingsModal').style.display = 'none';
}
function showSettingsTab(tab) {
  document.querySelectorAll('.settings-tab').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.settings-tab-content').forEach(div => div.style.display = 'none');
  document.querySelector('.settings-tab[onclick*="' + tab + '"]').classList.add('active');
  document.getElementById('settingsTab' + tab.charAt(0).toUpperCase() + tab.slice(1)).style.display = '';
}
function saveSettings() {
  // Placeholder: Save settings to localStorage or backend
  closeSettingsModal();
  alert('Settings saved! (Demo)');
}
window.addEventListener('DOMContentLoaded', function() {
  var settingsBtn = document.querySelector('.sidebar-settings');
  if(settingsBtn) settingsBtn.onclick = openSettingsModal;
}); 