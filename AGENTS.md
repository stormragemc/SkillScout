# Working on SkillScout

Use Python 3.11+. Run the unittest suite, build_bundle.py and check_package.py.
Use temporary SKILLSCOUT_HOME directories. Never initialize the user's actual
skills, accounts or scheduler as a test. Do not commit credentials, downloaded
candidates, media or private state.

Maintain one canonical skill at skills/skillscout. Host manifests reference it;
the bundle builder adds the runtime without installing. Preserve fail-closed
security gates. Gate changes require meaningful regression tests and accurate
coverage notes. Do not execute untrusted candidate scripts or approve on a
scheduled user's behalf.
