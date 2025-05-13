# The FIST System

## Introdcution

The F.I.S.T. stands for "fast, intuitive and sensitive test", which is the philosophy the community deal with the content supervision. The system is responsible for automatically and randomly check all the content within certain domain area.

## Basic Logic

The system stretch a piece of each thread(provided) and use AI tools to determine whether it uses suitable language to express the idea.

- To minimize the AI token usage, the input will be in structured JSON format, so does the return.

- To maximize the productivity and protect the privacy of content creators, only input the pieced content.

- To reduce the bandwith usage of the website, it will check each content only when it's changed once.

## Procedure

1. Scrape the content from the website.

2. Randomly select a percentage of the content:
    - 80% if the content is shorter than 500 words.
    - 60% if the content is 500-1000 words.
    - 40% if the content is 1000-3000 words.
    - 20% if the content is longer than 3000 words.

3. Send the content to the AI model with structured JSON format.
    - Return True if the content is appropriate.
    - Return False if the content is inappropriate.
    - Include confidence score and reasoning when available.

4. Process the result:
    - If True, do nothing.
    - If False, trigger the visibility restriction and warning.
    - Log the decision for audit purposes.

## AI prompt

Input:
```json
{
  "content": "text_to_check",
  "tos": "relevant_tos_rules"
}
```

Output:
```json
{
  "appropriate": true|false,
  "confidence": 0.0-1.0,
  "reason": "brief_explanation"
}
```

## Actions

1. Restrict visibility of inappropriate content.
2. Send detailed warning to the content creator and admin.
3. Provide appeal mechanism for content creators.
4. Track false positive/negative rates to improve system accuracy.
5. Manually review flagged content within 48 hours.

## FIST Term of Service

1. We will never send sensitive data to any other third-party without acquired permission. No exception so far.

2. Only content will come into the system for AI checking. No user information will be involved.

3. The system will only be used for content supervision. No other purpose will be allowed.

4. The content supervision follows the TOS of the website/provided by website admin.

5. We only support the region(server physical address or legislation) where FIST is safe to use.

6. Users have the right to appeal any content flagged as inappropriate by the system.

7. We maintain logs of all content checks for a limited period(30d currently, will be determined) for audit purposes only.

8. The system may be updated periodically to improve accuracy and compliance with regulations.
