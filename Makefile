# Makefile
PYTHON ?= python3.12

.PHONY: install serve refresh test

install:
	$(PYTHON) -m pip install -e '.[dev]'

serve:
	$(PYTHON) -m ai_debt_bubble_analysis serve

refresh:
	$(PYTHON) -m ai_debt_bubble_analysis refresh

test:
	$(PYTHON) -m pytest -q
