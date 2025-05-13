# The FIST System

## Introdcution

The F.I.S.T. stands for "fast, intuitive and sensitive test", which is the philosophy the community deal with the content supervision. The system is responsible for automatically and randomly check all the content within certain domain area.

## Basic Logic

The system stretch a piece of each thread(provided) and use AI tools to determine whether it uses suitable language to express the idea.

- To minimize the AI token usage, the input will be structured json formatted, so does the return.

- To maximize the productivity and protect the privacy of content creators, only input the pieced content.

- To reduce the bandwith usage of the website, it will check each content only when it's changed once.

## Procedure

1. Scratch the content from the website.

2. Randomly select #% of the content.
    - 80% if the content is shorter than 500 words.
    - 60% if the content is 500-1000 words.
    - 40% if the content is 1000-3000 words.
    - 20% if the content is longer than 3000 words.

3. Send the content to the AI model.
    - Return True if the content is appropriate.
    - Return False if the content is inappropriate.

4. Receive the result.
    - If True, do nothing.
    - If False, trigger the visibility and warning.

## AI prompt

Parameters: {content}, {tos-content}

Prompt: Check {content} if it's follow the {tos-content}.

Return: {rtn}, True if it's appropriate, False if it's inappropriate.