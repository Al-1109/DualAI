# Система управления задачами DualAI

## Структура Issues

### Типы Issues
1. **Feature** - новая функциональность
2. **Bug** - исправление ошибок
3. **Documentation** - документация
4. **Enhancement** - улучшение существующего функционала
5. **Task** - технические задачи

### Формат Issues
```markdown
## Описание
[Подробное описание задачи]

## Требования
- [ ] Требование 1
- [ ] Требование 2

## Связанные компоненты
- [ ] Компонент 1
- [ ] Компонент 2

## Технические детали
- Файлы для изменения:
  - `path/to/file1.py`
  - `path/to/file2.py`

## Критерии приемки
- [ ] Критерий 1
- [ ] Критерий 2

## Связанные Issues
- #issue_number
```

## Kanban Board

### Колонки
1. **Backlog** - задачи для планирования
2. **To Do** - задачи к выполнению
3. **In Progress** - задачи в работе
4. **Review** - задачи на проверке
5. **Done** - завершенные задачи

### Правила перемещения
- Из Backlog в To Do: задача готова к выполнению
- Из To Do в In Progress: разработчик начал работу
- Из In Progress в Review: код готов к проверке
- Из Review в Done: код проверен и принят

## GitHub Actions

### Основные workflows
1. **CI Pipeline**
   ```yaml
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
         - name: Install dependencies
           run: pip install -r requirements.txt
         - name: Run tests
           run: pytest
   ```

2. **Deployment Pipeline**
   ```yaml
   name: Deploy
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Deploy to server
           run: |
             # Команды деплоя
   ```

## Процесс создания задачи

1. **Создание Issue**
   - Использовать шаблон Issue
   - Добавить соответствующие метки
   - Указать связанные компоненты

2. **Добавление в Kanban**
   - Переместить Issue в колонку Backlog
   - Назначить исполнителя
   - Установить приоритет

3. **Создание ветки**
   - Название: `feature/issue-number-description`
   - Создать от main
   - Связать с Issue

4. **Разработка**
   - Следовать гайдлайнам кодирования
   - Регулярно коммитить изменения
   - Обновлять статус в Kanban

5. **Проверка**
   - Создать Pull Request
   - Пройти код-ревью
   - Обновить статус Issue

## Автоматизация

### GitHub Actions
- Автоматическое создание веток при создании Issue
- Автоматическое обновление статуса в Kanban
- Автоматическое закрытие Issue при мерже PR
- Автоматическое создание релизов

### Скрипты
- Скрипт для создания Issue из шаблона
- Скрипт для обновления статуса в PROJECT_STATUS.md
- Скрипт для генерации changelog

## Метрики и отчетность

### Еженедельные отчеты
- Количество созданных Issues
- Количество закрытых Issues
- Среднее время решения задач
- Статус проекта

### Метрики качества
- Количество багов
- Время на код-ревью
- Процент успешных деплоев
- Покрытие тестами 