.PHONY: install collect build status migrate gsc-collect gsc-report gsc-sites

install:
	python3 -m venv .venv
	.venv/bin/pip install -r pipeline/requirements.txt
	cd site && pnpm install

collect:
	.venv/bin/python -m pipeline.cli collect --all

build:
	.venv/bin/python -m pipeline.cli build

migrate:
	.venv/bin/python -m pipeline.cli migrate

status:
	.venv/bin/python -m pipeline.cli status

gsc-sites:
	.venv/bin/python -m pipeline.cli gsc-sites

gsc-collect:
	.venv/bin/python -m pipeline.cli gsc-collect

gsc-report:
	.venv/bin/python -m pipeline.cli gsc-report
