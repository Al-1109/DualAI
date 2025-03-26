#!/usr/bin/env python3
import os
import re
from datetime import datetime
from typing import List, Dict
import requests
from github import Github

def get_github_stats(token: str) -> Dict:
    """Получение статистики с GitHub."""
    g = Github(token)
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    
    issues = repo.get_issues(state='all')
    pulls = repo.get_pulls(state='all')
    
    return {
        'total_issues': issues.totalCount,
        'open_issues': sum(1 for i in issues if i.state == 'open'),
        'closed_issues': sum(1 for i in issues if i.state == 'closed'),
        'total_pulls': pulls.totalCount,
        'open_pulls': sum(1 for p in pulls if p.state == 'open'),
        'merged_pulls': sum(1 for p in pulls if p.state == 'merged'),
    }

def update_project_status(stats: Dict) -> None:
    """Обновление файла PROJECT_STATUS.md."""
    status_file = 'PROJECT_STATUS.md'
    
    with open(status_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновление статистики
    stats_section = f"""
## Статистика проекта (Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
- Всего Issues: {stats['total_issues']}
- Открытых Issues: {stats['open_issues']}
- Закрытых Issues: {stats['closed_issues']}
- Всего Pull Requests: {stats['total_pulls']}
- Открытых PR: {stats['open_pulls']}
- Принятых PR: {stats['merged_pulls']}
"""
    
    # Замена или добавление секции статистики
    if '## Статистика проекта' in content:
        content = re.sub(r'## Статистика проекта.*?(?=\n##|\Z)', stats_section, content, flags=re.DOTALL)
    else:
        content += stats_section
    
    with open(status_file, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Основная функция."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN не установлен")
    
    stats = get_github_stats(token)
    update_project_status(stats)

if __name__ == '__main__':
    main() 