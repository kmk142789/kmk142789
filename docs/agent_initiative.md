# Echo Autonomous Initiative Backlog

The `tools/agent_initiative.py` helper generates a curated list of improvement
opportunities for the repository.  It balances the estimated impact of each
initiative with the effort required so collaborators can quickly decide where to
spend their creative energy.

## Usage

```bash
python -m tools.agent_initiative
```

Running the module prints a ranked backlog similar to the snippet below:

```
Echo Autonomous Initiative Backlog
===============================
1. Strengthen autonomous test coverage (score 2.25)
   Impact: 9
   Effort: 4
   Description:
     Backfill regression tests for the automated Echo flows so that iterative
     agents can move faster without breaking the existing rituals.
```

Developers can also import `generate_ranked_initiatives` to embed the planning
signal inside dashboards, notebooks, or orchestration scripts.
