---

## **Expected Challenges in Implementation**

### **1. Confluence API limitations and rate constraints**

- Metadata and page-body fetch frequency must respect rate limits.
- Large enterprise spaces may require batching and optimized crawling.
- Confluence Cloud vs Server differences may affect connectors.

### **2. Scaling deterministic ranking at enterprise size**

- Processing tens of thousands of pages requires efficient metadata indexing.
- Link-graph analysis and duplication detection must remain performant at scale.
- Ranking must remain stable, deterministic, and explainable.

### **3. Context assembly for LLM evaluation**

- Choosing the correct structural neighbors and canonical candidates is non-trivial.
- Over-contextualizing or under-contextualizing may skew LLM scoring.
- LLM prompt design must minimize hallucination and ensure repeatability.

### **4. LLM cost optimization**

- Evaluating thousands of pages regularly can be expensive.
- Requires batching, prioritization, and selective evaluation strategies.

### **5. Score surfacing inside Confluence**

- Must ensure atomic and reliable updates to metadata fields.
- Comment posting should avoid noise or duplication.
- Permissions and app-level access need to be configured correctly.

### **6. Avoiding false positives and instability in evaluation**

- Duplication detection and conflict identification must be robust and explainable.
- LLM scoring must remain stable across iterations and model upgrades.

### **7. Maintaining continuous evaluation cycles**

- Designing a scheduler that balances freshness, throughput, and concurrency.
- Ensuring evaluation loops do not create overload on Confluence or LLM backends.

### **8. Alignment with enterprise AI systems (e.g., Glean)**

- Page scores and diagnostic flags must be consistently formatted and exported.
- Enterprise search systems may require additional metadata mapping.
- Must avoid leaking internal evaluation-only fields unintentionally.
