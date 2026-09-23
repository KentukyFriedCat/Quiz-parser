import requests
from bs4 import BeautifulSoup
import time
import html

BASE_URL = 'https://qarocks.ru/test_post/istqb-big-quiz/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
DELAY = 2
OUTPUT_HTML = 'istqb_report.html'

def parse_page(url):
    """
    Возвращает кортеж (список_вопросов_на_странице, ссылка_на_следующую_страницу)
    Каждый вопрос — словарь: {'question': текст, 'answers': [{'text': текст, 'is_correct': bool}, ...]}
    """
    print(f"📥 Загружаем страницу: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    question_blocks = soup.find_all('div', class_='quastion')
    if not question_blocks:
        print("⚠️ Блоки вопросов не найдены. Возможно, изменилась структура сайта.")
        return [], None

    page_questions = []

    for q_block in question_blocks:

        p_tag = q_block.find('p')
        question_text = p_tag.get_text(strip=True) if p_tag else q_block.get_text(strip=True)

        form = q_block.find_next_sibling('form', class_='quastion_form')
        if not form:
            print(f"⚠️ Не найдена форма для вопроса: {question_text[:50]}...")
            continue

        answer_blocks = form.find_all('div', class_='answer_block')
        answers_data = []

        for ans in answer_blocks:

            answer_text = ans.get_text(strip=True)


            label = ans.find_parent('label')
            is_correct = False
            if label:

                notice = label.find_next_sibling('div', class_='notice')
                if notice:
                    notice_title = notice.find('div', class_='notice_title')
                    if notice_title and 'Верно!' in notice_title.get_text():
                        is_correct = True

            answers_data.append({
                'text': answer_text,
                'is_correct': is_correct
            })

        page_questions.append({
            'question': question_text,
            'answers': answers_data
        })


    next_button = soup.find('div', class_='next_btn')
    next_url = None
    if next_button and 'disabled' not in next_button.get('class', []):
        link = next_button.find('a')
        if link and link.get('href'):
            next_url = requests.compat.urljoin(BASE_URL, link['href'])

    return page_questions, next_url


def generate_html_report(questions, filename):
    """
    Создаёт HTML-файл с таблицей вопросов и ответов.
    Правильные ответы выделены зелёным, неправильные — красным.
    """
    html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ISTQB - большой тест: вопросы и ответы</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 30px;
            background-color: #f8f9fa;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats {{
            text-align: center;
            margin: 20px 0;
            font-size: 1.2em;
            color: #27ae60;
        }}
        .question-card {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 25px;
            padding: 20px;
            border-left: 5px solid #3498db;
        }}
        .question-text {{
            font-weight: 600;
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .answers {{
            margin-left: 20px;
        }}
        .answer-row {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 6px;
            background-color: #f8f9fa;
            border-left: 4px solid transparent;
        }}
        .answer-row.correct {{
            background-color: #d4edda;
            border-left-color: #28a745;
        }}
        .answer-row.incorrect {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }}
        .answer-text {{
            flex: 1;
            font-size: 1.05em;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 15px;
            white-space: nowrap;
        }}
        .badge-correct {{
            background-color: #28a745;
            color: white;
        }}
        .badge-incorrect {{
            background-color: #dc3545;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>📋 ISTQB — большой тест: вопросы и ответы</h1>
    <div class="stats">Всего собрано вопросов: {total}</div>
    {content}
    <div class="footer">Сгенерировано автоматически. Дата: {date}</div>
</body>
</html>'''

    content_parts = []
    for idx, q in enumerate(questions, start=1):
        
        question_escaped = html.escape(q['question'])

        answers_html = ''
        for ans in q['answers']:
            answer_escaped = html.escape(ans['text'])
            correct_class = 'correct' if ans['is_correct'] else 'incorrect'
            badge_text = '✅ Верно' if ans['is_correct'] else '❌ Не верно'
            badge_class = 'badge-correct' if ans['is_correct'] else 'badge-incorrect'

            answers_html += f'''
                <div class="answer-row {correct_class}">
                    <span class="answer-text">{answer_escaped}</span>
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>'''

        card = f'''
    <div class="question-card">
        <div class="question-text">Вопрос {idx}: {question_escaped}</div>
        <div class="answers">
            {answers_html}
        </div>
    </div>'''
        content_parts.append(card)

    full_content = '\n'.join(content_parts)

    from datetime import datetime
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    html_output = html_template.format(total=len(questions), content=full_content, date=now)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"\n✅ HTML-отчёт сохранён: {filename}")

def main():
    all_questions = []
    current_url = BASE_URL
    page_num = 1

    while current_url:
        questions, next_url = parse_page(current_url)

        if questions is None:
            break
        if questions:
            print(f"   → Найдено вопросов на странице: {len(questions)}")
            all_questions.extend(questions)
        else:
            print("   → На странице нет вопросов (возможно, последняя страница).")

        current_url = next_url
        if current_url:
            print(f"⏩ Переход на страницу {page_num + 1}...\n")
            time.sleep(DELAY)
            page_num += 1
        else:
            print("\n🏁 Достигнут конец теста. Больше страниц нет.")

    if not all_questions:
        print("❌ Не удалось собрать ни одного вопроса.")
        return

    print(f"\n📊 Итого собрано вопросов: {len(all_questions)}")
    generate_html_report(all_questions, OUTPUT_HTML)


if __name__ == '__main__':
    main()
