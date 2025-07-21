import subprocess
import sys
import os
import json

def get_input():
    with open('input.json', 'r') as f:
        return json.load(f)
    return None

def main():
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
            os.path.join(base_dir, 'submodules', 'glassdoor-scraper', 'interviews.py'),
            *( ['--headless'] if input['glassdoor_interviews']['headless'] else [] ),
            *( ['--url', input['glassdoor_interviews']['url']] if input['glassdoor_interviews']['url'] else [] )
        ],
        [
            os.path.join(base_dir, 'submodules', 'glassdoor-scraper', 'reviews.py'),
            *( ['--hide-window'] if input['glassdoor_reviews']['hide_window'] else [] ),
            *( ['--url', input['glassdoor_reviews']['url']] if input['glassdoor_reviews']['url'] else [] )
        ],
        [
            os.path.join(base_dir, 'submodules', 'linkedin-api', 'job_posting.py'),
            *( ['--headless'] if input['linkedin_job_posting']['headless'] else [] ),
            *( ['--url', input['linkedin_job_posting']['url']] if input['linkedin_job_posting']['url'] else [] )
        ]
    ]
    
    for script in scripts:
        print(f'Running {script[0]}...')
        result = subprocess.run([sys.executable, *script], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

if __name__ == "__main__":
    main()