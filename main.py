import subprocess
import sys
import os
import json
import pandas as pd

def get_input():
    with open('input.json', 'r') as f:
        return json.load(f)
    return None

def generate_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input = get_input()
    if input is None:
        print("No input found")
        return
    
    if set(input.keys()) != {'linkedin_job_posting', 'glassdoor_reviews', 'glassdoor_interviews'}:
        print("Invalid input")
        return
    
    scripts = [
        [
            os.path.join(base_dir, 'submodules', 'glassdoor-scraper', 'reviews.py'),
            *( ['--hide-window'] if input['glassdoor_reviews']['hide_window'] else [] ),
            *( ['--proxy', input['glassdoor_reviews']['proxy']] if input['glassdoor_reviews']['proxy'] else [] ),
            *( ['--url', input['glassdoor_reviews']['url']] if input['glassdoor_reviews']['url'] else [] ),
            *( ['--filepath', input['glassdoor_reviews']['filepath']] if input['glassdoor_reviews']['filepath'] else [] )
        ],
        [
            os.path.join(base_dir, 'submodules', 'glassdoor-scraper', 'interviews.py'),
            *( ['--headless'] if input['glassdoor_interviews']['headless'] else [] ),
            *( ['--url', input['glassdoor_interviews']['url']] if input['glassdoor_interviews']['url'] else [] ),
            *( ['--filepath', input['glassdoor_interviews']['filepath']] if input['glassdoor_interviews']['filepath'] else [] )
        ],
        [
            os.path.join(base_dir, 'submodules', 'linkedin-api', 'job_posting.py'),
            *( ['--headless'] if input['linkedin_job_posting']['headless'] else [] ),
            *( ['--url', input['linkedin_job_posting']['url']] if input['linkedin_job_posting']['url'] else [] ),
            *( ['--filepath', input['linkedin_job_posting']['filepath']] if input['linkedin_job_posting']['filepath'] else [] )
        ]
    ]
    
    for script in scripts:
        print(f'Running {script[0]}...')
        result = subprocess.run([sys.executable, *script])
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

def get_data_in_memory():
    input = get_input()
    with open(input['linkedin_job_posting']['filepath'], 'r') as f:
        linkedin_text = f.read()  
    with open(input['llm_config']['system_prompt'], 'r') as f:
        system_prompt = f.read()
    with open(input['llm_config']['response_format'], 'r') as f:
        response_format = json.load(f)
    llm_config = input['llm_config']
    glassdoor_reviews_df = pd.read_csv(input['glassdoor_reviews']['filepath'])
    glassdoor_interviews_df = pd.read_csv(input['glassdoor_interviews']['filepath'])
    return {
        'linkedin_text': linkedin_text,
        'system_prompt': system_prompt,
        'response_format': response_format,
        'glassdoor_reviews_df': glassdoor_reviews_df,
        'glassdoor_interviews_df': glassdoor_interviews_df,
        'llm_config': llm_config,
        'tags': input['tags']
    }

def preprocess_interview_questions(dataFrame: pd.DataFrame, tags: list):
    relevant_words = tags
    interviews_filtered = dataFrame
    interviews_filtered = interviews_filtered[interviews_filtered['interview_position'].str.contains('|'.join(relevant_words), case=False)]
    interviews_filtered = interviews_filtered[['interview_questions']]
    chunk_size = 10
    messages = [{"role": "user", "content": data['linkedin_text']}]
    for i in range(0, len(interviews_filtered), chunk_size):
        # Each row in 'interview_questions' is a list of strings; join them into a single string per row
        chunk_df = interviews_filtered.copy()
        chunk_df['interview_questions'] = chunk_df['interview_questions'].apply(
            lambda x: ', '.join(eval(x)) if isinstance(x, str) and x.startswith('[') else str(x)
        )
     
        chunk_df = chunk_df.iloc[i:i+chunk_size]
        chunk_text = ' '.join(chunk_df['interview_questions'].astype(str))
        messages.append({"role": "user", "content": chunk_text})
    return messages


def chunk_input_data(data):	
    max_tokens = data['llm_config']['api_parameters']['max_tokens']
    max_characters = max_tokens * 4 # assuming one token is 4 characters
    sum_tokens = 0
    for key, value in data.items():
        if key in ['llm_config', 'response_format']:
            continue
        if isinstance(value, pd.DataFrame):
            value = value.to_markdown()
        print(f'{key}: {len(value)} characters, {len(value)/max_characters*100}% of max allowed {max_characters} characters')
        print(f'{key}: {len(value)/4} tokens, {len(value)/4/max_tokens*100}% of max allowed {max_tokens} tokens')
        sum_tokens += len(value)/4
    print(f'Total tokens: {sum_tokens}')
    print(f'Total tokens: {sum_tokens/max_tokens*100}% of max allowed {max_tokens} tokens')
    if sum_tokens > max_tokens:
        print(f'Total tokens is greater than max allowed {max_tokens} tokens')
        return None
    return data


def generate_flashcards():
    from submodules.openrouter_api.api import API
    api = API()
    data = get_data_in_memory()
    data = chunk_input_data(data)
    if data is None:
        return
    response = api.safe_completion(messages=[
        {"role": "system", "content": data['system_prompt']}, 
    ], response_format=data['response_format'], model=data['llm_config']['model'], **data['llm_config']['api_parameters'])
    return response.json()

def interview_questions_stats(dataFrame: pd.DataFrame):
    import pandas as pd

    df = dataFrame
    num_rows = len(df)
    if num_rows == 0:
        avg_length_chars = 0
        avg_length_tokens = 0
    else:
        questions = df['interview_questions'].astype(str)
        total_chars = questions.str.len().sum()
        total_tokens = (questions.str.len() // 4).sum()
        avg_length_chars = total_chars / num_rows
        avg_length_tokens = total_tokens / num_rows

    print(f'Number of interview questions: {num_rows}')
    print(f'Average length of interview questions: {avg_length_chars} characters, {avg_length_tokens} tokens')

    return dataFrame
if __name__ == "__main__":
    data = get_data_in_memory()
    chunk_input_data(data)
    interview_questions_stats(data['glassdoor_interviews_df'])
    messages = preprocess_interview_questions(data['glassdoor_interviews_df'], data['tags'])
