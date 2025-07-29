#!/usr/bin/env python3
"""
Migrate tasks from tasks.yml to GitHub issues efficiently.

This script reads tasks from tasks.yml and creates corresponding GitHub issues
using the gh CLI tool, with proper labels, formatting, and metadata.
"""

import yaml
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_tasks(tasks_file: Path) -> List[Dict[str, Any]]:
    """Load tasks from YAML file."""
    with open(tasks_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_status_label(status: str) -> str:
    """Map task status to GitHub label."""
    status_map = {
        'done': 'status:completed',
        'in-progress': 'status:in-progress', 
        'pending': 'status:todo'
    }
    return status_map.get(status, 'status:todo')


def get_priority_label(priority: int) -> str:
    """Map priority number to GitHub label."""
    priority_map = {
        1: 'priority:critical',
        2: 'priority:high',
        3: 'priority:medium',
        4: 'priority:low',
        5: 'priority:low'
    }
    return priority_map.get(priority, 'priority:medium')


def get_component_label(component: str) -> str:
    """Map component to GitHub label."""
    if not component:
        return 'component:general'
    return f"component:{component.lower().replace(' ', '-')}"


def get_area_label(area: str) -> str:
    """Map area to GitHub label."""
    if not area:
        return None
    return f"area:{area.lower().replace(' ', '-')}"


def format_issue_body(task: Dict[str, Any]) -> str:
    """Format task data into GitHub issue body."""
    body_parts = [task.get('description', '')]
    
    # Add task metadata
    if task.get('task_id'):
        body_parts.append(f"**Task ID:** `{task['task_id']}`")
    
    if task.get('component'):
        body_parts.append(f"**Component:** {task['component']}")
    
    if task.get('epic'):
        body_parts.append(f"**Epic:** {task['epic']}")
    
    # Add actionable steps
    if task.get('actionable_steps'):
        body_parts.append("## Actionable Steps")
        for step in task['actionable_steps']:
            body_parts.append(f"- {step}")
    
    # Add acceptance criteria
    if task.get('acceptance_criteria'):
        body_parts.append("## Acceptance Criteria")
        for criteria in task['acceptance_criteria']:
            body_parts.append(f"- [ ] {criteria}")
    
    # Add execution details
    if task.get('command'):
        body_parts.append(f"## Command")
        body_parts.append(f"```bash\n{task['command']}\n```")
    
    # Add CI notes
    if task.get('ci_notes'):
        body_parts.append(f"## CI Notes")
        body_parts.append(task['ci_notes'])
    
    # Add dependencies
    if task.get('dependencies'):
        deps = task['dependencies']
        if deps:
            body_parts.append(f"## Dependencies")
            body_parts.append(f"Depends on tasks: {', '.join(map(str, deps))}")
    
    return '\n\n'.join(body_parts)


def create_labels_if_needed(labels: List[str]) -> None:
    """Create GitHub labels if they don't exist."""
    existing_labels = set()
    
    try:
        result = subprocess.run(['gh', 'label', 'list', '--json', 'name'], 
                              capture_output=True, text=True, check=True)
        label_data = json.loads(result.stdout)
        existing_labels = {label['name'] for label in label_data}
    except subprocess.CalledProcessError:
        print("Warning: Could not fetch existing labels")
    
    # Define label colors
    label_colors = {
        'status:todo': '0052cc',
        'status:in-progress': 'fbca04', 
        'status:completed': '0e8a16',
        'priority:critical': 'd73a49',
        'priority:high': 'f85149',
        'priority:medium': 'f9c513',
        'priority:low': '7dd3fc',
        'component:scraper': 'bfd4f2',
        'component:enricher': 'c2e0c6',
        'component:trustforge': 'ffd8cc',
        'component:cli': 'f1f8ff',
        'component:testing': 'e1f5fe',
        'component:docs': 'fff2cc',
        'area:data-ingestion': 'd4edda',
        'area:semantic-enrichment': 'cce5df',
        'area:quality-assurance': 'f8d7da'
    }
    
    for label in labels:
        if label not in existing_labels:
            color = label_colors.get(label, 'ededed')
            try:
                subprocess.run(['gh', 'label', 'create', label, '--color', color], 
                             check=True, capture_output=True)
                print(f"Created label: {label}")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not create label {label}: {e}")


def check_existing_issue(task: Dict[str, Any]) -> Optional[str]:
    """Check if an issue already exists for this task."""
    title = task.get('title', f"Task {task.get('id', 'Unknown')}")
    task_id = task.get('task_id', '')
    
    try:
        # Search for issues with the same title
        result = subprocess.run(['gh', 'issue', 'list', '--search', f'"{title}" in:title', '--json', 'title,url'], 
                              capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)
        
        for issue in issues:
            if issue['title'] == title:
                return issue['url']
        
        # Also check by task_id if it exists
        if task_id:
            result = subprocess.run(['gh', 'issue', 'list', '--search', f'"{task_id}"', '--json', 'body,url'], 
                                  capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            
            for issue in issues:
                if task_id in issue.get('body', ''):
                    return issue['url']
        
        return None
        
    except subprocess.CalledProcessError:
        # If search fails, assume no duplicates
        return None


def create_github_issue(task: Dict[str, Any], dry_run: bool = False, force: bool = False) -> Optional[str]:
    """Create a GitHub issue from a task."""
    title = task.get('title', f"Task {task.get('id', 'Unknown')}")
    
    # Check for existing issues unless forced
    if not force:
        existing_url = check_existing_issue(task)
        if existing_url:
            if dry_run:
                print(f"Issue already exists: {title} -> {existing_url}")
            else:
                print(f"Skipping duplicate: {title} -> {existing_url}")
            return existing_url
    
    body = format_issue_body(task)
    
    # Build labels
    labels = []
    
    # Status label
    if task.get('status'):
        labels.append(get_status_label(task['status']))
    
    # Priority label
    if task.get('priority'):
        labels.append(get_priority_label(task['priority']))
    
    # Component label
    if task.get('component'):
        labels.append(get_component_label(task['component']))
    
    # Area label
    if task.get('area'):
        area_label = get_area_label(task['area'])
        if area_label:
            labels.append(area_label)
    
    # Epic label
    if task.get('epic'):
        labels.append(f"epic:{task['epic'].lower().replace(' ', '-')}")
    
    if dry_run:
        print(f"Would create issue: {title}")
        print(f"Labels: {', '.join(labels)}")
        print(f"Body preview: {body[:100]}...")
        print("---")
        return None
    
    try:
        # Create labels if needed
        create_labels_if_needed(labels)
        
        # Create the issue
        cmd = ['gh', 'issue', 'create', '--title', title, '--body', body]
        
        if labels:
            cmd.extend(['--label', ','.join(labels)])
        
        # Create the issue (don't auto-close done tasks - leave open for review)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        
        if task.get('status') == 'done':
            print(f"Created completed issue (open for review): {title} -> {issue_url}")
        else:
            print(f"Created issue: {title} -> {issue_url}")
        
        return issue_url
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating issue '{title}': {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate tasks.yml to GitHub issues")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be created without actually creating issues')
    parser.add_argument('--tasks-file', default='tasks.yml',
                       help='Path to tasks.yml file (default: tasks.yml)')
    parser.add_argument('--filter-status', choices=['done', 'in-progress', 'pending'],
                       help='Only migrate tasks with this status')
    parser.add_argument('--filter-priority', type=int, choices=[1, 2, 3, 4, 5],
                       help='Only migrate tasks with this priority')
    parser.add_argument('--force', action='store_true',
                       help='Create issues even if duplicates exist')
    
    args = parser.parse_args()
    
    tasks_file = Path(args.tasks_file)
    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found")
        sys.exit(1)
    
    # Check if gh CLI is available
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) is not installed or not in PATH")
        print("Install it from: https://cli.github.com/")
        sys.exit(1)
    
    # Load tasks
    print(f"Loading tasks from {tasks_file}")
    tasks = load_tasks(tasks_file)
    
    # Apply filters
    if args.filter_status:
        tasks = [t for t in tasks if t.get('status') == args.filter_status]
        print(f"Filtered to {len(tasks)} tasks with status '{args.filter_status}'")
    
    if args.filter_priority:
        tasks = [t for t in tasks if t.get('priority') == args.filter_priority]
        print(f"Filtered to {len(tasks)} tasks with priority {args.filter_priority}")
    
    if args.dry_run:
        print(f"\n=== DRY RUN: Would create {len(tasks)} issues ===")
    else:
        print(f"\n=== Creating {len(tasks)} GitHub issues ===")
    
    created_count = 0
    for task in tasks:
        result = create_github_issue(task, dry_run=args.dry_run, force=args.force)
        if result or args.dry_run:
            created_count += 1
    
    if args.dry_run:
        print(f"\nDry run complete. Would create {created_count} issues.")
        print("Run without --dry-run to actually create the issues.")
    else:
        print(f"\nMigration complete! Created {created_count} issues.")


if __name__ == '__main__':
    main()