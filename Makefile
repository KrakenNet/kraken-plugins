.PHONY: lint validate frontmatter smart-kraken

lint: validate frontmatter smart-kraken
	@echo "all lints OK"

validate:
	./scripts/validate-marketplaces.sh

frontmatter:
	./scripts/lint-frontmatter.sh

smart-kraken:
	./scripts/lint-smart-kraken.sh
