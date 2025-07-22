Prepare for an exam or a job interview by creating a Google Sheet of flashcards

Example ```input.json```:

```json
{
    "linkedin_job_posting": {
        "url": "https://www.linkedin.com/jobs/view/fake-url",
        "headless": true,
        "filepath": "job_description.md"
    },
    "glassdoor_reviews": {
        "url": "https://www.glassdoor.com/Reviews/fake-url",
        "hide_window": true,
        "proxy": "https://41.110.10.205:8888",
        "filepath": "reviews.csv"
    },
    "glassdoor_interviews": {
        "url": "https://www.glassdoor.com/Interview/fake-url",
        "headless": true,
        "filepath": "interviews.csv"
    },
    "llm_config": {
        "model": "google/gemini-2.5-pro",
        "response_format": "response_format.json",
        "system_prompt": "system_prompt.md",
        "api_parameters": {
          "stream": false,
          "max_tokens": 4096,
          "temperature": 0.5,
          "presence_penalty": 0.0,
          "frequency_penalty": 0.0,
          "provider": {
            "require_parameters": false
          }
        }
    }
}
```