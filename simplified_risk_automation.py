# simplified_risk_automation.py
# Add this as a new file in your project

import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class SimpleAutomatedRiskCalculator:
    """
    Simplified automated risk calculations using rule-based logic
    No heavy dependencies required - works with your existing setup
    """
    
    def __init__(self):
        self.risk_keywords = {
            'critical': ['critical', 'urgent', 'emergency', 'blocker', 'showstopper', 'asap'],
            'security': ['security', 'breach', 'vulnerability', 'hack', 'attack', 'ssl', 'auth'],
            'performance': ['performance', 'slow', 'timeout', 'scalability', 'capacity', 'memory'],
            'integration': ['api', 'integration', 'third-party', 'external', 'vendor', 'service'],
            'compliance': ['compliance', 'regulatory', 'legal', 'gdpr', 'audit', 'policy'],
            'financial': ['budget', 'cost', 'expensive', 'revenue', 'financial', 'billing']
        }
        
        self.priority_weights = {
            'Critical': 4,
            'Highest': 4,
            'High': 3, 
            'Medium': 2,
            'Low': 1,
            'Lowest': 1
        }
    
    def calculate_say_do_ratio(self, issues_data):
        """Calculate Say-Do ratio using simple rules"""
        if not issues_data:
            return {
                'say_do_ratio': 1.0,
                'reliability': 'Medium',
                'recommendation': 'No data available for analysis',
                'factors_analyzed': 0
            }
        
        total_ratio = 0
        count = 0
        
        for issue in issues_data:
            # Estimate complexity based on description length and keywords
            complexity_score = self._calculate_complexity(issue)
            priority_weight = self.priority_weights.get(issue.get('priority'), 2)
            
            # Simple rule-based Say-Do estimation
            base_ratio = 1.0
            
            # Adjust based on complexity
            if complexity_score > 100:
                base_ratio *= 1.25  # Very complex issues take 25% longer
            elif complexity_score > 50:
                base_ratio *= 1.15  # Medium complexity 15% longer
            elif complexity_score < 20:
                base_ratio *= 0.9   # Simple issues finish early
            
            # Adjust based on priority (urgent items often rushed, estimates off)
            if priority_weight >= 4:
                base_ratio *= 1.2   # Critical items often underestimated
            elif priority_weight >= 3:
                base_ratio *= 1.1   # High priority items take a bit longer
            
            # Adjust based on external dependencies
            if self._has_external_dependency(issue):
                base_ratio *= 1.3   # External deps add significant delays
            
            # Adjust based on issue type
            issue_type = issue.get('issuetype', 'Task').lower()
            if 'bug' in issue_type:
                base_ratio *= 1.15  # Bugs often take longer to fix
            elif 'epic' in issue_type or 'story' in issue_type:
                base_ratio *= 1.1   # Stories have scope creep
            
            total_ratio += base_ratio
            count += 1
        
        avg_ratio = total_ratio / count if count > 0 else 1.0
        
        return {
            'say_do_ratio': round(avg_ratio, 2),
            'reliability': self._get_reliability_category(avg_ratio),
            'recommendation': self._get_say_do_recommendation(avg_ratio),
            'factors_analyzed': count,
            'trend': self._analyze_say_do_trend(avg_ratio)
        }
    
    def calculate_idle_time(self, team_workload):
        """Calculate team idle time using workload analysis"""
        if not team_workload:
            return {
                'average_utilization': 0,
                'total_idle_hours': 0,
                'team_breakdown': {},
                'optimization_suggestions': ['No team data available']
            }
        
        team_utilization = {}
        
        for assignee, issues in team_workload.items():
            if assignee in ['Unassigned', '', None]:
                continue
                
            # Calculate workload score
            active_issues = [i for i in issues if self._is_active_issue(i)]
            
            workload_score = 0
            for issue in active_issues:
                complexity = self._calculate_complexity(issue)
                priority = self.priority_weights.get(issue.get('priority'), 2)
                
                # Calculate hours needed based on complexity and priority
                base_hours = (complexity / 20) + (priority * 0.5)
                workload_score += base_hours
            
            # Estimate utilization (8 hours = 100% utilization)
            estimated_hours_needed = min(workload_score, 12)  # Cap at 12 hours (150%)
            utilization_rate = (estimated_hours_needed / 8) * 100
            idle_hours = max(0, 8 - estimated_hours_needed)
            
            # Determine workload status
            workload_status = self._get_workload_status(utilization_rate)
            
            team_utilization[assignee] = {
                'utilization_rate': min(150, round(utilization_rate, 1)),  # Cap display at 150%
                'idle_hours': round(idle_hours, 1),
                'active_issues': len(active_issues),
                'workload_score': round(workload_score, 1),
                'workload_status': workload_status,
                'recommendations': self._get_individual_recommendations(utilization_rate, len(active_issues))
            }
        
        # Calculate team averages
        if team_utilization:
            avg_utilization = statistics.mean([u['utilization_rate'] for u in team_utilization.values()])
            total_idle = sum([u['idle_hours'] for u in team_utilization.values()])
        else:
            avg_utilization = 0
            total_idle = 0
        
        return {
            'average_utilization': round(avg_utilization, 1),
            'total_idle_hours': round(total_idle, 1),
            'team_breakdown': team_utilization,
            'optimization_suggestions': self._get_utilization_suggestions(avg_utilization, team_utilization),
            'balance_score': self._calculate_balance_score(team_utilization)
        }
    
    def calculate_risk_impact(self, risks_data):
        """Calculate risk impact using keyword analysis"""
        if not risks_data:
            return {
                'total_risk_score': 0,
                'average_risk_score': 0,
                'risk_distribution': {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0},
                'detailed_analysis': [],
                'automated_recommendations': ['No risks to analyze']
            }
        
        risk_scores = []
        risk_analysis = []
        
        for risk in risks_data:
            text = f"{risk.get('summary', '')} {risk.get('description', '')}".lower()
            
            # Calculate base impact score
            impact_score = 2  # Base score
            risk_factors = []
            confidence_factors = []
            
            # Analyze risk categories
            for category, keywords in self.risk_keywords.items():
                keyword_matches = [kw for kw in keywords if kw in text]
                if keyword_matches:
                    confidence_factors.extend(keyword_matches)
                    
                    if category == 'critical':
                        impact_score += 3
                        risk_factors.append('Critical Priority')
                    elif category == 'security':
                        impact_score += 2.5
                        risk_factors.append('Security Risk')
                    elif category == 'compliance':
                        impact_score += 2
                        risk_factors.append('Compliance Risk')
                    elif category == 'financial':
                        impact_score += 1.5
                        risk_factors.append('Financial Impact')
                    elif category == 'integration':
                        impact_score += 1.5
                        risk_factors.append('Integration Risk')
                    elif category == 'performance':
                        impact_score += 1
                        risk_factors.append('Performance Risk')
            
            # Check for external dependencies
            if self._has_external_dependency(risk):
                impact_score += 1.5
                risk_factors.append('External Dependency')
                confidence_factors.append('external dependency')
            
            # Priority adjustment
            priority = risk.get('priority', 'Medium')
            priority_weight = self.priority_weights.get(priority, 2)
            impact_score += (priority_weight - 2) * 0.8
            
            # Text length factor (longer descriptions often indicate complexity)
            text_length = len(text)
            if text_length > 200:
                impact_score += 0.5
            elif text_length < 50:
                impact_score -= 0.5
            
            # Determine impact level and confidence
            impact_level = self._get_impact_level(impact_score)
            confidence = self._calculate_confidence(confidence_factors, len(risk_factors))
            
            risk_analysis.append({
                'risk_id': risk.get('key', 'Unknown'),
                'impact_score': round(max(0, impact_score), 1),
                'impact_level': impact_level,
                'risk_factors': risk_factors,
                'automation_confidence': confidence,
                'priority': priority,
                'keyword_matches': len(confidence_factors)
            })
            
            risk_scores.append(max(0, impact_score))
        
        # Calculate overall metrics
        total_score = sum(risk_scores) if risk_scores else 0
        avg_score = statistics.mean(risk_scores) if risk_scores else 0
        
        # Risk distribution
        distribution = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for analysis in risk_analysis:
            distribution[analysis['impact_level']] += 1
        
        return {
            'total_risk_score': round(total_score, 1),
            'average_risk_score': round(avg_score, 1),
            'risk_distribution': distribution,
            'detailed_analysis': risk_analysis,
            'automated_recommendations': self._get_risk_recommendations(risk_analysis),
            'risk_trend': self._analyze_risk_trend(risk_analysis)
        }
    
    def calculate_project_health(self, say_do_data, utilization_data, risk_data, project_data):
        """Calculate overall project health score"""
        health_score = 100  # Start with perfect score
        impact_details = {}
        
        # Say-Do impact (30% weight)
        say_do_ratio = say_do_data.get('say_do_ratio', 1.0)
        say_do_penalty = 0
        if say_do_ratio < 0.7:
            say_do_penalty = 30
        elif say_do_ratio < 0.8:
            say_do_penalty = 20
        elif say_do_ratio < 0.9:
            say_do_penalty = 10
        elif say_do_ratio > 1.4:
            say_do_penalty = 25
        elif say_do_ratio > 1.3:
            say_do_penalty = 15
        elif say_do_ratio > 1.2:
            say_do_penalty = 8
        
        health_score -= say_do_penalty
        impact_details['say_do'] = {
            'penalty': say_do_penalty,
            'impact': self._assess_say_do_impact(say_do_ratio)
        }
        
        # Utilization impact (25% weight)
        avg_utilization = utilization_data.get('average_utilization', 80)
        utilization_penalty = 0
        if avg_utilization < 50:
            utilization_penalty = 25
        elif avg_utilization < 60:
            utilization_penalty = 15
        elif avg_utilization < 70:
            utilization_penalty = 8
        elif avg_utilization > 120:
            utilization_penalty = 20
        elif avg_utilization > 100:
            utilization_penalty = 10
        
        health_score -= utilization_penalty
        impact_details['utilization'] = {
            'penalty': utilization_penalty,
            'impact': self._assess_utilization_impact(avg_utilization)
        }
        
        # Risk impact (35% weight)
        avg_risk = risk_data.get('average_risk_score', 0)
        critical_risks = risk_data.get('risk_distribution', {}).get('Critical', 0)
        high_risks = risk_data.get('risk_distribution', {}).get('High', 0)
        
        risk_penalty = 0
        if critical_risks > 0:
            risk_penalty += critical_risks * 15
        if high_risks > 0:
            risk_penalty += high_risks * 8
        if avg_risk > 7:
            risk_penalty += 15
        elif avg_risk > 5:
            risk_penalty += 8
        elif avg_risk > 3:
            risk_penalty += 3
        
        health_score -= risk_penalty
        impact_details['risk'] = {
            'penalty': risk_penalty,
            'impact': self._assess_risk_impact(avg_risk)
        }
        
        # Progress impact (10% weight)
        progress = project_data.get('progress_percentage', 0)
        total_issues = project_data.get('status_counts', {}).get('total', 0)
        
        progress_penalty = 0
        if progress < 10 and total_issues > 20:
            progress_penalty = 15  # Many issues but very low progress
        elif progress < 25 and total_issues > 10:
            progress_penalty = 8   # Some issues but low progress
        
        health_score -= progress_penalty
        impact_details['progress'] = {
            'penalty': progress_penalty,
            'current_progress': progress
        }
        
        # Ensure score is within bounds
        health_score = max(0, min(100, health_score))
        
        return {
            'health_score': round(health_score),
            'health_category': self._get_health_category(health_score),
            'contributing_factors': {
                'say_do_impact': impact_details['say_do']['impact'],
                'utilization_impact': impact_details['utilization']['impact'],
                'risk_impact': impact_details['risk']['impact']
            },
            'impact_breakdown': impact_details,
            'improvement_recommendations': self._get_health_recommendations(health_score, say_do_data, utilization_data, risk_data),
            'automated_insights': self._generate_insights(health_score, say_do_data, utilization_data, risk_data, project_data)
        }
    
    # Helper methods
    def _calculate_complexity(self, issue):
        """Calculate issue complexity score based on multiple factors"""
        complexity = 0
        
        # Text length factor
        summary = issue.get('summary', '')
        description = issue.get('description', '')
        text_length = len(summary) + len(description)
        complexity += text_length / 15  # Base complexity from text length
        
        # Keyword-based complexity adjustment
        text = f"{summary} {description}".lower()
        
        complex_keywords = {
            'very_high': ['migration', 'refactor', 'architecture', 'redesign', 'overhaul'],
            'high': ['integration', 'complex', 'multiple', 'advanced', 'enterprise'],
            'medium': ['update', 'modify', 'enhance', 'improve', 'configure'],
            'low': ['fix', 'simple', 'quick', 'minor', 'small']
        }
        
        for level, keywords in complex_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if level == 'very_high':
                        complexity += 40
                    elif level == 'high':
                        complexity += 25
                    elif level == 'medium':
                        complexity += 10
                    elif level == 'low':
                        complexity -= 5
                    break  # Only count first match per level
        
        # Component complexity
        components = issue.get('components', [])
        if isinstance(components, list):
            complexity += len(components) * 8
        
        # Labels complexity
        labels = issue.get('labels', [])
        if isinstance(labels, list):
            complex_labels = ['backend', 'frontend', 'database', 'api', 'security']
            for label in labels:
                if any(cl in str(label).lower() for cl in complex_labels):
                    complexity += 5
        
        return max(10, min(complexity, 150))  # Bound between 10 and 150
    
    def _is_active_issue(self, issue):
        """Check if issue is active (not done/closed)"""
        status = issue.get('status', '').lower()
        inactive_statuses = ['done', 'closed', 'resolved', 'complete', 'finished']
        return not any(inactive in status for inactive in inactive_statuses)
    
    def _has_external_dependency(self, issue):
        """Check if issue has external dependencies"""
        text = f"{issue.get('summary', '')} {issue.get('description', '')}".lower()
        external_keywords = [
            'vendor', 'third-party', 'external', 'client', 'customer', 
            'partner', 'supplier', 'contractor', 'outsource', 'agency'
        ]
        return any(keyword in text for keyword in external_keywords)
    
    def _get_impact_level(self, score):
        """Convert numeric score to impact level"""
        if score >= 8:
            return 'Critical'
        elif score >= 5.5:
            return 'High'
        elif score >= 3:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_confidence(self, confidence_factors, risk_factor_count):
        """Calculate confidence level for risk assessment"""
        if len(confidence_factors) >= 3 and risk_factor_count >= 2:
            return 'High'
        elif len(confidence_factors) >= 1 and risk_factor_count >= 1:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_reliability_category(self, ratio):
        """Get reliability category for Say-Do ratio"""
        if 0.85 <= ratio <= 1.15:
            return 'High'
        elif 0.7 <= ratio <= 1.4:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_say_do_recommendation(self, ratio):
        """Get recommendation based on Say-Do ratio"""
        if ratio < 0.7:
            return "🚨 Significantly under-delivering: Urgent estimation review needed"
        elif ratio < 0.8:
            return "⚠️ Under-delivering: Improve estimation accuracy or reduce scope"
        elif ratio < 0.9:
            return "📊 Slightly under-delivering: Fine-tune estimation process"
        elif ratio <= 1.15:
            return "✅ Excellent balance between commitments and delivery"
        elif ratio <= 1.3:
            return "📈 Over-delivering: Consider taking on more challenging work"
        else:
            return "🎯 Significantly over-delivering: Review estimation process for under-commitment"
    
    def _analyze_say_do_trend(self, ratio):
        """Analyze Say-Do trend (simplified)"""
        if ratio < 0.8:
            return "Concerning - needs attention"
        elif ratio > 1.3:
            return "Potential under-estimation pattern"
        else:
            return "Stable"
    
    def _get_workload_status(self, utilization_rate):
        """Get workload status based on utilization rate"""
        if utilization_rate >= 120:
            return "Severely Overloaded"
        elif utilization_rate >= 100:
            return "Overloaded"
        elif utilization_rate >= 85:
            return "Fully Utilized"
        elif utilization_rate >= 70:
            return "Well Utilized"
        elif utilization_rate >= 50:
            return "Underutilized"
        else:
            return "Significantly Underutilized"
    
    def _get_individual_recommendations(self, utilization_rate, issue_count):
        """Get recommendations for individual team members"""
        if utilization_rate >= 120:
            return [f"🔥 Overloaded ({utilization_rate:.0f}%) - redistribute {issue_count-3} issues"]
        elif utilization_rate >= 100:
            return [f"⚠️ At capacity ({utilization_rate:.0f}%) - monitor closely"]
        elif utilization_rate < 50:
            return [f"📈 Underutilized ({utilization_rate:.0f}%) - can take {5-issue_count} more issues"]
        elif utilization_rate < 70:
            return [f"📊 Below optimal ({utilization_rate:.0f}%) - can take {2-issue_count} more issues"]
        else:
            return [f"✅ Good utilization ({utilization_rate:.0f}%)"]
    
    def _calculate_balance_score(self, team_utilization):
        """Calculate team balance score"""
        if not team_utilization:
            return 0
        
        utilization_rates = [member['utilization_rate'] for member in team_utilization.values()]
        if len(utilization_rates) < 2:
            return 100
        
        std_dev = statistics.stdev(utilization_rates)
        # Lower standard deviation = better balance
        balance_score = max(0, 100 - (std_dev * 2))
        return round(balance_score, 1)
    
    def _get_utilization_suggestions(self, avg_utilization, team_data):
        """Get team utilization suggestions"""
        suggestions = []
        
        if avg_utilization < 60:
            suggestions.append("📈 Team significantly underutilized - consider additional projects")
        elif avg_utilization < 70:
            suggestions.append("📊 Team has capacity for additional work")
        elif avg_utilization > 110:
            suggestions.append("🚨 Team severely overloaded - immediate redistribution needed")
        elif avg_utilization > 90:
            suggestions.append("⚠️ Team at high utilization - monitor for burnout")
        
        # Check for workload imbalance
        if team_data:
            utilization_rates = [member['utilization_rate'] for member in team_data.values()]
            if len(utilization_rates) > 1:
                max_util = max(utilization_rates)
                min_util = min(utilization_rates)
                if max_util - min_util > 40:
                    suggestions.append("⚖️ Significant workload imbalance - redistribute tasks")
        
        if not suggestions:
            suggestions.append("✅ Team utilization is well balanced and optimal")
        
        return suggestions
    
    def _get_risk_recommendations(self, risk_analysis):
        """Get automated risk recommendations"""
        recommendations = []
        
        # Count risks by level
        critical_risks = [r for r in risk_analysis if r['impact_level'] == 'Critical']
        high_risks = [r for r in risk_analysis if r['impact_level'] == 'High']
        
        if critical_risks:
            recommendations.append(f"🚨 {len(critical_risks)} critical risks need immediate escalation and mitigation")
        
        if high_risks:
            recommendations.append(f"⚠️ {len(high_risks)} high-impact risks require detailed mitigation plans within 48 hours")
        
        # Check for common risk patterns
        all_factors = []
        for risk in risk_analysis:
            all_factors.extend(risk['risk_factors'])
        
        factor_counts = defaultdict(int)
        for factor in all_factors:
            factor_counts[factor] += 1
        
        # Find factors that appear in multiple risks
        common_factors = [factor for factor, count in factor_counts.items() if count >= 2]
        if common_factors:
            top_factors = sorted(common_factors, key=lambda x: factor_counts[x], reverse=True)[:3]
            recommendations.append(f"🎯 Address recurring risk patterns: {', '.join(top_factors)}")
        
        # Check for external dependency concentration
        external_risks = [r for r in risk_analysis if 'External Dependency' in r['risk_factors']]
        if len(external_risks) >= 3:
            recommendations.append("🤝 High external dependency risk - diversify vendor relationships")
        
        # Security-specific recommendations
        security_risks = [r for r in risk_analysis if 'Security Risk' in r['risk_factors']]
        if security_risks:
            recommendations.append("🔒 Security risks detected - involve security team in review")
        
        if not recommendations:
            recommendations.append("✅ Risk levels are manageable with current processes")
        
        return recommendations
    
    def _analyze_risk_trend(self, risk_analysis):
        """Analyze risk trend (simplified)"""
        high_severity_count = len([r for r in risk_analysis if r['impact_level'] in ['Critical', 'High']])
        total_risks = len(risk_analysis)
        
        if total_risks == 0:
            return "No risks identified"
        
        high_severity_ratio = high_severity_count / total_risks
        
        if high_severity_ratio > 0.5:
            return "High severity concentration"
        elif high_severity_ratio > 0.3:
            return "Moderate risk levels"
        else:
            return "Manageable risk profile"
    
    def _get_health_category(self, score):
        """Get health category based on score"""
        if score >= 85:
            return 'Excellent'
        elif score >= 70:
            return 'Good'
        elif score >= 50:
            return 'Fair'
        elif score >= 30:
            return 'Poor'
        else:
            return 'Critical'
    
    def _assess_say_do_impact(self, ratio):
        """Assess Say-Do impact on health"""
        if 0.85 <= ratio <= 1.15:
            return 'Positive'
        elif 0.7 <= ratio <= 1.4:
            return 'Neutral'
        else:
            return 'Negative'
    
    def _assess_utilization_impact(self, utilization):
        """Assess utilization impact on health"""
        if 70 <= utilization <= 90:
            return 'Positive'
        elif 60 <= utilization <= 100:
            return 'Neutral'
        else:
            return 'Negative'
    
    def _assess_risk_impact(self, avg_risk):
        """Assess risk impact on health"""
        if avg_risk < 3:
            return 'Positive'
        elif avg_risk < 6:
            return 'Neutral'
        else:
            return 'Negative'
    
    def _get_health_recommendations(self, score, say_do, utilization, risk):
        """Get health improvement recommendations"""
        recommendations = []
        
        if score < 30:
            recommendations.append("🚨 Project in critical state - immediate intervention required")
        elif score < 50:
            recommendations.append("⚠️ Project needs attention - address key issues urgently")
        elif score < 70:
            recommendations.append("📊 Project has room for improvement")
        
        # Specific recommendations based on metrics
        say_do_ratio = say_do.get('say_do_ratio', 1.0)
        if say_do_ratio < 0.8:
            recommendations.append("📊 Focus on improving delivery predictability and estimation accuracy")
        elif say_do_ratio > 1.3:
            recommendations.append("🎯 Consider more ambitious goals or challenging work")
        
        avg_utilization = utilization.get('average_utilization', 80)
        if avg_utilization < 70:
            recommendations.append("⚡ Optimize resource allocation and increase team utilization")
        elif avg_utilization > 100:
            recommendations.append("👥 Team overloaded - redistribute work or add resources")
        
        avg_risk = risk.get('average_risk_score', 0)
        if avg_risk > 6:
            recommendations.append("🛡️ Prioritize immediate risk mitigation activities")
        elif avg_risk > 3:
            recommendations.append("🔍 Develop proactive risk management strategies")
        
        if not recommendations:
            recommendations.append("✅ Maintain current practices - project health is good")
        
        return recommendations
    
    def _generate_insights(self, health_score, say_do, utilization, risk, project):
        """Generate automated insights"""
        insights = []
        
        # Performance insights
        if say_do.get('say_do_ratio', 1.0) > 1.2 and utilization.get('average_utilization', 0) < 80:
            insights.append("💡 Team over-delivering with spare capacity - good opportunity for stretch goals")
        
        # Risk insights
        critical_risks = risk.get('risk_distribution', {}).get('Critical', 0)
        if critical_risks > 0 and health_score > 70:
            insights.append("⚖️ Despite critical risks, project health remains stable - good risk management")
        
        # Utilization insights
        balance_score = utilization.get('balance_score', 0)
        if balance_score > 90:
            insights.append("👥 Excellent team workload balance - effective resource management")
        elif balance_score < 60:
            insights.append("⚖️ Workload imbalance detected - some team members may need support")
        
        # Progress insights
        progress = project.get('progress_percentage', 0)
        if progress > 75 and health_score > 80:
            insights.append("🎯 Project approaching completion with strong health metrics")
        
        return insights 