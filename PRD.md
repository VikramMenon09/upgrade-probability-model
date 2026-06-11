# Product Requirements Document — Smartphone Upgrade Probability Model Repo

## 1. Product Overview
The Smartphone Upgrade Probability Model is an academic research-focused Python repository that recreates and extends a behavioral economics simulation of smartphone upgrade decisions. The project models how different environmental information conditions affect consumer upgrade probability in the United States and India.

The repo is based on a research paper about environmental framing, moral licensing, and smartphone upgrade decisions. The paper argues that positive environmental trade-in messaging may not reduce upgrades; instead, it may morally license consumers to upgrade sooner by reducing psychological resistance. The model compares three information conditions: no environmental framing, positive manufacturer framing, and accurate environmental cost disclosure.

The product should function as a transparent, reproducible, and visually clear modeling tool for research, GitHub portfolio presentation, and future empirical expansion.

## 2. Problem Statement
Smartphone manufacturers often frame trade-in programs as environmentally responsible. However, this framing may unintentionally increase consumers' willingness to upgrade by making them feel that the environmental cost has already been handled.

Currently, this theory exists mainly as a written simulation model. The problem is that the model needs to be translated into a reproducible technical project that allows users to:

1. Inspect the formula and assumptions.
2. Recreate the baseline results.
3. Adjust key parameters.
4. Visualize sensitivity analysis.
5. Understand how moral licensing differs across markets.

## 3. Goals
The goal of this project is to create a polished, research-oriented GitHub repo that demonstrates economics, behavioral science, environmental policy, and Python modeling.

Core goals:

- Recreate the upgrade probability simulation from the paper.
- Compare upgrade probability across the United States and India.
- Show how positive environmental framing changes predicted upgrade behavior.
- Model the effect of claim verifiability and environmental self-identity.
- Include sensitivity analysis for credit-to-income ratio, claim verifiability, present bias, and disclosure specificity.
- Provide a clean notebook that a reviewer, teacher, professor, or admissions reader could understand.
- Provide optional interactive sliders through Jupyter widgets or Streamlit.

## 4. Non-Goals
This project is not intended to prove a causal relationship using real-world consumer data yet. The first version will not:

- Scrape real-time data from Apple, Samsung, IDC, or Counterpoint.
- Make final empirical claims about actual consumers.
- Include a full randomized survey experiment.
- Estimate parameters using original survey data.
- Predict individual consumer behavior with high accuracy.
- Function as a commercial app.

The product is a simulation and research demonstration, not a validated production forecasting system.

## 5. Target Users
**Primary users:** the student researcher developing the model; research supervisors reviewing the model structure; college admissions readers evaluating independent research and technical ability; economics or behavioral science teachers; GitHub visitors interested in behavioral economics and environmental policy.

**Secondary users:** students studying consumer economics; environmental policy researchers; developers interested in simple economic modeling.

## 6. User Stories
**Researcher:** run the notebook and recreate the baseline results; adjust parameters like claim verifiability and environmental identity to test sensitivity; clearly see the model formula and assumptions.

**Reviewer:** a clean README; graphs that match the paper's argument; clearly stated limitations.

**Portfolio:** a polished, organized repo; a project that connects research, modeling, and real-world policy relevance.

## 7. Core Model
The model estimates upgrade probability using the following function:

```text
P(upgrade | f) = Φ[ v(C/Y) - κ + γ · φ(f) · (1 - V) · (1 - ω) ]
```

Where:

```text
C/Y     = trade-in credit-to-income ratio
v(C/Y)  = utility from trade-in credit relative to income
κ       = baseline resistance to upgrading
γ       = moral licensing effect size
φ(f)    = framing condition effect
V       = claim verifiability
ω       = environmental self-identity weight
Φ       = standard normal cumulative distribution function
```

The three framing conditions are:

```text
Control:             no environmental framing
Positive framing:    manufacturer presents trade-in as environmentally responsible
Accurate disclosure: consumer receives specific environmental cost information
```

