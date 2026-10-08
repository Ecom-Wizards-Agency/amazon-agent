---
title: "Multi-Agent Advertising Campaign Creation Workshop"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/workshop-gen-ai-langgraph-agents/overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
---

# How to build a multi-agent advertising system with AWS Bedrock AgentCore

by Youssry Abubakr Partner Solutions Architect @ Amazon Ads, Chintan Sanghavi Lead Solutions Architect @ Amazon Ads on March 18th 2026

**Duration:** ~3 hours

**Level:** Intermediate

**Prerequisites:** Python 3.12+, AWS account, basic familiarity with LLMs and APIs

## Introduction

This workshop walks you through building a production-ready multi-agent system for Amazon Advertising. An orchestration agent intelligently routes user queries to specialized sub-agents:

```
User  → Chat Frontend → Orchestration Agent
                            ├── Custom Ads Agent      (profile  &  campaign CRUD)
                            ├── Amazon Ads MCP Agent   (analytics  &  reporting)
                            ├── S3 Vectors Agent       (RAG knowledge base)
                            └── RDS Campaign Agent     (database queries via MCP Gateway)
```

Each agent is independently deployed to AWS Bedrock AgentCore and communicates using the A2A protocol. The orchestration agent uses an LLM to decide which sub-agent should handle each request.

## Modules

| # | Module | Duration |
| --- | --- | --- |
| 0 | Environment Setup | 15 min |
| 1 | Understanding the Architecture | 15 min |
| 2 | Building an MCP Server | 20 min |
| 3 | Building an A2A Agent | 25 min |
| 4 | Building a RAG Agent with S3 Vectors | 25 min |
| 5 | Building the Orchestration Agent | 25 min |
| 6 | Deploying Agents to AgentCore | 15–30 min |
| 6A | ↳ Option A: Manual Deployment | ~30 min |
| 6B | ↳ Option B: Automated Deployment | ~15 min |
| 7 | Building the RDS Agent with MCP Gateway | 20 min |
| 8 | Connecting the Chat Frontend | 15 min |
| 9 | Testing & Troubleshooting | 10 min |
| 10 | Cleanup | 10 min |

## Quick Navigation

**Just want to understand the concepts?** → Modules 1–5

**Ready to deploy?** → Module 6 (pick Option A or B)

**Want the full end-to-end experience?** → Modules 0–9 in order

**Short on time?** → Modules 0, 1, 6B (automated deploy), 8, 9

## Project Structure

```
├──   custom-ads-mcp/                   # MCP server wrapping Ads API (Module 2) 
 ├──   custom-ads-a2a-agent/             # Profile & campaign A2A agent (Module 3) 
 ├──   mcp-ads-a2a-agent/                # Analytics & reporting A2A agent (Module 3) 
 ├──   s3-vectors-a2a-agent/             # RAG knowledge base agent (Module 4) 
 ├──   orchestration-a2a-agent/          # Orchestration agent (Module 5) 
 ├──   custom-ads-rds-mcp-agent/         # RDS agent + CDK infra (Module 7) 
 ├──   ads-chat-nextjs/                  # Next.js chat frontend (Module 8) 
 ├──   deployment_tool/                  # Automated deployment CLI (Module 6B)
```

Next: Environment Setup →
