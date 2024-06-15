# coding: utf8

"""
Single Responsibility Principle 예시 - 위키 글 작성 Project

이제부터 당신은 위키피디아 글을 openai api를 이용하여 작성하는 프로젝트를 진행하려고 한다. 이 때, 아래와 같이 있는 코드를 Single Responsibility 원칙에 맞게 수정해 봅시다. 이 수정이 끝나고 나면, 다음과 같은 수정사항들을 용이하게 대처할 수 있게 되어야 합니다.

1. 전체 코드 구조 설명

- main.py

write_article 함수를 실행시키는 것이 가장 중요한 기능입니다. write_article

- config.py
- prompts.py

config와 prompt들이 들어있는 파일입니다. 크게 중요하지 않으므로 설명은 생략합니다.

2. 개선해야 할 문제들

2.1 기능 추가

현재 clear_text 함수에서는 chatgpt의 output 형식인 Markdown 형식을 미디어위키 문법에 맞춰서 바꾸는 기능만 수행합니다. (pypandoc.convert_text() 함수). 그런데, 실질적으로 chatgpt의 output 형식을 넣어보면 지금 함수로는 문제가 생기기 때문에 이를 수정하는 기능을 추가하여야 합니다. clear_text 함수의 주석을 참고해서, clear_text 함수의 기능을 수정해 보세요.

2.2 구조 개선

현재 글을 생성할 때, 글의 구조는 다음과 같습니다.

Intro 대단원
|- cost 단원
|- customer 단원

여기서 단원의 추가, 혹은 기존 단원을 subsection등으로 내리거나 단원으로 올리는 등의 작업을 하고자 합니다. 이 작업이 용이하게 이뤄질 수 있도록 코드를 수정해보세요. 이 때 ask 함수는 수정하지 마세요. (openai assistant call logic을 담고 있는 함수이기에 수정 불필요)

추가로, 생성시에 다양한 오류들이 있을 수 있는데, 이에 대한 logging 및 지출한 token count에 대한 logging은 어떤 구조로 하면 좋을지 제안해보세요. logging하고자 하는 데이터들 역시 바뀔 수 있습니다. (Optional Question)

Appendix. Suggested Reading

* 트리 데이터구조와 그 Traversal: 앞 부분 수업자료 참고
* 미디어위키 문법 기초 : https://www.mediawiki.org/wiki/Help:Formatting/ko 및 관련 문서들 참고
* openai assistant 구조의 개요: https://platform.openai.com/docs/assistants/overview 및 assistant 하위 문서들 참고
"""
import pypandoc
import re

from openai import OpenAI
from string import Template

import config
import prompts

# Do not change this function
# 부를 때마다 돈 나가므로 조심해서 부를 것
def ask(thread, prompt, ticker):
    thread_message = client.beta.threads.messages.create(
        thread.id,
        role = 'user',
        content = prompt.substitute(ticker = ticker)
    )

    assistant = client.beta.assistants.create(
        name = f'{ticker} helper - gpt 3.5',
        instructions = '',
        model = 'gpt-3.5-turbo-0125',
        tools=[{"type": "file_search"}],
    )


    def find_file(ticker):
        file_list = list(client.files.list())

        for file in file_list:
            if file.filename.split('-')[0] == ticker.lower():
                return file

    file = find_file(ticker)
    ticker_vs = client.beta.vector_stores.create(name = f'{ticker} helper', file_ids = [file.id])

    assistant = client.beta.assistants.update(
        assistant_id = assistant.id,
        tool_resources = {"file_search": {"vector_store_ids": [ticker_vs.id]}},
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id = thread.id, assistant_id = assistant.id
    )

    messages = list(client.beta.threads.messages.list(thread_id = thread.id, run_id = run.id))

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            # citations.append(f"[{index}] {cited_file.filename}")
            citations.append((index, cited_file.filename))

    # clear meassage contents
    return message_content.value

def clear_text(msg):
    """chatgpt output 형식을 미디어위키 형식으로 바꾸고, 문서 양식에 맞게 전처리하는 함수.

    처리하는 휴리스틱에 제한은 없으나, 다음과

    - chatgpt output들의 경우 단원명 앞에 숫자가 붙어있는 경우가 꽤 있음. 이런 경우, 숫자가 없는 것이 더 보기에 좋음. 따라서 단원명 앞에 있는 숫자를 일괄적으로 정규표현식을 사용하여 삭제할 것. (2.1 기능 추가 문제)

    - chatgpt에서 맨 처음에 생성하면, 무조건 top level Markdown으로 생성됨. 그런데, 쓰고자 하는 문서에서는 그렇게 하면 꼬일 수 있음. 따라서 이 부분을 수정할 필요가 있음. (2.2 구조 개선과 결부된 문제)

    예) chatgpt 생성문이 '''단원명'''인 경우, 이를 Markdown으로 바꾸면 최상위 단원이 되는데 (1. 단원명 같이), 애초에 글을 넣고자 하는 곳이 만약 subsubsection이라면 (1.1.2 에 글을 넣고자 함), 글 내용 중에 갑자기 상위 단원이 생기는 불상사가 생김. 이를 방지해야 함.

    - 이외에도 자유롭게 처리해볼 것. (Optional)

    Args:
        msg: chatgpt의 output 텍스트
    Returns:
        str: 미디어위키 형식으로 맞춤 및 휴리스틱에 기반한 수정들이 들어간 함수.
    """
    msg = pypandoc.convert_text(msg, to = 'mediawiki', format = 'md')

    return msg

def write_article(client, ticker):
    """글을 실제로 생성하는 함수.

    ticker 회사에 대한 설명을 생성하는 함수. 현재 prompting 등이 적절하지 않아 크게 좋은 글을 얻기는 어려우나, 자유롭게 prompt를 수정하여 다양한 시도를 해 보는 것을 권장함. (optional)

    Args:
        client: OpenAI object
        ticker: 미국 상장사 고유 id
    Returns:
        str: 미디어위키 형식의 text를 리턴
    """
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.list(thread.id)

    intro = ask(
        thread,
        prompts.intro_prompt,
        ticker = ticker
    )

    cost = ask(
        thread,
        prompts.cost_prompt,
        ticker = ticker
    )

    customer = ask(
        thread,
        prompts.customer_analysis_prompt,
        ticker = ticker
    )

    intro = clear_text(intro)
    cost = clear_text(cost)
    customer = clear_text(customer)

    print(intro)
    text = Template('''
== Intro ==

$intro

=== Cost ===

$cost

=== Customer ===

$customer

    ''').substitute(intro = intro, cost = cost, customer = customer)


    with open(f'wiki_base.txt', 'w+', encoding = 'utf-8') as f:
        f.write(text)

    print(text)

if __name__ == '__main__':
    client = OpenAI(api_key = config.openai_api_key)

    ticker = 'ghld'
    write_article(client, ticker)