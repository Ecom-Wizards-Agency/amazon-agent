---
title: "Multi-Agent Advertising Campaign Creation Workshop"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/workshop-gen-ai-langgraph-agents/overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
---

# Multi-Agent Advertising Campaign Creation Workshop

This workshop explains how to build a production-ready multi-agent system for Amazon Advertising with AWS Bedrock AgentCore.

Duration: ~3 hours  
Level: Intermediate  
Prerequisites: Python 3.12+, AWS account, basic familiarity with LLMs and APIs

## Architecture

```text
User
  -> Chat Frontend
  -> Orchestration Agent
       -> Custom Ads Agent: profile and campaign CRUD
       -> Amazon Ads MCP Agent: analytics and reporting
       -> S3 Vectors Agent: RAG knowledge base
       -> RDS Campaign Agent: database queries through MCP Gateway
```

Each agent is deployed independently to AWS Bedrock AgentCore and communicates through the A2A protocol. The orchestration agent uses an LLM to choose which sub-agent handles each request.

## Modules

| # | Module | Duration |
| --- | --- | --- |
| 0 | Environment Setup | 15 min |
| 1 | Understanding the Architecture | 15 min |
| 2 | Building an MCP Server | 20 min |
| 3 | Building an A2A Agent | 25 min |
| 4 | Building a RAG Agent with S3 Vectors | 25 min |
| 5 | Building the Orchestration Agent | 25 min |
| 6 | Deploying Agents to AgentCore | 15-30 min |
| 6A | Manual Deployment | ~30 min |
| 6B | Automated Deployment | ~15 min |
| 7 | Building the RDS Agent with MCP Gateway | 20 min |
| 8 | Connecting the Chat Frontend | 15 min |
| 9 | Testing & Troubleshooting | 10 min |
| 10 | Cleanup | 10 min |

## Quick navigation

- Concepts only: modules 1-5.
- Deployment: module 6, choose manual or automated.
- Full end-to-end experience: modules 0-9.
- Short path: modules 0, 1, 6B, 8, 9.

## Project structure

| Folder | Purpose |
| --- | --- |
| `custom-ads-mcp/` | MCP server wrapping Ads API. |
| `custom-ads-a2a-agent/` | Profile and campaign A2A agent. |
| `mcp-ads-a2a-agent/` | Analytics and reporting A2A agent. |
| `s3-vectors-a2a-agent/` | RAG knowledge base agent. |
| `orchestration-a2a-agent/` | Orchestration agent. |
| `custom-ads-rds-mcp-agent/` | RDS agent plus CDK infrastructure. |
| `ads-chat-nextjs/` | Next.js chat frontend. |
| `deployment_tool/` | Automated deployment CLI. |

## Routing use

Use this page when planning a proper Amazon Ads routing skill/agent architecture, especially if the task needs specialized agents for Ads API CRUD, reporting, RAG knowledge retrieval, database querying, and a user-facing chat interface.
