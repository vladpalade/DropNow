# DropNow: Advanced E-Commerce Arbitrage & Intelligence System

DropNow is an automated market intelligence pipeline designed to solve a complex data problem in the dropshipping industry: validating product profitability and true quality at scale. 

Instead of relying on manual research, this application autonomously scrapes B2B supplier data, evaluates real customer sentiment using a custom-built Deep Learning model trained from scratch, and cross-references supply costs with local retail markets to calculate exact, unit-normalized profit margins.

![Product Analysis Dashboard]((https://raw.githubusercontent.com/vladpalade/DropNow/main/assets/analysis_dashboard.png))

## Key Features & Business Logic

* **Custom NLP Sentiment Engine:** Replaces misleading aggregate star ratings with deep text analysis. Raw customer reviews are processed through a custom PyTorch Multi-Layer Perceptron (MLP) to evaluate true product quality and predict potential return rates.
* **Advanced DOM Manipulation & Scraping:** Utilizes Playwright to navigate complex, dynamically rendered single-page applications (AliExpress). The system autonomously bypasses UI restrictions, ad placements, and anti-bot layouts by executing precise, coordinate-based hardware-level clicks to extract optimal hidden product variants.
* **Unit-Price Normalization (Apples-to-Apples):** Automatically detects and extracts product quantities from unstructured text using advanced regular expressions (e.g., standardizing a "50-pack" vs. "Set of 10"). It mathematically scales supplier bulk prices against competitor retail prices to compute the absolute unit profit.
* **Market Arbitrage Intelligence:** Instantly searches the local target market (eMAG), filters out sponsored or anomalous listings, and establishes a realistic retail baseline to calculate precise net profit margins for the entire imported package.

![User Portfolio & History](https://raw.githubusercontent.com/vladpalade/DropNow/main/assets/portofolio_history.png)

## Technology Stack

**Backend & Data Engineering:**
* **Python 3.10+**
* **FastAPI:** High-performance, asynchronous REST API for seamless client-server communication.
* **Playwright:** Headless browser automation handling asynchronous JS execution and dynamic DOM traversal.
* **SQLite:** Lightweight relational database managing user states, portfolio persistence, and analysis history.

**Machine Learning (NLP Pipeline):**
* **PyTorch:** Framework utilized to build, train, and deploy the neural network.
* **Scikit-Learn:** TF-IDF Vectorization (capped at 15,000 features) for text preprocessing.
* **Architecture & Optimization:** Trained on a comprehensive Kaggle dataset of e-commerce reviews. To handle massive sparse matrices without exceeding system RAM constraints during training, a custom PyTorch `Dataset` was implemented leveraging lazy-loading (`toarray().squeeze()`) for batch processing.

**Frontend Interface:**
* **Vanilla JavaScript (ES6+), HTML5, CSS3:** A zero-dependency, highly responsive UI engineered for performance, featuring modern design principles, asynchronous `fetch` requests, and state-driven micro-interactions.

## The Machine Learning Architecture

The core quality-assurance mechanism is a bespoke neural network built to decode the nuances of e-commerce reviews:
1. **Data Sourcing:** An extensive dataset of raw reviews was sourced from Kaggle and preprocessed using Pandas.
2. **Feature Extraction:** Text variables are mapped into numerical representations using a TF-IDF Vectorizer.
3. **Neural Network:** A PyTorch model featuring a hidden layer (256 neurons, ReLU activation) compresses the 15,000 TF-IDF features into a definitive, float-based quality score.
4. **Inference Integration:** The serialized model weights (`.pth`) and vocabulary dictionary (`.pkl`) are loaded into the FastAPI backend, enabling real-time NLP inference while the scraping pipeline runs asynchronously.

## Project Scope

This application goes beyond standard CRUD operations by addressing unstructured data normalization. Comparing a "Magic Sponge 50-pack" on a B2B supplier platform with a "Sponge - 4 pieces" on a local retail site requires intelligent text parsing, dynamic UI interaction, and mathematical scaling—all executed autonomously by the DropNow pipeline in under 60 seconds.

## Future Roadmap

As B2B platforms become increasingly saturated with artificial feedback, the next iteration of DropNow focuses on data purity:
* **AI-Generated Review Filtering:** Developing a secondary classification layer (Zero-Shot anomaly detection) designed to identify and filter out synthetic, LLM-pumped seller reviews. This will ensure the sentiment engine evaluates only authentic human feedback, further reducing the risk of high-return-rate product selection.
