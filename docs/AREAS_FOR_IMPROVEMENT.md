# Areas for Improvement

This document captures concrete improvement opportunities based on the current repository state.

## Documentation and Onboarding
- **Fix the clone path typo in the README.** The quick-start instructions say `cd programminglangauage`, which looks like a typo that can confuse new users; it should match the repo name. (Source: `README.md` clone instructions.)
- **Document API/server dependencies separately from core.** The README and `requirements.txt` emphasize "no external dependencies," but there is a dedicated `requirements-api.txt` for FastAPI/uvicorn, etc. It would help to add a short README section that explains when to use each requirements file and how to run the API/server components.

## Packaging and Installation
- **Add an installable `api` extra in `setup.py`.** Since API dependencies are already listed in `requirements-api.txt`, exposing them as an optional extra (e.g., `pip install .[api]`) would make setup easier and keep packaging in sync with the API stack.

