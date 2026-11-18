PY := python3
NB := notebooks/analysis_walkthrough.ipynb

.PHONY: all setup figures notebook firmware clean

all: figures notebook

setup:
	bash scripts/setup_env.sh

figures:
	$(PY) simulation/terramechanics_analysis.py

notebook:
	jupyter nbconvert --to notebook --execute --inplace $(NB)

firmware:
	arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name ".ipynb_checkpoints" -exec rm -rf {} +
