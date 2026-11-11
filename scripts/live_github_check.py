"""Read-only smoke test; it initializes no user state."""
import json
from skillscout.github import GitHub

client = GitHub()
meta = client.metadata("NVIDIA/SkillSpector")
assert meta["full_name"] == "NVIDIA/SkillSpector"
revision = client.revision("NVIDIA/SkillSpector")
assert len(revision) == 40
history = client.history("NVIDIA/SkillSpector")
print(json.dumps({"metadata": "passed", "revision": revision,
                  "history": history, "state_initialized": False}))
