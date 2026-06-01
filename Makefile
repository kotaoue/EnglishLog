.PHONY: lint lint-spell lint-markdown prune

lint: lint-spell lint-markdown

lint-spell:
	cspell "**/*.md" --config cspell.json

lint-markdown:
	markdownlint-cli2 "**/*.md"

prune:
	@current=$$(git branch --show-current); \
	merged=$$(git for-each-ref --format='%(refname:short)' refs/heads --merged); \
	keep_remote_quiz=$$(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/remotes/origin/quiz | head -n 1); \
	keep_local_quiz=$${keep_remote_quiz#origin/}; \
	deleted=0; \
	for branch in $$merged; do \
		case "$$branch" in \
			main|master|develop|dev|$$current) continue ;; \
		esac; \
		git branch -d "$$branch" && deleted=1; \
	done; \
	for branch in $$(git for-each-ref --format='%(refname:short)' refs/heads/quiz/); do \
		case "$$branch" in \
			$$current|$$keep_local_quiz) continue ;; \
		esac; \
		git branch -D "$$branch" && deleted=1; \
	done; \
	if [ $$deleted -eq 0 ]; then \
		echo "No local branches to delete."; \
	elif [ -n "$$keep_remote_quiz" ]; then \
		echo "Kept $$keep_local_quiz (from $$keep_remote_quiz)."; \
	fi
