# 7.4 When BDD Is Required

### 7.4 When BDD Is Required

Generate BDD/Gherkin scenarios for:
- **User-facing features** — Any AC that describes end-user behavior (registration, checkout, search)
- **Multi-step workflows** — Features involving state transitions (order lifecycle, approval flows)
- **Stakeholder-visible behavior** — Features that non-technical stakeholders need to verify

Skip BDD for:
- Internal infrastructure (DB migrations, caching, logging)
- Pure computation (math functions, data transformations)
- Developer-facing APIs with no UI (unless consumer contracts apply)

---

