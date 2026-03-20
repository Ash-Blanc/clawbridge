---
name: web-search
description: Search the web for current information
category: research
version: 1.0.0
author: clawbridge
tags:
  - search
  - web
  - research
tools:
  - name: search_web
    description: Search the web using DuckDuckGo
    parameters:
      - name: query
        type: string
        description: The search query
        required: true
      - name: max_results
        type: integer
        description: Maximum number of results to return
        required: false
        default: 5
  - name: fetch_url
    description: Fetch and extract content from a URL
    parameters:
      - name: url
        type: string
        description: The URL to fetch
        required: true
---

# Skill: Web Search

## Overview
You can search the web for current information using DuckDuckGo.
Use this skill when the user asks about recent events, current data,
or anything that might not be in your training data.

## Guidelines
- Always cite your sources
- Prefer recent results
- Summarize findings concisely
- If results are ambiguous, present multiple perspectives

## Examples
- "What's the latest news about AI?"
- "Find the current price of Bitcoin"
- "Search for reviews of the new MacBook"