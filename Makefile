.PHONY: check reproduce

check:
	python -m unittest discover -s tests -v

reproduce:
	python -m education_finance_mlops run-release --train-through-year 2020 --evaluation-year 2021 --score-year 2022 --output artifacts/release-v1-2022
	-python -m education_finance_mlops run-release --train-through-year 2021 --evaluation-year 2022 --score-year 2023 --output artifacts/release-v1-2023