## 8. Functional Requirements
**8.1 Notebook** — title and explanation, research question, formula, parameter table, baseline US/India simulation, framing bar chart, sensitivity analyses (verifiability, credit-to-income, information specificity), optional sliders, limitations.

**8.2 Python module (`model.py`)** — functions for trade-in utility, framing-condition term, latent upgrade score, upgrade probability, and moral-licensing strength; modular enough to import elsewhere.

**8.3 Data (`data/parameters.csv`)** — baseline values per market: market, claim verifiability, environmental self-identity, moral-licensing effect, present bias, discount factor, baseline resistance, specificity threshold. Initial markets: United States, India.

**8.4 Visualizations** — (1) upgrade probability by framing condition and market, (2) moral-licensing strength vs. claim verifiability, (3) upgrade probability across credit-to-income ratios, (4) accurate-disclosure effect across information specificity, (5) optional present-bias sensitivity. Clear titles, labeled axes, legends, percent formatting, simple academic styling.

**8.5 Streamlit app** — adjust market, credit-to-income, information specificity, claim verifiability, environmental self-identity, moral-licensing effect, baseline resistance, specificity threshold; output upgrade probability per condition, a bar chart, moral-licensing strength, and a credit-to-income sensitivity curve.

## 9. Non-Functional Requirements
Easy to install and run locally; well-commented; understandable with basic Python; visually clean; academically honest about limitations; organized like a real research codebase. The notebook prioritizes clarity and reproducibility over advanced ML.

## 10. Repo Structure
```text
upgrade_probability_model_repo/
├── README.md
├── PRD.md
├── requirements.txt
├── model.py
├── figures.py
├── app.py
├── data/
│   └── parameters.csv
├── notebooks/
│   └── upgrade_probability_model.ipynb
└── figures/
    └── *.png
```

## 11. Success Metrics
Clone-and-run with no errors; notebook recreates the baseline; README explains the project in under two minutes; graphs support the argument; modular, easy-to-modify code; clearly demonstrates interest in economics, behavioral science, and environmental policy; reader understands it is a simulation, not a completed empirical study.

## 12. MVP Scope
`README.md`, `requirements.txt`, `model.py`, `parameters.csv`, `upgrade_probability_model.ipynb`, and at least three charts (baseline framing comparison, claim-verifiability sensitivity, information-specificity threshold). No deployed app, real survey data, or scraping required.

## 13. Version 1 Scope
Complete notebook, clean baseline visualizations, Streamlit demo, parameter sliders, exported figures, strong README, clear limitations, and an explanation of how the project connects to the research paper.

## 14. Version 2 Ideas
Randomized survey experiment; real consumer-response data; Apple/Samsung trade-in language comparison; country expansion; advanced parameter calibration; confidence intervals or Monte Carlo simulation; Streamlit Community Cloud deployment; disclosure-requirement policy simulator; claim-verifiability scoring system.

## 15. Risks and Limitations
The main risk is overclaiming — the model is theoretical and simulation-based and must not be presented as proof that environmental framing causes upgrades. Parameter values are hard to validate; market-level assumptions hide individual differences; the model simplifies behavior; verifiability and self-identity are hard to measure; disclosure effects vary with wording, trust, numeracy, and culture. The repo states clearly that the model is a theoretical simulation intended to generate testable predictions.

## 16. Launch Checklist
Confirm the notebook runs top-to-bottom; add chart screenshots to the README; add a short description and limitations section; add a citation/note linking to the paper; check spelling/formatting; make the repo public; add topics: `behavioral-economics`, `environmental-economics`, `moral-licensing`, `e-waste`, `python`, `simulation`, `consumer-behavior`, `sustainability`.

## 17. One-Sentence Product Description
A Python-based behavioral economics simulation that models how environmental trade-in framing may influence smartphone upgrade probability through moral licensing across the United States and India.
