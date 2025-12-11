# Interlock

Interlock is a documentation-governance engine that identifies outdated, duplicated, or low-quality Confluence pages using deterministic scoring and structured LLM evaluation. It provides automated visibility into the health of knowledge bases without modifying content or requiring manual auditing.

Interlock integrates with Confluence and Glean, retrieves page metadata, ranks pages by urgency, evaluates selected pages with an LLM, and writes back structured diagnostics for teams to act on.

---

## Why Interlock exists

Large organizations accumulate thousands of documentation pages. Over time, many become stale, duplicated, or low-quality. Traditional cleanup is manual, unreliable, and rarely prioritized.

Interlock solves this by:

- Continuously scanning existing documentation.
- Using **deterministic metadata scoring** (freshness, traffic, backlinks, duplication signals).
- Applying **LLM-based evaluation** only where necessary.
- Surfacing actionable insights *without editing the documentation itself*.
- Providing a clear governance loop that improves documentation quality over time.

---

## Core principles

Interlock is designed around a strict governance model:

1. **Confluence is the system of record**  
   Interlock never modifies documentation text. It only reads metadata and writes diagnostic comments/scores.

2. **Metadata-only storage**  
   No page bodies or sensitive content is stored. Only metadata, ranking values, and evaluation summaries are retained.

3. **Deterministic prioritization**  
   Ranking is rule-based and reproducible. LLMs do not influence prioritization order.

4. **LLM evaluation layer**  
   After deterministic ranking selects a batch of pages, the LLM evaluates structure, clarity, duplication, and quality using a strict schema.

5. **Non-intrusive governance**  
   Interlock does not attempt autonomous rewriting. It flags issues so humans can update the documentation safely.

6. **Continuous evaluation loop**  
   The system runs periodically, providing ongoing, incremental improvement.

---

## High-level architecture

### 1. Data ingestion
- Retrieve page metadata from Confluence (title, links, modified date, views, hierarchy, labels).
- Retrieve organizational signals from Glean (search impressions, click-through, duplication clusters).
- Normalize into a lightweight metadata index (no page content stored).

### 2. Deterministic ranking engine
Pages are scored using:
- Freshness decay
- User traffic and link analysis
- Duplication candidates
- Missing owners
- Structural completeness indicators

Produces a prioritized queue of pages needing review.

### 3. LLM evaluation engine
For the top-ranked pages:
- Pull page body **directly from Confluence** (not stored).
- Provide page text + metadata + deterministic signals to an evaluation LLM.
- LLM returns a structured result:
  - Clarity score
  - Structure quality
  - Duplication likelihood
  - Recommended action (review, consolidate, archive)
  - Notes or flags

### 4. Write-back to Confluence
Interlock writes:
- Page health score  
- Diagnostic summary  
- Optional comments or metadata updates  

**It does not modify the page content.**

### 5. Scheduled pipeline
Interlock runs daily/weekly:
- Refresh metadata index  
- Recompute rankings  
- Re-evaluate top pages  
- Produce governance reports  

---

## Integration points

### Confluence API
Used for:
- Metadata retrieval  
- Page body fetch (read-only)  
- Writing diagnostic entries  

### Glean API
Used for:
- Search and usage signals  
- Duplication detection clusters  
- Traffic patterns  

### LLM Provider
Used for:
- Structured evaluation of selected pages  
- No role in ranking or metadata ingestion  

---

## Data model

Interlock stores only:
- Page ID  
- Titles, timestamps, link counts  
- Ranking metrics  
- Evaluation results  
No HTML, no bodies, and no sensitive content are stored.

---

## System guarantees

- **Reproducibility**: same metadata inputs → same ranking.  
- **No autonomous editing**: ensures governance safety.  
- **Explainability**: all scores and flags are attributable to clear rules or LLM schema fields.  
- **Privacy compliance**: metadata-only persistence reduces exposure.

---

## Deployment

Interlock can run as:
- A scheduled serverless job (AWS Lambda / GCP Cloud Run / Azure Functions)  
- A containerized service with a cron-like trigger  
- A lightweight internal microservice integrated with Glean and Confluence proxies  

Configuration includes:
- Confluence API token  
- Glean API token  
- Evaluation LLM endpoint  
- Schedule frequency  
- Metadata index storage location  

---

## Roadmap

### Phase 1 — Foundation  
- Metadata ingestion  
- Deterministic scoring engine  
- Metadata index storage  
- Confluence write-back  

### Phase 2 — Evaluation  
- Page-body retrieval on-demand  
- LLM evaluation schema  
- Diagnostic reporting  

### Phase 3 — Governance analytics  
- Weekly governance dashboards  
- Duplicate-cluster insights  
- Owner-based alerts  

### Phase 4 — Advanced insights (optional)  
- Knowledge graph integration  
- Version drift detection  
- Doc lifecycle recommendations  

---

## Non-goals

Interlock does **not**:
- Edit or rewrite Confluence pages  
- Store documentation bodies  
- Act as a CMS or drafting tool  
- Replace Confluence or Glean search  

---

## Example workflow

1. Interlock pulls 10,000 page metadata entries.  
2. Ranking engine selects 150 highest-risk pages.  
3. LLM evaluates 20 pages in the current batch.  
4. Interlock writes back scores and flags to each page.  
5. Documentation owners see automated insights and update content accordingly.  
6. Next day/week, the cycle continues.

---

## Contributing

This project emphasizes:
- Deterministic logic first  
- LLM usage only within constrained schemas  
- Separation between metadata, ranking, and evaluation  

Contributions should maintain these boundaries and avoid introducing autonomous editing features.

---

## License

Internal / TBD based on organization usage.
