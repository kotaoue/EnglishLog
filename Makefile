.PHONY: lint lint-spell lint-markdown

lint: lint-spell lint-markdown

lint-spell:
	cspell "**/*.md" --config cspell.json

lint-markdown:
	markdownlint-cli2 "**/*.md"
