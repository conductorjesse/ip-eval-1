# IP Evaluation Tool

A Streamlit-based tool for evaluating intellectual property (patents) for commercial viability. Analyzes patents from Google Patents using AI to provide structured assessments across technology readiness, market potential, and further exploration areas.

## Features

- **Patent Analysis** — Automatically scrape and analyze patents from Google Patents
- **Portfolio Analysis** — Evaluate multiple complementary patents together
- **IP Score Matrix** — EPO IPScore methodology assessment across 5 categories (Legal, Technology, Market, Finance, Strategy)
- **Interactive Chat** — Ask follow-up questions about specific evaluation sections
- **PDF Export** — Download evaluation results as formatted reports

## Setup

### Prerequisites

- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create `.streamlit/secrets.toml` and add your OpenAI API key:

```bash
mkdir -p .streamlit
```

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-openai-api-key-here"
```

### Run

```bash
streamlit run main.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

## Usage

1. **Analysis Setup** — Enter your background/goals and paste a patent number (e.g. `US9138726B2`) or Google Patents URL
2. **Evaluation Results** — Review the AI-generated analysis across Technology, Market, and Further Exploration tabs
3. **IP Score Matrix** — Complete the structured EPO IPScore questionnaire for a quantitative assessment
4. **Tools & Resources** — Additional reference materials

## Project Structure

```
├── main.py                  # Streamlit app entry point
├── logic/
│   ├── analysis.py          # AI analysis and chat functions
│   ├── scraper.py           # Google Patents web scraper
│   └── report_generator.py  # PDF report generation
├── ui/
│   ├── layout.py            # Main UI layouts and navigation
│   ├── ip_score.py          # IP Score Matrix page
│   └── tools.py             # Tools & Resources page
├── data/
│   └── IPscore-full-table.csv  # EPO IPScore questionnaire data
├── .devcontainer/
│   └── devcontainer.json    # VS Code DevContainer / Codespaces config
└── requirements.txt
```

## DevContainer / Codespaces

This repo includes a DevContainer config for VS Code or GitHub Codespaces. Opening in a DevContainer will automatically install dependencies and start the Streamlit server on port 8501.
