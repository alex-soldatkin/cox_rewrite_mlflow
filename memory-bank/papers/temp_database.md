---
title: A Neo4j graph database <br> of the Russian banking system
authors: 
    - name: Alexander Soldatkin 
      email: alexander.soldatkin@sant.ox.ac.uk
      affiliations:
        - name: University of Oxford
          department: Oxford School of Global and Area Studies
keywords: 
    - graph databases
    - Russian banking
    - compliance data
    - network analysis

abstract: | 
        We present a Neo4j graph database of the Russian banking system that integrates heterogeneous sources into a unified, queryable network of banks, companies, individuals, and public bodies. The database combines (i) Central Bank of Russia (CBR) ownership/control statements (PDF converted to structured format), (ii) CBR regulatory and accounting forms (DBF: 101/102), (iii) Banki.ru registries and news, and (iv) Reputation.ru compliance data. We develop a reproducible pipeline that uses OCR and large language models to parse semi-structured ownership documents into a validated JSON schema, followed by cleaning, entity resolution (REGN/OGRN/INN/name), and import into Neo4j with Graph Data Science (GDS) projections. The current release contains over 61k nodes and 114k relationships with rich metadata and is designed for traversal of ownership chains, measurement of network structure, and linkage to bank-level financial indicators.

        This article documents the data sources, processing and integration methods, data model, and quality checks, and provides an extensive descriptive overview of the resulting graph (coverage, composition, relationship types, and network topology). We also supply a library of Cypher queries for common operations and illustrate how the resource can support future research on ownership structures, state involvement, and foreign participation—without making substantive claims here. The database, import scripts, and example notebooks are released with versioning to facilitate reuse, replication, and extension.

format:
  typst:
    toc: true
    # toc-title: "Contents"
    toc-depth: 2
    number-sections: true
    number-depth: 2
    mainfont: "CMU Bright"
    syntaxes:
        - ./cypher.sublime-syntax
    template-partials:
        - ./typst-template.typ
    code-line-numbers: true

  pdf:
    pdf-engine: lualatex
    toc: true
    toc-title: "Contents"
    toc-depth: 2
    number-sections: true
    number-depth: 3
    mainfont: "CMU Bright"
    fig-pos: 'ht'
    lst-pos: 'ht'
    code-block-font-size: tiny
    highlight-style: pygments
    include-in-header: 
      text: |
        \usepackage{fvextra}
        \DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,commandchars=\\\{\}}
        \DefineVerbatimEnvironment{OutputCode}{Verbatim}{breaklines,commandchars=\\\{\}}
        \usepackage{adjustbox}
        \usepackage{etoolbox}
        \AtBeginEnvironment{table}{\begin{adjustbox}{width=\textwidth,center}}
        \AfterEndEnvironment{table}{\end{adjustbox}}
lang: "en-gb"
filters: 
  - quarto-ext/include-code-files
execute:
  enabled: true
jupyter:
  kernel: factions-env
---

```{=typst}
#import "@preview/muchpdf:0.1.0": muchpdf
// Collect figures (not raw blocks)
#let appendix_figures = state("appendix-figs", ())

// Helper: does a figure contain a raw block whose language starts with "appendix-"?
#let is_appendix_listing = context it => {
  // Find raw descendants of this figure (contextual query)
  let raws = query(raw)
  // Keep only those raws that are inside `it`'s location
  let loc = it.location()
  let inner = ()
  for r in raws {
    if r.location().is-inside(loc) {
      inner += (r,)
    }
  }
  if inner.len() == 0 { return false }
  // Check the first raw's language
  let lang = if inner.first().func.lang == none { "" } else { str(inner.first().func.lang) }
  lang.starts-with("appendix-")
}

// Intercept *figures* that are code listings and stash them.
// IMPORTANT: we still return `it` so the original figure renders with its lst-cap.
#show figure.where(kind: raw): it => {
  if is_appendix_listing(it) {
    appendix_figures.update(arr => (..arr, it))
  }
  it
}

// Render all collected figures at the end, reusing Quarto's original caption/numbering.
#let render_appendix_listings(title: "Appendix: Code listings") = context {
  let figs = appendix_figures.final()
  if figs.len() == 0 { return [] }

  pagebreak()
  heading(level: 1, title)

  // Re-print each figure exactly as captured
  for f in figs {
    // f is a figure element; reuse its body & caption
    figure(
      f.body,
      caption: f.caption, // retains Quarto’s lst-cap
      kind: f.kind,       // keep it a listing
      supplement: auto,   // default supplement ("Listing") as Quarto set it
      numbering: auto,
    )
    v(0.8em)
  }
}

```


```{python}
#| include: false
#| echo: false

from graphdatascience import GraphDataScience
from IPython.display import Markdown, HTML, display_html
import pandas as pd
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv(override=True)
uri = os.getenv("NEO4J_URI")
print(uri)
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))
gds = GraphDataScience(driver, database="neo4j")
```

{{< pagebreak >}}



## Introduction {.unnumbered}

<!-- The survival of Russian banks is contingent on a multitude of factors, such as their financial performance, the state of the economy, and their connection to the government. This analysis focuses on exploring whether the presence of a family in a bank's ownership and management network influences the likelihood of its survival. We compile a unique dataset in the form of a graph database (Neo4j) from various sources, such as information from the Central Bank on financial performance under the CAMEL framework, licence revocation records, data from the `reputation.ru` website, which in turn comprises data from a number of state agencies, such as the Federal Tax Service, the Unified State Register of Legal Entities; and Banki.ru news articles from 2007. Additionally, we incorporate a hitherto unused dataset from the Central Bank which is no longer publicly available, containing information on the persons with significant control over banks and their familial relationships as reported by the CBR or imputed using natural language processing (NLP) techniques. We process the data using large language models (LLMs) to extract relationships between nodes from textual information. After extensive cleaning and post-processing, we present a graph database with 61,710 nodes and 114,952 relationships, conduct some initial exploratory analysis on the network, and provide a number of sample queries for researchers using the Cypher query language and use cases for the database. This database promises to be a valuable resource for researchers dealing with complex ownership structures and allows them to trace down connections down to the level of individuals, opening up new avenues for research in field of the Russian political economy.  -->

The Russian banking sector has long been characterised by complex ownership structures, frequent regulatory interventions, and recurring episodes of financial instability. Yet, systematic data on the linkages between banks, their owners, affiliated companies, and regulatory actions have remained fragmented across multiple sources. Existing information is scattered across Central Bank filings, financial statements, licence revocation records, compliance registries, and media reports, often published in heterogeneous formats that are difficult to integrate. This lack of structured data has limited researchers’ ability to study questions of ownership concentration, state involvement, foreign participation, and broader patterns in the political economy of Russian finance.

This paper presents a new resource: a Neo4j [@robinson_GraphDatabases_2015] graph database of the Russian banking system. The database integrates information from a wide range of primary sources, including ownership and control statements from the Central Bank of Russia (CBR), accounting and regulatory filings, Banki.ru archives, and compliance indicators from reputation.ru. These sources have been processed using optical character recognition (OCR), large language models (LLMs), and extensive post-processing routines to extract and standardise entities (persons, companies, banks, government bodies) and relationships (ownership, management, family, regulatory actions).

The resulting database contains over 61,000 nodes and 114,000 relationships, with rich metadata on both entities and links. It allows researchers to traverse and query ownership chains, identify clusters of interconnected firms and individuals, and link structural information on networks to quantitative indicators of bank performance and regulatory outcomes. While this article focuses on documenting the construction, scope, and structure of the database, the resource is intended to support a wide range of applications---including future work on family ownership, state influence, and the survival of Russian banks.

In what follows, we situate the work in existing literature in @sec-related-work, describe the underlying data sources and the procedures used to extract and integrate them in @sec-data-collection-processing, outline the database structure and post-processing steps in @sec-postprocessing, and present descriptive statistics and network properties of the final dataset in @sec-descriptive-statistics. We conclude by discussing the database’s potential applications, limitations, and avenues for future updates.

## Related work {#sec-related-work}

Work on Russian bank data was systematised by Karas and Schoors, who reconciled commercial sources (KonfOb, Interfax, Mobile) into a near-population panel from 1997 to 2003 and documented the merging logic around the CBR registration number (`regn`), accounting break handling, and internal consistency checks. Their 2005 data-engineering paper, @karas_HeraclesSisyphusFinding_2005, and follow-on guide set the template for identities and statements; more recently, @karas_RussianBankData_2020 added hand-coded closure reason tags designed to be joined to CBR statements. Together, these assets made Russian banks empirically tractable, although they remained constrained by third-party aggregation, heterogeneous periodicity, and a limited 1995–2003 timespan. Our use of the CBR’s native statements extends that coverage and retains line-item granularity while remaining compatible with `regn`-keyed resources such as the closure-tag dataset.

A second strand builds ownership/control graphs at scale. @glattfelder_DecodingComplexityUncovering_2013 constructed a map of transnational corporate control and established both representation and stylised facts (a bow-tie with a tightly knit financial core), standardising influence/ultimate-control computations on directed ownership networks. These studies largely rely on Orbis-style sources, which are useful but uneven across countries, prompting guidance on how to model beneficial ownership and on data quality expectations. Our graph model borrows these representational choices but constrains the domain to banks and their immediate corporate neighbourhoods, using public Russian sources rather than commercial feeds.

A third segment of literature treats bank–bank relations directly through the lens of interbank lending. Interbank datasets, such as the one constructed by @fricke_CorePeripheryStructure_2015, typically reveal a core–periphery structure with a small, dense core and a sparse periphery; this appears robust across markets and maturities. While these works expose systemic linkages, they abstract from banks’ internal corporate webs and supervisory statements. Our database is complementary: it focuses on ownership and person–entity ties around individual banks, while remaining compatible with interbank layers should such edges be added later.

Finally, operational and academic anti-money-laundering (AML) work, for example, @johannessen_FindingMoneyLaunderers_2023, has shifted from rules to graph machine learning on heterogeneous transaction/role graphs. Recent studies report gains from graph neural networks (GNNs) on real bank data (e.g., DNB’s heterogeneous GNN from), self-supervised representations for customer–transaction bipartite graphs [@cardoso_LaundroGraphSelfSupervisedGraph_2022], and hybrid temporal–graph models [@alarab_GraphBasedLSTMAntimoney_2023]. Those approaches assume a reliable entity/relationship substrate and benefit from auxiliary signals on ownership, control, and governance [@IMF_UnmaskingControlGuide_2022]. By publishing a bank-centred, multi-label graph with documented data quality and `regn`-keyed joins to closure tags and CBR accounts, this paper and the underlying database aim to bridge this gap.

In sum, the contribution is to bridge the Karas–Schoors identity/statement tradition with the ownership-graph toolkit and AML graph practice: we (i) expose a Neo4j/GDS model of banks and related entities that is consistent with beneficial-ownership standards, (ii) retain CBR line-item detail to reproduce or extend supervisory ratios, and (iii) enable presence/absence analyses---e.g., whether particular corporate configurations or network motifs co-occur with specific closure-reason tags—beyond the 1995–2003 window covered by the classic commercial panels.


## Data collection and processing {#sec-data-collection-processing}

As outlined in the simplified overview of the data collection and processing flow in @fig-flow, the process can be broadly divided into three stages: data acquisition, processing and integration, and graph construction and outputs. Below we describe each stage in detail: the data sources, the processing steps, and the integration methods.

::: {}

```{mermaid .landscape}
%%| fig-width: 40%
%%| fig-cap: "A directed acyclic graph (DAG) for the data collection and processing flow."
%%| label: fig-flow
%%{init: {
  "flowchart": {
    "htmlLabels": false,
    "nodeSpacing": 70,
    "rankSpacing": 80,
    "padding": 10,
    "useMaxWidth": false,
    "defaultRenderer": "elk" 
  },
  "themeVariables": {
    "fontFamily": "CMU Bright, DejaVu Sans, Arial, sans-serif"
  }
}}%%
%%| fig-width: 40%
%%| fig-cap: "A directed acyclic graph (DAG) for the data collection and processing flow."
%%| label: fig-flow
%%{init: {
  "flowchart": {
    "htmlLabels": false,
    "nodeSpacing": 70,
    "rankSpacing": 80,
    "padding": 10,
    "useMaxWidth": false,
    "defaultRenderer": "elk"   
  },
  "themeVariables": {
    "fontFamily": "CMU Bright, DejaVu Sans, Arial, sans-serif"
  }
}}%%
flowchart TB

  %% =========================
  %% DATA ACQUISITION
  %% =========================
  subgraph ACQ [Data acquisition]
    direction TB
    P0["CBR ownership PDFs"] -->|download| P1["OCR text"]
    P1 -->|ocr| P2["LLM JSON vX.Y"]
    P2 -->|extract to JSON| P3["Clean JSONL"]
    P3 -->|write JSONL| P4["neo_export.jsonl"]

    F0["CBR DBF forms 101/102/134"] -->|decode CP-1251| F1["UTF-8 Parquet"]
    F1 -->|convert to Parquet| F2["DuckDB views"]
    F2 -->|aggregate CAMEL| F3["CAMEL aggregations"]

    B0["Banki.ru pages"] -->|scrape active| B1["Active list JSONL"]
    B0 -->|scrape memory| B2["Memory book JSONL"]
    B1 -->|parse bank meta| B3["News items JSONL"]
    B2 -->|parse memory items| B3

    R0["Reputation.ru API"] -->|pull and flatten| R1["Flattened tables"]
  end

  %% =========================
  %% PROCESSING AND INTEGRATION
  %% =========================
  subgraph PROC [Processing and integration]
    direction TB
    P4 -->|merge on REGN/OGRN/INN| ER["Entity resolution via REGN/OGRN/INN/name"]
    F3 -->|join on REGN| ER
    B3 -->|link news to banks| ER
    R1 -->|enrich attributes| ER
    %% S1 -->|link firms to owners| ER
    ER -->|log matches and coverage| ERQ{"Quality control: match logs and coverage"}
  end

  %% =========================
  %% GRAPH AND OUTPUTS
  %% =========================
  subgraph OUT [Graph and outputs]
    direction TB
    ERQ -->|APOC import to Neo4j| G0["Neo4j Graph\nv0.x"]
    G0 -->|compute| G1["GDS metrics"]
    G0 -->|provide| G2["Cypher snippets"]
    G0 -->|export| G3["Descriptive outputs"]
    V0["Release notes"] -- hash or commit --> G0
  end

```

:::


### CBR ownership and control statements

Up until 2020, the Central Bank published tabular PDF statements of ownership and control of banks, which included information on the owners of banks, their shareholdings, and the relationships between them. Such a dataset is invaluable for enhancing our understanding of potential bank performance, as it provides a rich set of network features that have previously remained obscure and underexplored, barring a few mainly qualitative studies on the topic. An example such a statement is presented below in @fig-ownership-pdf-example: 

![An example page from the ownership statements published on the CBR website](./img/ownership_pdf_example.png){#fig-ownership-pdf-example}

Since the statements are mostly in a tabular format with an ownership network diagram at the end of each one, we used a combination of Optical Character Recognition (OCR) and Large Language Models (LLMs) to extract the interrelations from the pages. The PDFs were first processed using the [`Unstructured`](https://pypi.org/project/unstructured/) data extraction framework in Python [@Unstructured2025unstructured], then passed through to the LlamaParse [@meta_2025_llamaparse] and Gemini models for structured network-oriented output in the form of a JavaScript Object Notation (JSON) files. 

Both approaches were manually evaluated and compared [^eval], and the Gemini model was found to be more accurate in terms of extracting the interrelations. The LlamaParse model, while also effective, produced a higher number of false positives and negatives. The prompt in @lst-prompt-gemini was used to extract the interrelations from the PDF. 

[^eval]: The evaluation was performed on a random sample of 150 banks from the 2013-2020 ownership statements, with manual verification of the extracted relationships against the original PDF text.

:::{#lst-prompt-gemini lst-cap="Prompt for extracting interrelations from the CBR ownership statements using Gemini"}

```{.markdown}
Each row in the incoming request is a TSV file. The first column is the one representing the bank, not each row. 

The Bank is only represented by the bank_regn, it only appears in the first column, and each row contains one OWNERSHIP relationship with the stated bank_regn, ie. startNode is  `(:Person {full_name})-[:OWNERSHIP]->(:Bank {regn:XXX})` and the `Bank` is the `endNode`. The ONLY property of the `Bank` node is its `regn`, it is not stated in any of the rows, only in the first column of `bank_regn`, it does not name a `full_name`. Relationships in the interrelations column given the context and full names of the nodes (companies or people). 

If a property is not present for a certain node, do not include it in the JSON, for example, the `bank_regn` property is only present for a `:Bank` node, ogrn is only present for a `:Company` node. Discern family relationships if present and output all of them in English. For citizenship, use ISO 2-letter country codes. 

You need to make sure all organisations mentioned in the TSV are created as nodes in the graph and all of their relationships are extracted. If minority shareholders of any company or bank are mentioned, they should have their own node (with `full_name` "minority shareholders", in English) and relationships. "Sole participant" implies 100% ownership. 

Residence should be obtained from the TSV in the first instance. If no citizenship or residence is mentioned, it is null. 

"Not indicated" or similar expressions should be interpreted as null. 

The first node should always be the bank the regn mentioned in the first column. It does not have a full_name, so you should only give it an "Anonymous Bank" `full_name`.   
```

:::

The TSV format was chosen for its robustness in the face of potential errors with escaping commas in the text compared to CSV. A sample of the TSV file is presented in @tbl-sample-tsv-to-gemini, alongside an English translation. As we can observe, the formulaic language allows us to extract the interrelations with a high degree of accuracy, even though there might be some abbreviations of patronymics and company names.

As the resulting output still contained a number of nodes with abbreviated patronymics and company names, we had to clean the data further using another LLM, Google Gemini. Since the result of the model is heavily dependent on whether it is told to produce structured data, we also used a JSON schema to ensure the output is processed in the Neo4j graph database export/import format specified in the appendix @lst-gemini-schema.

Having iterated over the ownership statements for 2013-2020 [^cbr_ownership], we obtained a dataset with 147,278 edges and 35,000 nodes in a JSONL (JSON Lines) format, which was chosen for its compatibility with the existing Neo4j infrastructure and compactness; the dataset was then cleaned and imported into the Neo4j graph database using the following two queries in @lst-import-gemini-into-neo for nodes and relationships, respectively. 


[^cbr_ownership]: Ownership statements are only available for the years 2013-2020, unlike bank accounting data or company compliance data. 

### CBR accounting statements {#sec-cbr-accounting}

The CBR publishes a number of accounting statements for banks, including the balance sheet, profit and loss statement, and other financial indicators. These statements are available on [the CBR website](https://www.cbr.ru/banking_sector/otchetnost-kreditnykh-organizaciy/) in the DBF format encoded in the CP-1251 Cyrillic encoding for Windows. The DBF format is a binary format used by the dBase database management system, and it is not easily readable by most programming languages. Banks are uniquely identified by their Central Bank registration number, hereafter referred to as `REGN` or `regn`. To extract the data from the DBF files, we used the [`dbfread`](https://pypi.org/project/dbfread/) library in Python [@Ole2016dbfread] to read in the file, convert it to a Pandas DataFrame with a more widely supported UTF-8 encoding, and then dump it into an SQLite 3 database, a Python built-in. The resulting database was about 10 GiB in size and did not allow for easy querying even with proper indexing added for complex joins that are required for CAMEL indicators. We then made the decision to pivot to DuckDB which uses a familiar SQL syntax and is much more performant on complex joins and aggregations. The DuckDB compression algorithm also allowed us to reduce the size of the database to about 1.2 GiB and the queries returned results in a matter of seconds.

The dataset is constructed in two sequential stages. The first involves aggregating Forms 101 and 102 into a consistent set of balance-sheet and income-statement variables. The second applies imputation and reconciliation methods in order to obtain a monthly panel with full coverage. Both stages are deliberately transparent, with every adjustment logged and every filled value explicitly flagged.

#### Aggregation from CBR forms {#sec-cbr-aggregation}

Form 101 (balance sheet) is ingested as monthly parquet files and aggregated using DuckDB (see @lst-cbr-aggregation in the code Appendix). Assets are defined as A_P=1 and liabilities as A_P=2, with equity removed from liabilities and computed separately as the net of А-plan 102, 106, 107, and 108, minus 105, 109, and 111. This ensures that the accounting equation is preserved without mixing capital accounts into the liability base. The loan portfolio is split into state loans (441–444), retail loans (455 and 457), and corporate loans (the remaining 44x and 45x families used in the query). Non-performing loans are taken from families 458 and 459, and provisions are collected from 324%, 446%, and 455%. Deposits are defined broadly as 401–440 on the liability side, while liquid assets are grouped as 202, 301, and 302 on the asset side.

Form 102 (profit and loss) is read in dual-stack mode. Where modern codes are present, we take 10001–10004 for interest and operating income and expenses, and 61101–61102 for net income. Where they are absent, we reconstruct interest income from 11000, 111xx–116xx, and 121xx–123xx, and interest expense from 21000, 211xx–213xx, and 24101–24107. Operating components are backed out from totals 10000 and 20000, while code 35001 is included as a direct loss item if available. Net income therefore always has either a modern or a legacy source. Ratios such as ROA, ROE, and NIM are calculated only when the required inputs are present; missing values are left as nulls rather than forced. As a final step in this stage, we check the accounting identity row by row and report quantiles of any absolute gaps.
The output of aggregation is therefore a set of clean but incomplete series. Some banks report monthly flows, others quarterly, and many contain long gaps. To move from this irregular raw panel to a usable dataset, we apply imputation and reconciliation.

Summaries of missing values and zero values are available in Tables [-@tbl-missing-after-aggregation] and [-@tbl-zero-after-aggregation], respectively.

#### Imputation and reconciliation {#sec-cbr-imputation}

The imputation procedure has three parts: flows, stocks, and identities (see Appendix @lst-cbr-imputation for the relevant code listing).

Flows are first tested for “quarterly-like” behaviour. On a month-start grid, we identify series that have exactly one non-null per quarter and low density overall. Where a bank has no flows at all, we attempt a Form 102 bridge: quarterly totals are extracted directly from the raw 102 file and then disaggregated. The disaggregation uses Denton’s proportional benchmarking method, which preserves the path of an indicator such as total assets or deposits while ensuring that the sum of three months equals the observed quarterly total. Two modes are applied: overwrite, when the series is genuinely quarterly-like, and gap-filling, when the series is only partially missing. This is the same movement-preserving method used by statistical agencies for temporal disaggregation (Dagum and Cholette, 2006; Sax and Steiner, 2013). Net interest income is re-derived wherever both components are present. Each operation produces an audit line identifying the method, the number of months filled, and whether the bank was bridged from Form 102.

Stock variables are imputed by a structural state-space model when the time series is sufficiently informative, or otherwise by cubic interpolation confined to the observed support. The state-space specification is a local level with trend estimated by the Kalman filter, following standard treatments in time-series econometrics (Harvey, 1989; Durbin and Koopman, 2012). Imputed values are flagged, and for each bank the number of cells added is reported.

After flows and stocks are on a complete monthly grid, we reconcile them back to the accounting identities. Assets are projected to equal liabilities plus equity, and the sum of loan components is forced not to exceed the total. In most cases, proportional adjustments to liabilities and equity are sufficient. For the rare problematic case, we solve a small quadratic program to find the minimum-distance feasible vector. Reconciling after imputation avoids encoding gaps as spurious liabilities or equity.

Finally, ratios are recomputed using the imputed series, and a quality-control report is generated. This records the total number of rows, the number of identity violations, and the maximum absolute gap. The outputs include the completed panel in parquet format and an audit log of every filled cell. The complete list of aggregation codes and imputation methods is available in @tbl-aggregation-imputation. 

The two-stage process deliberately separates aggregation and imputation. Aggregation preserves the accounting definitions and avoids premature filling, leaving missing values as signals. Imputation then fills these gaps using methods widely accepted in official statistics and time-series analysis, with state-space models for stocks and Denton benchmarking for flows. By reconciling identities only after filling, and by logging every adjustment, the resulting panel remains both consistent and transparent, and can support replication and robustness checks.

The constructed indicators align comprehensively with the CAMEL (**C**apital adequacy, **A**sset quality, **M**anagement efficiency, **E**arnings, **L**iquidity) supervisory framework:

**C**apital Adequacy: Tier 1 capital ratios and leverage metrics directly assess capital strength relative to risk exposures and total assets, providing regulatory compliance indicators and buffer capacity measures.

**A**sset Quality: Non-performing loan ratios, provision coverage ratios, and loan loss provisions relative to total loans offer multiple perspectives on credit risk management and portfolio health.

**M**anagement Efficiency: Cost-to-income ratios, operating expense-to-asset ratios, and asset turnover metrics evaluate operational efficiency and management effectiveness in resource utilisation.

**E**arnings: Return on assets (ROA), return on equity (ROE), and net interest margin (NIM) provide comprehensive profitability assessment across different analytical perspectives.

**L**iquidity: Loan-to-deposit ratios, liquid assets-to-total assets ratios, and cash position metrics assess short-term financial flexibility and funding stability.


### CBR and Banki.ru licence revocation data {#sec-cbr-banki-revocations}

A list of banks registered in Russia is [published on the CBR website](https://www.cbr.ru/banking_sector/credit/), with one important caveat: it does not include older banks that were set up in the 1990s and whose licences have been revoked. This list therefore had to be cross-referenced with the data from [Banki.ru](https://banki.ru/) on two separate endpoints: the [list of currently active banks](https://www.banki.ru/banks/) and the so-called ['Banki.ru Memory Book'](http://www.banki.ru/banks/memory/), which does not seem to be available any longer. All three of these sources were scraped using the `Scrapy` framework [@2025scrapy], and the data was then cleaned and merged into a single dataset comprising the following columns: a bank's name, its registration number, the date of registration, the date of revocation of the banking licence (if present), and the reason for revocation. For Banki.ru, the news articles pertaining to each bank were also scraped along with their titles, links, and dates for further qualitative and quantitative analysis. They were then input into the Neo4j graph database with schema presented in  @lst-banki-schema.

The Banki.ru data were then merged immediately on the `regn` property and a `(:Bank)-[:HAS_NEWS]->(:News)` relationship was set as presented in @lst-banki-merge. 


### Reputation.ru data {#sec-reputation}


[Reputation.ru](https://reputation.ru/) is a Russian compliance and risk management platform that provides a variety of indicators from a diverse range of state agencies whose APIs are publicly available but rather cumbersome to deal with on their own. @tbl-reputation-json presents a detailed description of the data returned by the API and its typical values. The API returns a wealth of data aggregated over the entire lifetime of a company, such as the shareholder structure, the number of employees, the number of federal procurement contracts secured, the number of inspections carried out, and the number of legal cases in which the company has been involved as either a plaintiff or a defendant. This JSON response is then used to populate or enrich the graph database based on either the internal Reputation ID, the combination of the OGRN and INN identifiers, or the full name where none of the above is available.


## Postprocessing and data quality {#sec-postprocessing}

### Network metrics


The resulting graph database provides a fertile ground for exploring various centrality measures, such as degree, betweenness, and closeness centrality. These metrics can be calculated using the Neo4j Graph Data Science (GDS) library, which provides a suite of algorithms for analysing graph data. First, we create an in-memory projection of the graph with a Cypher query that includes the nodes and relationships of interest---in our case, the (`:Person`), (`:Company`), and (`:Bank`) nodes and the `:OWNERSHIP`, `:MANAGEMENT`, and `:FAMILY` relationships within 7 and 5 hops of a (`:Bank`) node, respectively. The query to make the projection is presented in @lst-neo-5-hop-projection, and the one to calculate and set the network metrics as node properties is shown in @lst-network-metrics. The subset of metrics we are interested in includes the following, as per @newman_Networks_2018 and @borgatti_CentralityNetworkFlow_2005:

1. **In-degree centrality**: The number of incoming relationships to a node, which can indicate the level of influence or importance of that node within the network.

2. **Out-degree centrality**: The number of outgoing relationships from a node, which can indicate the level of activity or engagement of that node within the network.

3. **Closeness centrality**: A measure of how close a node is to all other nodes in the network, which can indicate the efficiency of information flow from that node to others.

4. **Betweenness centrality**: A measure of how often a node acts as a bridge along the shortest path between two other nodes, which can indicate the level of control or influence that node has over the flow of information in the network.

5. **Eigenvector centrality**: A measure of a node's influence based on the number and quality of its connections, indicating its importance in the network.

6. **PageRank**: A measure of the importance of a node based on the number and quality of its incoming relationships, similar to Google's PageRank algorithm.

### Family ownership/management properties

Based on this graph structure, we have developed a set of metrics to quantify family ownership and control in banking networks. Our Cypher query computes these metrics for a specific bank identified by its registration number. Each component of the query's return statement corresponds to a distinct aspect of family ownership and control, as outlined in @lst-family-ownership-metrics, and the following sections presents the mathematical definitions of each metric.


#### Direct family ownership value

The direct family ownership value, denoted as $FOV_d(b)$ for a bank $b$, represents the total ownership value held by shareholders who are part of family networks. Mathematically, it is defined in @eq-family-ownership-value as:

$$
FOV_d(b) = \sum_{i \in D_b} \omega_i \cdot \mathbf{1}_{F}(i)
$${#eq-family-ownership-value}

Where:

- $D_b$ is the set of direct owners of bank $b$

- $\omega_i$ is the ownership value (the `FaceValue` property) held by owner $i$

- $\mathbf{1}_{F}(i)$ is an indicator function that equals 1 if owner $i$ has at least one family connection and 0 otherwise

This metric, represented as `direct_family_owned` in our query, quantifies the absolute magnitude of ownership concentrated in family-connected shareholders. As noted by Maury (2006), the magnitude of family ownership is positively associated with firm valuation in contexts with moderate shareholder protection, making this an important dimension of control.

#### Total ownership value

The total ownership value, denoted as $TOV(b)$ for a bank $b$, represents the sum of all direct ownership stakes in the bank. It is mathematically defined as:

$$
TOV(b) = \sum_{i \in D_b} \omega_i
$$

Where $D_b$ and $\omega_i$ are defined as above. This metric, represented as `total_direct_owned` in our query, provides the baseline against which family ownership concentration can be measured. Demsetz and Villalonga (2001) emphasise the importance of considering the total ownership structure when analysing corporate performance and governance.

#### Family ownership percentage

The family ownership percentage, denoted as $FOP(b)$ for a bank $b$, represents the proportion of total ownership that is held by family-connected shareholders. It is mathematically defined in @eq-family-ownership-percentage as:

$$
FOP(b) = \begin{cases}
\frac{FOV_d(b)}{TOV(b)} \times 100\%, & \text{if } TOV(b) > 0 \\
0, & \text{otherwise}
\end{cases}
$${#eq-family-ownership-percentage}

This normalised metric, calculated in our query using the expression `100.0 * direct_family_owned / total_direct_owned`, allows for comparative analysis across different banks regardless of their absolute size or capitalisation. @claessens_SeparationOwnershipControl_2000 utilise similar percentage-based measures to analyse the separation of ownership and control in East Asian corporations, demonstrating the value of such normalised metrics in cross-sectional analyses.

#### Direct owner count

The direct owner count, denoted as $|D_b|$ for a bank $b$, represents the total number of direct shareholders. This structural metric provides context for understanding ownership dispersion or concentration. @laporta_CorporateOwnershipWorld_1998 identify ownership concentration as a key dimension of corporate governance across different legal systems, with implications for investor protection and capital market development.

In our framework, represented as `direct_owner_count` in the query, this metric serves as a denominator for calculating relative measures of family influence. It also provides important context for interpreting other metrics, as the significance of family ownership may vary depending on whether ownership is widely dispersed or highly concentrated.

#### Total family connections

The total family connections, denoted as $|F_b|$ for a bank $b$, represents the count of family relationships among the direct owners of the bank. Mathematically, it is defined as:

$$
|F_b| = \sum_{i \in D_b} |N_F(i)|
$$

Where $N_F(i)$ represents the set of family members connected to owner $i$. This metric, represented as `total_family_connections` in our query, quantifies the density of family networks within the ownership structure.

@bertrand_MixingFamilyBusiness_2008 demonstrate in their study of Thai business groups that family networks can significantly influence business decisions and resource allocation, highlighting the importance of measuring family connection intensity. Our metric builds on this insight by explicitly quantifying the extent of family relationships within the ownership structure.

#### Family-controlled companies

The family-controlled companies metric, denoted as $|C_F(b)|$ for a bank $b$, represents the count of companies that are controlled by family members and have ownership stakes in the bank. In network terms, these are companies that lie on paths between family members and the bank, where the paths consist of multiple OWNERSHIP relationships. Mathematically, it is defined in @eq-family-controlled-companies as:

$$
|C_F(b)| = |\{c \in V \mid \exists f \in V, \exists p: f \xrightarrow{\text{`:OWNERSHIP`}^*} c \xrightarrow{\text{`:OWNERSHIP`}} b, \text{ and } \exists g: (f) \xrightarrow{\text{`:FAMILY`}} g\}|
$$ {#eq-family-controlled-companies}

Where $V$ is the set of all nodes in the graph, and $p$ represents a path of one or more `OWNERSHIP` relationships. This metric, represented as `family_controlled_companies` in our query, captures indirect family control through corporate structures.

@almeida_TheoryPyramidalOwnership_2006 develop a theoretical framework for analysing pyramidal ownership structures in family business groups, demonstrating how such structures can magnify family control beyond direct ownership stakes. Our metric operationalises this concept by explicitly identifying companies that serve as intermediaries for family control.

#### Family connection ratio

The family connection ratio, denoted as $\rho_F(b)$ for a bank $b$, represents the average number of family connections per direct owner. Mathematically, it is defined in @eq-family-connection-ratio as:

$$
\rho_F(b) = \begin{cases}
\frac{|F_b|}{|D_b|}, & \text{if } |D_b| > 0 \\
0, & \text{otherwise}
\end{cases}
$${#eq-family-connection-ratio}

Where $|F_b|$ and $|D_b|$ are defined as above. This normalised metric, calculated in our query using the expression `toFloat(total_family_connections) / direct_owner_count`, provides a measure of the relative intensity of family networks in the ownership structure.

@khanna_EstimatingPerformanceEffects_2001 emphasise the importance of network density in business groups, noting that denser networks facilitate information sharing and coordinated action. Our family connection ratio extends this concept to family networks specifically, providing a measure of how intensely family relationships permeate the ownership structure.

### Ownership complexity metrics


As outlined in @lst-complexity-metrics, we also calculate a proxy for the convolutedness of the ownership structure of a bank through the equation below (@eq-ownership-complexity).

$$
\begin{aligned} &\text{Given a directed graph } G = (V, E) \text{ where:} \\ &\quad V \text{ is the set of all entities (banks and owners)} \\ &\quad E \subseteq V \times V \text{ is the set of directed ownership relationships} \\ &\quad w: E \to \mathbb{R}^+ \text{ is a weight function representing ownership stakes} \\ \\ &\text{For a specific bank } b \in V \text{, define:} \\ &\quad P_b = \{p = (v_0, v_1, \ldots, v_k) : (v_{i-1}, v_i) \in E \text{ with OWNERSHIP type } \forall i \in \{1,\ldots,k\}, \\ &\quad \quad \quad \quad 1 \leq k \leq 5, \text{ and } v_k = b\} \\ \\ &\text{The complexity measures are defined as:} \\ &\quad U_b = |\{v_0 : \exists p = (v_0, v_1, \ldots, v_k) \in P_b\}| \quad \text{(Unique owners)} \\ &\quad L_b = \frac{1}{|P_b|} \sum_{p \in P_b} |p| \quad \text{(Average path length)} \\ &\quad T_b = |P_b| \quad \text{(Total paths)} \\ \\ &\text{The ownership complexity score is then:} \\ &\quad C_b = L_b \cdot \log_{10}(1 + U_b) \end{aligned} 
$$ {#eq-ownership-complexity}

This formula captures both the depth dimension through $L_b$ (vertical complexity through ownership chains) and the breadth dimension through $U_b$ (horizontal complexity from ownership dispersion), combined multiplicatively to reflect their interactive effect on overall ownership complexity.

### Foreign ownership metrics

$$
\begin{aligned}
& G = (V, E, \phi, \omega) \text{ where:} \\
& \quad V \text{ represents entities (banks, companies, individuals)} \\
& \quad E \subseteq V \times V \text{ represents ownership relationships} \\
& \quad \phi: V \to \{0,1\} \text{ indicates foreign (1) or domestic (0)} \\
& \quad \omega: E \to [0,1] \text{ is the ownership weight (graph property `Size`)}
\end{aligned}
$$

For a specific bank $b \in V$, we define the following sets and metrics as shown in @lst-foreign-ownership-metrics, and formalised in @eq-foreign-ownership-metrics. This formalisation captures multiple dimensions of foreign ownership and control in banking systems, aligning with established literature. First, the distinction between direct and indirect foreign ownership reflects what @claessens_SeparationOwnershipControl_2000 identify as the separation of cash flow rights from control rights in corporate governance structures. By capturing both direct stakes and indirect control through intermediate companies, we ensure that our metrics align with @almeida_TheoryPyramidalOwnership_2006 analysis of pyramidal ownership structures.

The foreign entity count ($FEC_d$) and foreign-controlled companies count ($FCC$) capture 'network embeddedness' of financial institutions in international ownership structures. These metrics quantify the breadth of foreign influence, analogous to degree centrality in network science [@freeman_CentralitySocialNetworks_1978a].

The percentage metrics ($FOP_d$ and $FOP_t$) normalise foreign ownership relative to total ownership, enabling cross-sectional comparisons similar to those conducted by @laporta_CorporateOwnershipWorld_1998 in their global analysis of corporate ownership patterns. Further, controlling for the number of foreign countries involved ($FCD$) allows us to assess the diversity of foreign ownership, which may act as a further protective characteristic for a bank's stability and longevity.

$$
\begin{aligned}
&\text{Direct Foreign Ownership Value:} \\
&FOV_d(b) = \sum_{v \in D_b} \phi(v) \cdot \omega(v, b) \\
\\
&\text{Foreign Direct Ownership Percentage:} \\
&FOP_d(b) = \begin{cases}
\frac{FOV_d(b)}{TOV_d(b)} \times 100\%, & \text{if } TOV_d(b) > 0 \\
0, & \text{otherwise}
\end{cases} \\
\\
&\text{Foreign Entity Direct Count:} \\
&FEC_d(b) = \sum_{v \in D_b} \phi(v) \\
\\
&\text{Indirect Foreign Control:} \\
&\text{Let } P_b = \{(f,c,b) : f,c \in V, (f,c) \in E, (c,b) \in E, \phi(f) = 1, c \notin D_b\} \\
&\text{where } f \text{ is a foreign entity, } c \text{ is an intermediate company} \\
\\
&\text{Foreign-Controlled Companies Count:} \\
&FCC(b) = |\{c \in V : \exists f \in V, (f,c,b) \in P_b\}| \\
\\
&\text{Indirect Foreign Ownership Value:} \\
&FOV_i(b) = \sum_{(f,c,b) \in P_b} \omega(c,b) \\
\\
&\text{Total Foreign Ownership Value:} \\
&FOV_t(b) = FOV_d(b) + FOV_i(b) \\
\\
&\text{Total Foreign Ownership Percentage:} \\
&FOP_t(b) = \begin{cases}
\frac{FOV_t(b)}{TOV_d(b)} \times 100\%, & \text{if } TOV_d(b) > 0 \\
0, & \text{otherwise}
\end{cases} \\
\end{aligned} 
$${#eq-foreign-ownership-metrics}


## Descriptive statistics {#sec-descriptive-statistics}

The following section of the paper presents summary statistics of the Neo4j graph database, including the distribution of node types, relationship types, and various network metrics calculated using the Neo4j Graph Data Science (GDS) library. Separately, we also inspect the post-imputation distributions of accounting indicators from the CBR bank statements dataset.

### Database statistics {#sec-database-statistics}

```{python}
#| include: false
#| echo: false
```

::: {.smaller}
```{python #neo4j-statistics-compute}
#| include: true
#| echo: false
#| tbl-cap: "Summary statistics for the Neo4j database"  
#| label: neo4j-statistics-compute

node_stats_df = gds.run_cypher(
'''
MATCH (n) 
WITH labels(n) as labels, size(keys(n)) as props, COUNT{(n)--()} as degree
RETURN
DISTINCT labels as `Labels`,
count(*) AS `# Nodes`,
avg(props) AS `Mean # of properties per node`,
min(props) AS `Min # of properties per node`,
max(props) AS `Max # of properties per node`,

avg(degree) AS `Mean # of relationships`,
min(degree) AS `Min # of relationships`,
max(degree) AS `Max # of relationships`
'''
)
# round the values to 2 decimal places, add column %
node_stats_df = node_stats_df.round(2)
node_stats_df["% of nodes"] = (
    node_stats_df["# Nodes"] / node_stats_df["# Nodes"].sum()
) * 100
node_stats_df["% of nodes"] = node_stats_df["% of nodes"].round(2)
# reorder columns
node_stats_df = node_stats_df[
    [
        "Labels",
        "# Nodes",
        "% of nodes",
        "Mean # of properties per node",
        # "Min # of properties per node",
        "Max # of properties per node",
        "Mean # of relationships",
        # "Min # of relationships",
        "Max # of relationships",
    ]
]
# sort by # Nodes
# Remove Ent from the labels, make it a string
node_stats_df.Labels = node_stats_df.Labels.apply(lambda x: ', '.join(x).replace('Ent, ', ''))
node_stats_df = node_stats_df.sort_values("# Nodes", ascending=False)
# Markdown
node_stats_df = node_stats_df.reset_index(drop=True)
# convert to markdown
# node_stats_df.loc['Total']= node_stats_df.sum()
total_nodes = node_stats_df['# Nodes'].sum()
node_stats_df = node_stats_df.to_markdown(
    index=False,
    tablefmt="pipe",
    floatfmt=",.2f",
    stralign="left",
    numalign="right")
```

:::

```{python}
#| include: false
#| echo: false
#| fig-cap: "Distribution of relationships in the Neo4j database"
#| fig-label: fig-neo4j-relationships

import cairosvg as cairo

db_stats_df = gds.run_cypher(
    '''
    CALL apoc.meta.stats()
    '''
)
rel_count = db_stats_df['relCount'].iloc[0]
rel_counts = pd.json_normalize(db_stats_df['relTypesCount'][0]).transpose().reset_index()
rel_counts.columns =['Relationship type', '# Relationships']
# drop some values from rel types
rel_counts_small = rel_counts[~rel_counts['Relationship type'].isin(['OWNERSHIP', 'MANAGEMENT', 'SIGNIFICANT_INFLUENCE', 'HAS_NEWS', 'FAMILY', 'GROUP', 'DIRECTorship', 'ELECTED', "CUSTODY", 'BENEFICIAL_OWNER'])]
rel_counts_large = rel_counts[rel_counts['Relationship type'].isin(['OWNERSHIP', 'MANAGEMENT', 'SIGNIFICANT_INFLUENCE', 'HAS_NEWS', 'FAMILY', 'GROUP', ])]
# sort by # Relationships
rel_counts_small = rel_counts_small.sort_values("# Relationships", ascending=True)
rel_counts_large = rel_counts_large.sort_values("# Relationships", ascending=True)
from lets_plot import * 
LetsPlot.setup_html()
lower_counts_bar_chart = (
    ggplot(rel_counts_small, aes(x='Relationship type', y='# Relationships', fill='# Relationships'))
    + geom_bar(stat='identity') 
    + coord_flip() 
    + scale_fill_gradient(low='lightblue', high='darkblue') 
    + labs(title='Relationship counts', x='', y='# Relationships (log scale)') 
    + theme(axis_text_x=element_text(angle=90)) 
    + ggtitle('Distribution of relationships with lower counts') 
    + theme_minimal() 
    + ggsize(1200, 600) 
    + theme(legend_position=[0.8,0.2])
)
higher_counts_bar_chart = (
    ggplot(rel_counts_large, aes(x='Relationship type', y='# Relationships', fill='# Relationships'))
    + geom_bar(stat='identity') 
    + coord_flip() 
    + scale_fill_gradient(low='lightblue', high='darkblue') 
    + labs(title='Relationship counts', x='', y='# Relationships (log scale)') 
    + theme(axis_text_x=element_text(angle=90)) 
    + ggtitle('Distribution of relationships with higher counts') 
    + theme_minimal() 
    + ggsize(1200, 600) 
    + theme(legend_position=[0.8,0.2])
)
# plot_svg = (
#     gggrid([higher_counts_bar_chart, lower_counts_bar_chart], ncol=1)
#     # .ggsize(1200, 600)
#     .to_pdf('figures/neo4j_relationships.pdf')
# )

higher_counts_bar_chart.to_svg('figures/neo4j_relationships_high.svg')
lower_counts_bar_chart.to_svg('figures/neo4j_relationships_low.svg')

```

As shown in @tbl-neo4j-statistics, the Neo4j database contains a total of `{python} "{:,.0f}".format(total_nodes)` nodes and `{python} "{:,.0f}".format(rel_count)` relationships, and the most common node types are `Person`, `Company`, and `Bank`, with a few special labels reserved for government entities, foreign companies, the Deposit Insurance Agency (`:DepositInsurance`), and the Central Bank of Russia (`:CentralBank`). Foreign government entities are a mixture of (`:Country`) and (`:Government`) labels, with the possible addition of either (`:Company`) or (`:ForeignCompany`) labels. 

::: {.landscape #fig-neo4j-relationships label=fig-neo4j-relationships}

![](figures/neo4j_relationships_high.svg)

![](figures/neo4j_relationships_low.svg)

: Distribution of relationships in the Neo4j database

:::

::: {.smaller}

```{python}
#| include: true
#| echo: false
#| tbl-cap: "Summary statistics for the Neo4j database"
#| label: tbl-neo4j-statistics
Markdown(node_stats_df)
```
:::


### Network metrics {#sec-network-metrics}

Whenever working with a graph database, it is advisable to use an in-memory projection to speed up computation and work only on the subgraph of interest. In a similar fashion to the query in @lst-neo-5-hop-projection, we created a 7-hop undirected projection of the graph with the non-isolate `:Bank` nodes as the starting point. This projection was then used to calculate the clustering coefficient and the number of triangles for each type of node in the graph. The clustering coefficient is defined as the ratio of the number of edges between nodes in a cluster to the number of edges that could possibly exist between those nodes. 

::: {.smaller .landscape}
```{python}
#| include: true
#| echo: false
#| output: asis
#| tbl-cap: "Clustering coefficients and triangles in the Neo4j database"
#| label: tbl-clustering-coefficient

clustering_df = gds.run_cypher(
    '''MATCH (n)
WHERE n.clustering_coefficient_7hop IS NOT NULL and not 'Trust' in labels(n)
RETURN 
  labels(n) AS node_type,
  COUNT(n) AS count,
  AVG(n.clustering_coefficient_7hop) AS avg_clustering,
  MIN(n.clustering_coefficient_7hop) AS min_clustering,
  MAX(n.clustering_coefficient_7hop) AS max_clustering, 
  AVG(n.harmonic_centrality) AS avg_harmonic_centrality,
  MIN(n.harmonic_centrality) AS min_harmonic_centrality,
  MAX(n.harmonic_centrality) AS max_harmonic_centrality,
  avg(n.triangles) AS avg_triangles,
    min(n.triangles) AS min_triangles,
    max(n.triangles) AS max_triangles
ORDER BY count(n) DESC;
'''
)
clustering_df.node_type = clustering_df.node_type.apply(lambda x: ', '.join(x).replace('Ent, ', ''))
# harmonic_centrality cols are in scientific notation with e    
# capture raw harmonic centrality values for prose (so we don't inherit the LaTeX-formatted strings)
hc_raw = clustering_df["avg_harmonic_centrality"].copy()

def format_sci_latex(x):
    if pd.isna(x):
        return ""
    base, exponent = f"{x:.2e}".split("e")
    return r"$" + base + r" \times 10^{" + str(int(exponent)) + r"}$"


# rename the columns
clustering_df.columns = [
    "Node type",
    "# Nodes",
    "Avg. clustering",
    "Min. clustering",
    "Max. clustering",
    "Avg. harmonic centrality",
    "Min. harmonic centrality",
    "Max. harmonic centrality",
    "Avg. triangles",
    "Min. triangles",
    "Max. triangles",
]

cols_sci = [
    "Avg. harmonic centrality",
    "Min. harmonic centrality",
    "Max. harmonic centrality",
]

for col in cols_sci:
    clustering_df[col] = clustering_df[col].apply(format_sci_latex)

# vars necessary for interpolation, with rounding to 2 decimal places or as latex strings
company_clustering = clustering_df['Avg. clustering'].iloc[0]
bank_clustering = clustering_df['Avg. clustering'].iloc[1]

# --- dicts for values ---

def pick(node_type, col):
    v = clustering_df.loc[clustering_df["Node type"] == node_type, col]
    return f"{v.iloc[0]:.2f}" if len(v) else "n/a"

clustering_values = {
    "person": pick("Person", "Avg. clustering"),
    "company": pick("Company", "Avg. clustering"),
    "bank_company": pick("Bank, Company", "Avg. clustering"),
    "bank_company_foreign": pick("Bank, Company, ForeignCompany", "Avg. clustering"),
    "country_government": pick("Country, Government", "Avg. clustering"),
    "company_foreign": pick("Company, ForeignCompany", "Avg. clustering"),
    "government_municipal": pick("Government, MunicipalSubject", "Avg. clustering"),
    "bank_company_country_government_foreign": pick("Bank, Company, Country, Government, ForeignCompany", "Avg. clustering"),
    "company_government_centralbank": pick("Company, Government, CentralBank", "Avg. clustering"),
    "company_country_government_statepropmgmt": pick("Company, Country, Government, StatePropMgmt", "Avg. clustering"),
}

avg_triangles = {
    "person": pick("Person", "Avg. triangles"),
    "company": pick("Company", "Avg. triangles"),
    "bank_company": pick("Bank, Company", "Avg. triangles"),
    "bank_company_foreign": pick("Bank, Company, ForeignCompany", "Avg. triangles"),
    "country_government": pick("Country, Government", "Avg. triangles"),
    "company_foreign": pick("Company, ForeignCompany", "Avg. triangles"),
    "government_municipal": pick("Government, Municipal-Subject", "Avg. triangles"),
    "bank_company_country_government_foreign": pick("Bank, Company, Country, Government, ForeignCompany", "Avg. triangles"),
    "company_government_centralbank": pick("Company, Government, CentralBank", "Avg. triangles"),
    "company_country_government_statepropmgmt": pick("Company, Country, Government, StatePropMgmt", "Avg. triangles"),
}

avg_harmonic = {
    "person": hc_raw[clustering_df["Node type"] == "Person"].values[0] if len(hc_raw[clustering_df["Node type"] == "Person"]) else None,
    "company": hc_raw[clustering_df["Node type"] == "Company"].values[0] if len(hc_raw[clustering_df["Node type"] == "Company"]) else None,
    "bank_company": hc_raw[clustering_df["Node type"] == "Bank, Company"].values[0] if len(hc_raw[clustering_df["Node type"] == "Bank, Company"]) else None,
    "bank_company_foreign": hc_raw[clustering_df["Node type"] == "Bank, Company, ForeignCompany"].values[0] if len(hc_raw[clustering_df["Node type"] == "Bank, Company, ForeignCompany"]) else None,
    "country_government": hc_raw[clustering_df["Node type"] == "Country, Government"].values[0] if len(hc_raw[clustering_df["Node type"] == "Country, Government"]) else None,
    "company_foreign": hc_raw[clustering_df["Node type"] == "Company, ForeignCompany"].values[0] if len(hc_raw[clustering_df["Node type"] == "Company, ForeignCompany"]) else None,
    "government_municipal": hc_raw[clustering_df["Node type"] == "Government, MunicipalSubject"].values[0] if len(hc_raw[clustering_df["Node type"] == "Government, MunicipalSubject"]) else None,
    "bank_company_country_government_foreign": hc_raw[clustering_df["Node type"] == "Bank, Company, Country, Government, ForeignCompany"].values[0] if len(hc_raw[clustering_df["Node type"] == "Bank, Company, Country, Government, ForeignCompany"]) else None,
    "company_government_centralbank": hc_raw[clustering_df["Node type"] == "Company, Government, CentralBank"].values[0] if len(hc_raw[clustering_df["Node type"] == "Company, Government, CentralBank"]) else None,
    "company_country_government_statepropmgmt": hc_raw[clustering_df["Node type"] == "Company, Country, Government, StatePropMgmt"].values[0] if len(hc_raw[clustering_df["Node type"] == "Company, Country, Government, StatePropMgmt"]) else None,
}

def fmt_harmonic_sci_inline_text(x):
    if x is None or pd.isna(x):
        return "n/a"
    base, exponent = f"{x:.2e}".split("e")
    return float(base), int(exponent)


harmonic_values_typst = {
    k: fmt_harmonic_sci_inline_text(v) for k, v in avg_harmonic.items()
}


clustering_df.fillna('n/a', inplace=True)

clustering_df_render = clustering_df.to_markdown(
    index=False,
    floatfmt=",.2f",
    stralign="left",
    numalign="right")
    
Markdown(clustering_df_render)

```

:::


As can be observed in @tbl-clustering-coefficient, the clustering coefficient and triangle counts vary across multi-label node types. Key observations:

1. `:Bank, :Company` nodes exhibit a moderate clustering of `{python} clustering_values['bank_company']` and the highest average triangle count among the large categories at `{python} avg_triangles['bank_company']`, consistent with banks frequently sitting in densely inter-owned corporate neighbourhoods.

2. `:Company, :ForeignCompany` nodes show high local clustering at `{python} clustering_values['company_foreign']` but only modest triangles at `{python} avg_triangles['company_foreign']`. This suggests that, when present, foreign-incorporated companies sit in tight local clusters, though sample size is small ($n=7$). [^small_sample]

3. Plain `:Company` nodes have lower clustering at `{python} clustering_values['company']` with triangle counts at `{python} avg_triangles['company']` comparable to foreign-company combinations, indicating broader but less tightly knit corporate neighbourhoods.

4. `:Government:MunicipalSubject` nodes have clustering at `{python} clustering_values['government_municipal']` and triangles at `{python} avg_triangles['government_municipal']`, implying moderate local closure where municipal ownership is involved.

5. The exceptional hub is the Central Bank combination (`:Company, :Government, :CentralBank`), which couples moderate clustering at `{python} clustering_values['company_government_centralbank']` with very high triangles at `{python} avg_triangles['company_government_centralbank']`, reflecting its role as a regulatory nexus connecting otherwise separate segments.

[^small_sample]: Note that values for rare label sets (e.g., `:CentralBank`, `:StatePropMgmt`) should be interpreted cautiously due to small counts.

Due to prohibitive computational costs of running shortest path algorithms on all pairs of nodes in the 7-hop subgraph containing $\approx 44000$ nodes, we chose instead to compute harmonic centrality as a proxy for average shortest path length, a measure of how close a node is to all other nodes in the network, defined as the sum of the inverse distances from the node to all other nodes in [@eq-harmonic-centrality].

$$\text{Harmonic Centrality}(v) = \sum_{u \in V \setminus \{v\}} \frac{1}{d(v,u)}$${#eq-harmonic-centrality}

We prefer harmonic centrality because the projection is sparse and partially disconnected; harmonic yields finite values without requiring full all-pairs shortest paths. The main findings from the summary statistics on harmonic centrality are as follows:

1. `:Company` nodes show relatively high average harmonic centrality (`{python} harmonic_values_typst['company'][0]` $\times 10^{ `{python} harmonic_values_typst['company'][1]` }$) but relatively low clustering at `{python} clustering_values['company']`, indicating that they often act as intermediary bridges across the network.

2. `:Bank` (i.e., `:Bank:Company`) nodes display the highest average harmonic centrality among the large categories at `{python} harmonic_values_typst['bank_company'][0]` $\times 10^{ `{python} harmonic_values_typst['bank_company'][1]` }$, combined with low clustering of `{python} clustering_values['bank_company']`, consistent with hub-like, spoke-and-wheel positioning.

3. `:Bank:ForeignCompany`[^multiple_labels] nodes have lower average harmonic centrality than other bank-related label sets (`{python} harmonic_values_typst['bank_company_foreign'][0]` $\times 10^{ `{python} harmonic_values_typst['bank_company_foreign'][1]` }$) despite a relatively higher clustering of `{python} clustering_values['bank_company_foreign']`, suggesting enclave-like cohesion with weaker integration into the broader network.

4. The Central Bank composite (`:Company:Government:CentralBank`) exhibits average harmonic centrality of `{python} harmonic_values_typst['company_government_centralbank'][0]` $\times 10^{ `{python} harmonic_values_typst['company_government_centralbank'][1]` }$ with a very high triangle count of `{python} avg_triangles['company_government_centralbank']`, underscoring a regulatory nexus that connects otherwise separate segments.

5. State-linked composites such as `:Company:Country:Government:StatePropMgmt` show low harmonic centrality (`{python} harmonic_values_typst['company_country_government_statepropmgmt'][0]` $\times 10^{ `{python} harmonic_values_typst['company_country_government_statepropmgmt'][1]` }$) and only `{python} avg_triangles['company_country_government_statepropmgmt']` triangles; interpret cautiously due to tiny $n$.

[^multiple_labels]: The use of multiple labels---for example, `:Bank:ForeignCompany`---reflects the underlying semantics of the data. In the Central Bank of Russia registers as well as in [Reputation.ru](https://reputation.ru/), entities can simultaneously be banks and foreign-incorporated companies. Preserving both labels in Neo4j facilitates filtering by functional type (bank versus non-bank) while still retaining the jurisdictional or ownership attributes implied by :ForeignCompany. This dual labelling avoids the need for artificial disaggregation and simplifies queries across categories of interest and conforms to Neo4j graph modelling best practices [@neo4j_GraphModelingGuidelines_2017].


### CBR accounting statistics {#sec-cbr-summary}

![Density plots for raw accounting stocks from the CBR forms](figures/grid_density_amounts_page1.svg){#fig-density-stocks}

The credit stocks in @fig-density-stocks exhibit a clear point mass at zero (banks/months with no book value reported) plus a right-shifted mode for active observations. Company and retail loans are bimodal in signed-log space: a narrow spike around 0, and a broad hump centred in the mid-teens, with a long upper tail—consistent with many small banks and a thin stratum of very large lenders. Loss provisions share that pattern but are slightly more right-skewed relative to loans, implying heavier tails in provisioning than in gross lending. NPL balances look smoother and more unimodal, centred below the loan modes, which is what we would expect if problem assets scale with book but have tighter dispersion.

Balance-sheet aggregates behave as a scale family: assets and liabilities form a tight peak in the high signed-log range with long but thin right tails; equity is narrower and left-shifted (smaller magnitude, higher kurtosis), while total loans sit just to the left of assets/liabilities, as expected if loans dominate but do not exhaust assets. 


![Density plots for raw accounting flows from the CBR forms (cont.)](figures/grid_density_amounts_page2.svg){#fig-density-flows}

Interest income and expense in @fig-density-flows are sharply peaked, near-symmetric on the signed-log scale, with modest right tails; their concentration suggests stable monthly accruals once banks are active. Net interest income is even tighter (income and expense move in tandem), whereas net income shows a mixture: a dominant positive mode and visible negative mass, producing a left tail—exactly what one expects around stress periods and write-downs. Operating income/expense echo the interest panels but with slightly fatter right tails, reflecting fee/other income heterogeneity across banks.

Deposits display a broad, unimodal hump just left of loans, while liquid assets are distinctly bimodal: a hard spike near zero (bank-months with negligible liquidity) and a main mass around the low-teens in signed-log space. That split is informative, suggesting a subset of observations with structurally lean liquidity buffers.


![Density plots for percentage indicators from the CBR forms](figures/grid_density_percents_page1.svg){#fig-density-percents}

Net interest margin ($\text{NIM}$) in @fig-density-percents has a compact core around small positive values with a long, thinning right tail; the density declines roughly monotonically beyond $1–1.5 \text{pp}$ and extends out to $\approx 4 \text{pp}$. There is also a thin left tail below zero. The log-scaled y-axis makes clear that extremes are rare; the shaded banded background (as drawn) usefully frames the plotting window for typical values and outliers. Because the ratio is derived only when inputs exist, the absence of multi-modal artefacts here is reassuring. Returns on assets ($\text{ROA}$) are more skewed: a prominent spike just above zero, a long right tail (positive profitability months), and a pronounced left tail into losses. The left tail contains several narrow local spikes (bank-month clusters), which is what one expects from episodic provisioning or resolution events hitting multiple banks at once.

![Density plots for derived accounting ratios from the CBR forms. _**Note:**_ scales are inverted](figures/grid_density_ratios_page1.svg){#fig-density-ratios}

Looking at @fig-density-ratios with inverted scale, all four ratios are heavily right-tailed. Coverage (provisions/NPL) decays steeply from a dense mass at low values and exhibits extreme outliers at very high multiples, consistent with periods where provisions overshoot measured NPLs (data timing, policy overlays, or legacy clean-ups). ${LLP} \div {Loans}$ ratio shows a similar monotone decay with gentle shoulders near $15–25%$, then sparse mass out to very high values; the bulk lies at single-digit percentages. NPL ratio concentrates near the low single digits and declines smoothly, with a thin rim of very high values at the far right, again pointing to stress episodes rather than steady-state banking. ${Loans} \div {Deposits}$ cluster tightly near unity with a sharp left shoulder (loan-light balance sheets) and a long right tail above 1 (loan-heavy balance sheets funded beyond deposits). The oscillations in the far tail of several panels simply demonstrate KDE on very sparse support (few observations at extreme values, but a dense core).

<!-- ## Historical timeline of the governors of the Bank of Russia

### Timeline of the governors of the Bank of Russia

```{=mermaid}

```

```{mermaid}
%%| fig-width: screen
%%| out-width: 100%
%%| label: fig-bank-governor-timeline
%%| fig-cap: "Timeline of the governors of the Bank of Russia (1992–2025)"
---
config:
  theme: neo-dark
  layout: elk
---
gantt
    dateFormat  YYYY-MM-DD
    axisFormat  %Y

    section Governors
    Georgy Matyukhin — Chairman                  :matyukhin, 1992-01-27, 1992-06-16
    Victor Gerashchenko — Acting Chairman      :gerash_acting, 1992-07-01, 1992-11-04
    Victor Gerashchenko — Chairman             :gerash_full, 1992-11-04, 1994-10-18
    Tatyana Paramonova — Acting Chairwoman     :paramonova, 1994-10-19, 1995-10-22
    Alexander Khandruyev — Temporary Acting Chairman :khandruyev, 1995-11-08, 1995-11-22
    Sergey Dubinin — Chairman                 :dubinin, 1995-11-22, 1998-09-11
    Victor Gerashchenko — Chairman             :gerash_return, 1998-09-11, 2002-03-20
    Sergey Ignatyev — Chairman                 :ignatyev, 2002-03-20, 2013-06-23
    Elvira Nabiullina — Chairwoman             :nabiullina, 2013-06-24, 2025-12-31
```


The timeline of the governors of the Bank of Russia is shown in @fig-bank-governor-timeline. 



{{< pagebreak >}} -->

## Conclusion {.unnumbered}

This paper has presented the construction of a Neo4j graph database of the Russian banking system, integrating ownership and control statements from the Central Bank, financial and accounting data, licence revocation records, [Banki.ru](https://banki.ru/) archives, and compliance information from [Reputation.ru](https://reputation.ru/). Using a combination of OCR, large language models, and post-processing pipelines, we converted heterogeneous and partially unstructured sources into a unified graph format with more than 61,000 nodes and 114,000 relationships.

The resulting resource offers several advantages. First, it enables the study of ownership structures and control chains in the Russian banking system at a level of granularity that was previously inaccessible. Second, it links ownership and relational data to detailed financial indicators, allowing researchers to explore connections between network structure and bank performance. Finally, the graph format facilitates a wide variety of queries and analytical techniques, from simple path searches to advanced network metrics available through the Neo4j Graph Data Science library.

Preliminary descriptives already illustrate the scope and structure of the resource: the current release comprises 61,713 nodes and 114,954 relationships; banks (the multi-label `:Bank, :Company` set) show low clustering ($0.01$) yet the highest harmonic centrality among large categories ($8.45 × 10^{-4}$), plain companies exhibit 0.06 clustering and $3.05 × 10^{-4}$ harmonic centrality, foreign-company combinations (`:Company, :ForeignCompany`) display high local closure ($0.45$) but only $1.29$ triangles on average, and the Central Bank composite (`:Company, :Government, :CentralBank`) couples moderate clustering (0.05) with an extreme triangle count (10). Taken together, these patterns are consistent with hub-and-spoke positioning of banks, enclave-like foreign clusters, and a regulatory nexus centred on the Central Bank—stylised facts we will augment, in future revisions, with accounting-panel summary statistics and preliminary links between network structure and bank outcomes.

Looking forward, the database provides a foundation for a broad research agenda. Future work will apply this resource to examine the role of families in bank ownership, the influence of state actors and regulatory bodies, and the impact of ownership complexity on bank stability. In addition, continued development will involve extending the temporal coverage, incorporating new sources as they become available, and improving the accuracy of entity resolution.

By documenting the data sources, processing pipeline, and structure of this graph database, this paper contributes a replicable and extensible resource for the study of Russian banking. We hope it will enable both qualitative and quantitative researchers to engage with questions of ownership, control, and financial stability in new ways.

{{< pagebreak >}}


<!-- typst  snippet to start numebring appendices with A, B, ... -->

```{=typst}

#let appendix(body) = {
  set heading(numbering: "A1", supplement: [Appendix])
  counter(heading).update(0)
  body
}

#show: appendix

```

## Appendix: tables {.appendix}

### CBR ownership statements {.appendix}


`#pagebreak()`{=typst}

:::{.landscape}
`#show figure: set block(breakable: true)`{=typst}

::: {.landscape .smaller #tbl-sample-tsv-to-gemini tbl-colwidths="[10,10,10,70]"}

| bank_regn | full_name | ... | interrelations |
|-----------|-----------|-----|----------------|
| 1896 | Каледин Александр Александрович | ... | Физическое лицо Каледин Александр Александрович является лицом, под значительным влиянием которого в соответствии с критериями МСФО (IAS) 28 находится банк. Куницин Павел Геннадьевич является сыном Куницина Геннадия Николаевича Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Куницин Геннадий Николаевич является отцом Куницина Павла Геннадьевича Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Куницин Г.Н. осуществляет функции единоличного исполнительного органа АО «АННА И К», Куницину П.Г. принадлежит 57,62% голосов к общему количеству голосующих акций АО «АННА И К», Куницину Г.Н. принадлежит 38,08% голосов к общему количеству голосующих акций АО «АННА И К» Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Мельников Алексей Александрович является сыном Мельниковой Натальи Сергеевны |
| 1896 | Куницин Павел Геннадьевич | ... | Куницин Павел Геннадьевич является сыном Куницина Геннадия Николаевича Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Мельников Алексей Александрович является сыном Мельниковой Натальи Сергеевны |
| 1896 | Куницин Геннадий Николаевич | ... | Куницин Геннадий Николаевич является отцом Куницина Павла Геннадьевича Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Куницин Г.Н. осуществляет функции единоличного исполнительного органа АО «АННА И К», Куницину П.Г. принадлежит 57,62% голосов к общему количеству голосующих акций АО «АННА И К», Куницину Г.Н. принадлежит 38,08% голосов к общему количеству голосующих акций АО «АННА И К» Куницин П.Г., Куницин Г.Н. и АО «АННА И К» образуют группу лиц Мельников Алексей Александрович является сыном Мельниковой Натальи Сергеевны |
| 1896 | Kaledin Alexander Alexandrovich | ... | The natural person Kaledin Alexander Alexandrovich is a person under whose significant influence the bank is according to IFRS (IAS) 28 criteria. Kunitsyn Pavel Gennadyevich is the son of Kunitsyn Gennady Nikolaevich. Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Kunitsyn Gennady Nikolaevich is the father of Kunitsyn Pavel Gennadyevich. Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Kunitsyn G.N. performs the functions of sole executive body of JSC "ANNA I K", Kunitsyn P.G. owns 57.62% of votes to the total number of voting shares of JSC "ANNA I K", Kunitsyn G.N. owns 38.08% of votes to the total number of voting shares of JSC "ANNA I K". Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Melnikov Alexey Alexandrovich is the son of Melnikova Natalia Sergeevna |
| 1896 | Kunitsyn Pavel Gennadyevich | ... | Kunitsyn Pavel Gennadyevich is the son of Kunitsyn Gennady Nikolaevich. Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Melnikov Alexey Alexandrovich is the son of Melnikova Natalia Sergeevna |
| 1896 | Kunitsyn Gennady Nikolaevich | ... | Kunitsyn Gennady Nikolaevich is the father of Kunitsyn Pavel Gennadyevich. Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Kunitsyn G.N. performs the functions of sole executive body of JSC "ANNA I K", Kunitsyn P.G. owns 57.62% of votes to the total number of voting shares of JSC "ANNA I K", Kunitsyn G.N. owns 38.08% of votes to the total number of voting shares of JSC "ANNA I K". Kunitsyn P.G., Kunitsyn G.N. and JSC "ANNA I K" form a group of persons. Melnikov Alexey Alexandrovich is the son of Melnikova Natalia Sergeevna |


:A sample TSV table provided to Gemini for processing into Neo4j-like structured output in Russian and English (below). 

:::
:::

{{< pagebreak >}}

### CBR accounting statements {.appendix}


::: { .smaller #tbl-aggregation-imputation tbl-colwidths="[24, 33, 33]"}

| Variable family                                                                                                              | Aggregation rule (Forms 101/102)                                                                        | Imputation strategy                                                                                                        |
|:---------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| Assets, liabilities, equity                                                                                                  | Assets = A_P=1; liabilities = A_P=2 excluding equity; equity = (А-plan 102, 106, 107, 108) − (105, 109, 111) | Structural state-space model if data sufficient; cubic interpolation otherwise; post-fill reconciliation to ensure A = L+E |
| Deposits                                                                                                                     | Liabilities families 401–440                                                                            | State-space or cubic fill, reconciled                                                                                      |
| Liquid assets                                                                                                                | Asset families 202, 301, 302                                                                            | State-space or cubic fill                                                                                                  |
| Loan totals and splits                                                                                                       | Loans = 44xxx–47xxx; state = 441–444; retail = 455, 457; corporate = remaining families                 | State-space or cubic fill for totals; proportional reconciliation across components                                        |
| Non-performing loans                                                                                                         | Families 458, 459                                                                                       | State-space or cubic fill                                                                                                  |
| Provisions                                                                                                                   | Families 324%, 446%, 455%                                                                               | State-space or cubic fill                                                                                                  |
| Interest income                                                                                                              | Modern: 10001; Legacy: 11000, 111xx–116xx, 121xx–123xx                                                  | Denton proportional benchmarking; overwrite if quarterly-like, otherwise gap-filling; Form 102 bridge when panel empty     |
| Interest expense                                                                                                             | Modern: 10003; Legacy: 21000, 211xx–213xx, 24101–24107                                                  | Same as interest income                                                                                                    |
| Operating income                                                                                                             | Modern: 10002; Legacy: 10000 minus interest income                                                      | Same as interest income                                                                                                    |
| Operating expense                                                                                                            | Modern: 10004; Legacy: 20000 minus interest expense                                                     | Same as interest income                                                                                                    |
| Net income                                                                                                                   | Modern: 61101−61102; Legacy: 10000−20000−35001                                                          | Derived directly when present; otherwise disaggregated from quarterly totals                                               |
| Net interest income                                                                                                          | Derived as interest income − interest expense                                                           | Recomputed wherever both components exist                                                                                  |
| Ratios (ROA, ROE, NIM, cost-to-income, NPL ratio, coverage ratio, LLP/loans, loan-to-deposit, liquidity, state equity share) | Computed only when inputs available                                                                     | Recomputed after imputation and reconciliation                                                                             |

: Detailed breakdown of accounting codes used for aggregation and their respective imputation methods. 

:::

{{< pagebreak >}}

::: {#tbl-missing-after-aggregation}

| Variable                      | Missing count | Percentage (%) |
| ----------------------------- | ------------- | -------------- |
| ROE                           | 117,806       | 68.72          |
| operating_income              | 114,883       | 67.01          |
| cost_to_income_ratio          | 114,883       | 67.01          |
| operating_expense             | 114,791       | 66.96          |
| ROA                           | 114,308       | 66.68          |
| net_income_amount             | 114,281       | 66.66          |
| NIM                           | 114,107       | 66.56          |
| interest_income               | 114,079       | 66.54          |
| net_interest_income           | 114,079       | 66.54          |
| interest_expense              | 114,079       | 66.54          |
| coverage_ratio                | 31,404        | 18.32          |
| npl_ratio                     | 14,892        | 8.69           |
| llp_to_loans_ratio            | 14,892        | 8.69           |
| loan_to_deposit_ratio         | 10,691        | 6.24           |
| state_equity_pct              | 8,605         | 5.02           |
| liquid_assets_to_total_assets | 80            | 0.05           |

: Summary of missing data after aggregation. **_NB:_** the missingness is systematic and accounted for in the imputation step. 

:::


{{< pagebreak >}}


::: {#tbl-zero-after-aggregation}

| Variable                      | Zero count | Percentage (%) |
| ----------------------------- | ---------- | -------------- |
| ROE                           | 117,809    | 68.72          |
| cost_to_income_ratio          | 114,883    | 67.01          |
| ROA                           | 114,311    | 66.68          |
| NIM                           | 114,252    | 66.64          |
| coverage_ratio                | 33,608     | 19.60          |
| npl_ratio                     | 31,404     | 18.32          |
| llp_to_loans_ratio            | 19,829     | 11.57          |
| loan_to_deposit_ratio         | 15,652     | 9.13           |
| state_equity_pct              | 8,674      | 5.06           |
| liquid_assets_to_total_assets | 8,608      | 5.02           |


: Summary of zero-value data after aggregation. **_NB:_** these values are recomputed after imputation. 

:::


{{< pagebreak >}}

### Reputation.ru compliance data {.appendix}


::: {.landscape}
::: {.landscape .smaller #tbl-reputation-json}

| JSON path | Explanation | Example value | Russian agency name | English agency name |
|-----------|-------------|---------------|---------------------|---------------------|
| Entity $\rightarrow$ Ogrn | Primary State Registration Number | "1107746858603" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Inn | Taxpayer Identification Number | "7703730349" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Kpp | Tax Registration Reason Code | "770101001" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Pfr | Pension Fund Registration Number | "087108168602" | Пенсионный фонд РФ | Pension Fund of Russia |
| Entity $\rightarrow$ Fss | Social Security Fund Number | "773603063777181" | Фонд социального страхования | Social Insurance Fund |
| Entity $\rightarrow$ RegistrationDate | Company registration date | "2010-10-20T00:00:00" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Status $\rightarrow$ Status | Current legal status | "Active" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Names $\rightarrow$ Items[0] $\rightarrow$ FullName | Full company name | "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ИНВЕСТ ИНЖИНИРИНГ\"" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ ActivityTypes $\rightarrow$ Items[0] $\rightarrow$ Code | Primary business activity code | "70.10.1" | Росстат | Federal State Statistics Service |
| Entity $\rightarrow$ ActivityTypes $\rightarrow$ Items[0] $\rightarrow$ Name | Business activity description | "ДЕЯТЕЛЬНОСТЬ ПО УПРАВЛЕНИЮ ФИНАНСОВО-ПРОМЫШЛЕННЫМИ ГРУППАМИ" | Росстат | Federal State Statistics Service |
| Entity $\rightarrow$ AuthorizedCapitals $\rightarrow$ Items[0] $\rightarrow$ Sum | Authorised (founding) capital amount | 55000.0 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ EmployeesInfo $\rightarrow$ Items[0] $\rightarrow$ Count | Number of employees | 0 | Росстат | Federal State Statistics Service |
| Entity $\rightarrow$ Addresses $\rightarrow$ Items[0] $\rightarrow$ UnsplittedAddress | Legal address | "105066, Г.МОСКВА, УЛ. СПАРТАКОВСКАЯ, Д. 11, ЭТ ПОДВАЛ ПОМ I КОМ 11.1" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Managers $\rightarrow$ Items[0] $\rightarrow$ Entity $\rightarrow$ Name | Director/manager name | "КАЛАШНИКОВА ЕКАТЕРИНА СЕРГЕЕВНА" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Managers $\rightarrow$ Items[0] $\rightarrow$ Position[0] $\rightarrow$ PositionName | Management position | "ГЕНЕРАЛЬНЫЙ ДИРЕКТОР" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Shareholders $\rightarrow$ Items[0] $\rightarrow$ Entity $\rightarrow$ Name | Shareholder name | "ООО ГДК \"РАЗВИТИЕ\"" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Shareholders $\rightarrow$ Items[0] $\rightarrow$ Share[0] $\rightarrow$ Size | Ownership percentage | 100.0 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ Shareholders $\rightarrow$ Items[0] $\rightarrow$ Share[0] $\rightarrow$ FaceValue | Share face value | 55000.0 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ TaxRegistrations $\rightarrow$ Items[0] $\rightarrow$ TaxOrganName | Tax authority name | "Инспекция Федеральной налоговой службы № 1 по г.Москве" | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ PensionFundRegistrations $\rightarrow$ Items[0] $\rightarrow$ FundOrganName | Pension fund office name | "Отделение Фонда пенсионного и социального страхования Российской Федерации по г. Москве и Московской области" | Пенсионный фонд РФ | Pension Fund of Russia |
| Entity $\rightarrow$ SocialInsuranceFundRegistrations $\rightarrow$ Items[0] $\rightarrow$ FundOrganName | Social insurance office name | "Отделение Фонда пенсионного и социального страхования Российской Федерации по г. Москве и Московской области" | Фонд социального страхования | Social Insurance Fund |
| Finance $\rightarrow$ ValueDynamics $\rightarrow$ 21203 $\rightarrow$ 2023 $\rightarrow$ 4 | Revenue (line 21203) | 612000.0 | Росстат | Federal State Statistics Service |
| Finance $\rightarrow$ ValueDynamics $\rightarrow$ 24003 $\rightarrow$ 2023 $\rightarrow$ 4 | Net profit (line 24003) | 12000.0 | Росстат | Federal State Statistics Service |
| ExpressCheck $\rightarrow$ TotalScore | Risk assessment score | "Attention" | Reputation.ru | Reputation.ru (proprietary analysis) |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Status | Legal status data | -1 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ AuthorisedCapital | Authorised (founding) capital records count | 1 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Name | Name records count | 1 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ ActivityTypeInfo | Activity type records count | 26 | Росстат | Federal State Statistics Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Address | Address records count | 6 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Shareholder | Shareholder records count | 4 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Manager | Manager records count | 4 | Федеральная налоговая служба | Federal Tax Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ License [^licence] | Licence records count | 3 | Various regulatory bodies | Various regulatory bodies |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Arbitr | Arbitration case records count | -1 | Высший арбитражный суд | Supreme Arbitration Court |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ FedresursMessages | Fedresurs message records count | -1 | Федресурс | Fedresurs |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ BankruptMessages | Bankruptcy message records count | -1 | Федресурс | Fedresurs |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Bailiffs | Bailiff enforcement records count | -1 | Федеральная служба судебных приставов | Federal Bailiff Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Contracts | Government contract records count | -1 | Федеральное казначейство | Federal Treasury |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Finance | Financial report records count | 12 | Росстат | Federal State Statistics Service |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Trademark | Trademark records count | -1 | Федеральная служба по интеллектуальной собственности | Federal Service for Intellectual Property |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Patents | Patent records count | -1 | Федеральная служба по интеллектуальной собственности | Federal Service for Intellectual Property |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Inspections | Inspection records count | -1 | Various regulatory agencies | Various regulatory agencies |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Subsidies | Subsidy records count | -1 | Федеральное казначейство | Federal Treasury |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ Vehicles | Vehicle registration records count | -1 | Министерство внутренних дел | Ministry of Internal Affairs |
| Entity $\rightarrow$ InfoCounters $\rightarrow$ BanksInfo | Banking information records count | -1 | Центральный банк | Central Bank of Russia |

: Detailed description of the JSON response from the Reputation.ru API, including sample values and their sources. **Note**: A value of -1 in `InfoCounters` indicates no data available or not applicable for this entity, while positive numbers show the count of available records for that data type.

:::
:::

[^licence]: Spelling preserved from the original JSON schema. 

{{< pagebreak >}}

<!-- ::: {.smaller #tbl-rfsd-description}

| Indicator | Description | Source |
|-----------|-------------|---------|
| **inn** | Taxpayer Identification Number (ИНН) | Federal Tax Service (FNS) via EGRUL |
| **ogrn** | Primary State Registration Number (ОГРН) | Federal Tax Service (FNS) via EGRUL |
| **line_1100** | Total Assets (Balance Sheet line 1100) | Rosstat financial statements register |
| **line_2110** | Revenue (Income Statement line 2110) | Rosstat financial statements register |
| **line_4100** | Net Cash Flow from Operating Activities | Rosstat financial statements register |
| **imputed** | Flag indicating if financial data was imputed using prior-year values | Rosstat (derived) |
| **articulated** | Flag indicating if statement coherence was verified | Rosstat (derived) |
| **eligible** | Flag indicating firm eligibility for inclusion in dataset | Multiple sources (Rosstat, CBR, FNS) |
| **exemption_criteria** | Reason for exemption from filing requirements | Rosstat Statistical Register |
| **okfc** | Organisational-Legal Form Classifier | FNS via EGRUL |
| **okved** | Russian Classification of Economic Activities | FNS via EGRUL + Rosstat |
| **oktmo** | Russian Classification of Municipal Territories | FNS via EGRUL |
| **lon** | Longitude coordinate of incorporation address | FNS via EGRUL (geo-coded) |
| **lat** | Latitude coordinate of incorporation address | FNS via EGRUL (geo-coded) |
| **region** | Federal subject of incorporation | FNS via EGRUL |
| **creation_date** | Date of company incorporation | FNS via EGRUL |
| **dissolution_date** | Date of company dissolution (if applicable) | FNS via EGRUL |
| **age** | Company age in years | FNS via EGRUL (calculated) |
| **financial** | Flag indicating if firm files financial statements | Rosstat |
| **filed** | Flag indicating if firm actually filed in given year | Rosstat |
| **simplified** | Flag for simplified reporting regime | Rosstat |
| **outlier** | Flag marking potential data outliers | Rosstat (derived) |
| **totals_adjustment** | Flag indicating totals were adjusted for consistency | Rosstat (derived) |

:Detailed description of the columns in the RFSD dataset, including their sources and meanings.

::: 

{{< pagebreak >}} -->



## Appendix: code {.appendix}


```{=typst}
#render_appendix_listings()
```

### LLM schema and initial ingestion Cypher {.appendix}

```json {#lst-gemini-schema lst-cap="JSON schema for Gemini structured output" code-line-numbers="true" typst:breakable=true}
{
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "description": "A unique node in a graph.",
                "properties": {
                    "type": {
                        "type": "string"
                    },
                    "id": {
                        "type": "string",
                        "description": "A unique identifier for the node."
                    },
                    "labels": {
                        "type": "array",
                        "description": "A list of labels for the node, one of Person, Company, Bank",
                        "items": {
                            "type": "string",
                            "enum": ["Person", "Company", "Bank"]
                        }
                    },
                    "properties": {
                        "type": "object",
                        "description": "A set of properties for the node.",
                        "properties": {
                            "full_name": {
                                "type": "string",
                                "description": "The full name of the person or organisation, eg. Ivanov Ivan Ivanovich or Obshchestvo s ogranichennoy otvetstvennostyu Roga i Kopyta."
                            },
                            "short_name": {
                                "type": "string",
                                "description": "The short name of the person or organisation, eg. Ivanov I.I. or JSC Roga i Kopyta."
                            },
                            "name_en": {
                                "type": "string",
                                "description": "The name of the person or organisation in English, transliterated or translated."
                            },
                            "citizenship": {
                                "type": "string",
                                "description": "The country of citizenship in ISO 3166-1 alpha-2 format, e.g. RU, US, GB (if present)."
                            },
                            "residence": {
                                "type": "string",
                                "description": "The place of residence in English, e.g. Moscow, Russia (if present)."
                            },
                            "ogrn": {
                                "type": "string",
                                "description": "The OGRN identifier for an organisation/company, if present."
                            },
                            "bank_regn": {
                                "type": "string",
                                "description": "The bank registration number for a bank, if present."
                            }
                        },
                        "required": ["full_name", "short_name"]
                    }
                },
                "required": ["type", "id", "labels", "properties"]
            }
        },
        "rels": {
            "type": "array",
            "items": {
                "type": "object",
                "description": "A relationship between two nodes in a graph.",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "A unique identifier for the relationship."
                    },
                    "label": {
                        "type": "string",
                        "description": "The type of relationship, one of OWNERSHIP, VOTING, FAMILY, SIGNIFICANT_INFLUENCE.",
                        "enum": ["OWNERSHIP", "VOTING", "FAMILY", "SIGNIFICANT_INFLUENCE"]
                    },
                    "properties": {
                        "type": "object",
                        "description": "A set of properties for the relationship.",
                        "properties": {
                            "value": {
                                "type": "number",
                                "description": "The percentage value involved in the relationship, eg. ownership_share or voting_share (if present)."
                            },
                            "type": {
                                "type": "string",
                                "description": "The specific type of the relationship in English, eg. individual executive body, founder, participant, spouse, son/daughter etc. (if present)."
                            },
                            "date": {
                                "type": "string",
                                "description": "The date of the relationship in the format YYYY-MM-DD, e.g. 2018-01-01 (if present)."
                            }
                        },
                        "required": ["value", "type"]
                    },
                    "startNode": {
                        "type": "string",
                        "description": "The unique identifier of the start node."
                    },
                    "endNode": {
                        "type": "string",
                        "description": "The unique identifier of the end node."
                    }
                },
                "required": ["id", "label", "properties", "startNode", "endNode"]
            }
        }
    },
    "required": ["nodes", "rels"]
}
```

{{< pagebreak >}}


```{.cypher #lst-import-gemini-into-neo lst-cap="Importing Gemini structured output into Neo4j" code-line-numbers="true"}
CALL apoc.load.json('neo_export.jsonl') YIELD value AS value

WHERE value.type = 'node'

WITH VALUE
CALL apoc.merge.node(
    value.labels + ['Ent'], 
    {neo4jImportId:value.id},
    value.properties, 
    value.properties
    ) YIELD node
RETURN node;

CALL apoc.load.json('neo_export.jsonl') YIELD value AS rel_props

WHERE rel_props.type = 'relationship'
MATCH (a:Ent) WHERE a.neo4jImportId = rel_props.start.id 
MATCH (b:Ent) WHERE b.neo4jImportId = rel_props.end.id

CALL apoc.merge.relationship(
    a, 
    rel_props.label, 
    rel_props.properties, 
    rel_props.properties, 
    b, {}
) YIELD rel

RETURN rel; 
```

{{< pagebreak >}}

### CBR accounting aggregation and imputation {.appendix}

```{.python #lst-cbr-aggregation include="../../../data_processing/cbr_accounting/cbr_aggregation.py" filename="data_processing/cbr_accounting/cbr_aggregation.py" lst-cap="Script to aggregate CBR accounting data, preserving nulls for imputation"}
```

{{< pagebreak >}}


```{.python #lst-cbr-imputation include="../../../data_processing/cbr_accounting/cbr_aggregation.py" filename="data_processing/cbr_accounting/cbr_imputation.py" lst-cap="Script to impute missing CBR accounting time series with SSM/cubic/Denton disaggregation"}
```


<!-- ::: {#lst-sql-for-camel lst-cap="SQL query in DuckDB to aggregate CAMEL indicators from monthly/quarterly CBR accounting data" code-line-numbers="true"} -->
<!-- ```sql {#lst-sql-for-camel lst-cap="SQL query in DuckDB to aggregate CAMEL indicators from monthly/quarterly CBR accounting data" code-line-numbers="true" typst:breakable=true}
WITH 
-- Total Assets, Liabilities, and Equity
balance_sheet AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CASE WHEN A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_assets,
        SUM(CASE WHEN A_P = '2' AND NOT (PLAN = 'А' AND 
             (NUM_SC LIKE '102%' OR NUM_SC LIKE '106%' OR NUM_SC LIKE '107%' OR NUM_SC LIKE '108%')) 
             THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_liabilities,
        SUM(CASE WHEN A_P = '2' AND PLAN = 'А' AND 
             (NUM_SC LIKE '102%' OR NUM_SC LIKE '106%' OR NUM_SC LIKE '107%' OR NUM_SC LIKE '108%')
             THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_equity
    FROM form101_post2008
    WHERE CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Loan data
loans AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CASE WHEN NUM_SC BETWEEN '44000' AND '47000' AND A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_loans
    FROM form101_post2008
    WHERE CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Loans by client type
loan_distribution AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CASE WHEN (NUM_SC LIKE '455%' OR NUM_SC LIKE '457%') 
            AND A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS individual_loans,
        SUM(CASE WHEN (NUM_SC BETWEEN '44200' AND '44699') 
            AND NUM_SC NOT IN ('44501', '44601', '44701', '44801', '44901')
            AND A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS company_loans,
        SUM(CASE WHEN (NUM_SC BETWEEN '44001' AND '44199' OR NUM_SC LIKE '458%' OR
                  NUM_SC IN ('44901', '44801', '44701'))
            AND A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS state_loans
    FROM form101_post2008
    WHERE CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Deposit data
deposits AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CASE WHEN NUM_SC BETWEEN '42000' AND '43000' AND A_P = '2' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_deposits
    FROM form101_post2008
    WHERE CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Non-performing loans
npl AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CAST(VITG AS DOUBLE)) AS npl_amount
    FROM form101_post2008
    WHERE NUM_SC LIKE '458%' AND A_P = '1' AND CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Loan loss provisions
llp AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CAST(VITG AS DOUBLE)) AS provision_amount
    FROM form101_post2008
    WHERE (NUM_SC LIKE '324%' OR NUM_SC LIKE '446%' OR NUM_SC LIKE '455%') AND A_P = '1' AND CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Liquid assets (cash and equivalents)
liquid_assets AS (
    SELECT 
        REGN,
        DT,
        report,
        SUM(CASE WHEN 
            (NUM_SC LIKE '202%' OR  -- Cash and equivalents
             NUM_SC LIKE '301%' OR  -- Correspondent accounts
             NUM_SC LIKE '302%')    -- Central bank reserves
            AND A_P = '1' THEN CAST(VITG AS DOUBLE) ELSE 0 END) AS total_liquid_assets
    FROM form101_post2008
    WHERE CAST(VITG AS DOUBLE) > 0 AND CAST(PRIZ AS INTEGER) = 1
    GROUP BY REGN, DT, report
),

-- Income statement data
income_data AS (
    SELECT 
        REGN,
        report,
        MAX(CASE WHEN CODE = '10001' THEN CAST(SIM_ITOGO AS DOUBLE) ELSE 0 END) AS interest_income,
        MAX(CASE WHEN CODE = '10002' THEN CAST(SIM_ITOGO AS DOUBLE) ELSE 0 END) AS operating_income,
        MAX(CASE WHEN CODE = '10003' THEN CAST(SIM_ITOGO AS DOUBLE) ELSE 0 END) AS interest_expense,
        MAX(CASE WHEN CODE = '10004' THEN CAST(SIM_ITOGO AS DOUBLE) ELSE 0 END) AS operating_expense
    FROM form102_pl
    WHERE CAST(SIM_ITOGO AS DOUBLE) > 0
    GROUP BY REGN, report
),

-- Net income calculation
net_income AS (
    SELECT
        REGN,
        report,
        (interest_income + operating_income - interest_expense - operating_expense) AS net_income_amount
    FROM income_data
),

-- Capital adequacy data from form134
capital_data AS (
    SELECT 
        REGN,
        MAX(CASE WHEN C1 = '000' THEN CAST(C3 AS DOUBLE) ELSE 0 END) AS total_assets_weighted,
        MAX(CASE WHEN C1 = '101' THEN CAST(C3 AS DOUBLE) ELSE 0 END) AS tier1_capital
    FROM form134_data
    WHERE CAST(C3 AS DOUBLE) > 0
    GROUP BY REGN
)

-- Main query combining all financial indicators
SELECT 
    bs.REGN,
    bs.DT,
    bs.report,
    
    -- Basic financials
    bs.total_assets,
    bs.total_liabilities,
    bs.total_equity,
    
    -- Profitability Indicators
    i.interest_income,
    i.interest_expense,
    (i.interest_income - i.interest_expense) AS net_interest_income,
    i.operating_income,
    i.operating_expense,
    ni.net_income_amount,
    
    -- Profitability Ratios
    CASE WHEN bs.total_assets > 0 THEN (ni.net_income_amount / bs.total_assets) * 100 ELSE NULL END AS ROA,
    CASE WHEN bs.total_equity > 0 THEN (ni.net_income_amount / bs.total_equity) * 100 ELSE NULL END AS ROE,
    CASE WHEN bs.total_assets > 0 THEN ((i.interest_income - i.interest_expense) / bs.total_assets) * 100 ELSE NULL END AS NIM,
    CASE WHEN (i.interest_income + i.operating_income) > 0 THEN (i.operating_expense / (i.interest_income + i.operating_income)) * 100 ELSE NULL END AS cost_to_income_ratio,
    
    -- Efficiency Indicators
    CASE WHEN bs.total_assets > 0 THEN ((i.interest_income + i.operating_income) / bs.total_assets) * 100 ELSE NULL END AS asset_turnover,
    CASE WHEN bs.total_assets > 0 THEN (i.operating_expense / bs.total_assets) * 100 ELSE NULL END AS non_interest_expense_to_assets,
    
    -- Risk and Credit Quality Indicators
    l.total_loans,
    n.npl_amount,
    p.provision_amount,
    CASE WHEN l.total_loans > 0 THEN (n.npl_amount / l.total_loans) * 100 ELSE NULL END AS npl_ratio,
    CASE WHEN l.total_loans > 0 THEN (p.provision_amount / l.total_loans) * 100 ELSE NULL END AS llp_to_loans_ratio,
    CASE WHEN n.npl_amount > 0 THEN (p.provision_amount / n.npl_amount) * 100 ELSE NULL END AS coverage_ratio,

    -- Loan Distribution Data
    ld.individual_loans,
    ld.company_loans,
    ld.state_loans,
    
    -- Loan Distribution Ratios
    CASE WHEN l.total_loans > 0 THEN (COALESCE(ld.individual_loans, 0) / l.total_loans) * 100 ELSE NULL END AS individuals_pct_of_loans,
    CASE WHEN l.total_loans > 0 THEN (COALESCE(ld.company_loans, 0) / l.total_loans) * 100 ELSE NULL END AS companies_pct_of_loans,
    CASE WHEN l.total_loans > 0 THEN (COALESCE(ld.state_loans, 0) / l.total_loans) * 100 ELSE NULL END AS state_pct_of_loans,
    
    -- Loans to Assets Ratios
    CASE WHEN bs.total_assets > 0 THEN (COALESCE(ld.individual_loans, 0) / bs.total_assets) * 100 ELSE NULL END AS individuals_loans_to_assets,
    CASE WHEN bs.total_assets > 0 THEN (COALESCE(ld.company_loans, 0) / bs.total_assets) * 100 ELSE NULL END AS companies_loans_to_assets,
    CASE WHEN bs.total_assets > 0 THEN (COALESCE(ld.state_loans, 0) / bs.total_assets) * 100 ELSE NULL END AS state_loans_to_assets,
    
    -- Comparative Loan Ratios
    CASE WHEN COALESCE(ld.company_loans, 0) > 0 THEN (COALESCE(ld.individual_loans, 0) / ld.company_loans) * 100 ELSE NULL END AS individuals_to_companies,
    CASE WHEN COALESCE(ld.state_loans, 0) > 0 THEN (COALESCE(ld.individual_loans, 0) / ld.state_loans) * 100 ELSE NULL END AS individuals_to_state,
    CASE WHEN COALESCE(ld.state_loans, 0) > 0 THEN (COALESCE(ld.company_loans, 0) / ld.state_loans) * 100 ELSE NULL END AS companies_to_state,
        
    -- Liquidity Indicators
    d.total_deposits,
    la.total_liquid_assets,
    CASE WHEN d.total_deposits > 0 THEN (l.total_loans / d.total_deposits) * 100 ELSE NULL END AS loan_to_deposit_ratio,
    CASE WHEN bs.total_assets > 0 THEN (la.total_liquid_assets / bs.total_assets) * 100 ELSE NULL END AS liquid_assets_to_total_assets,
    
    -- Capital Adequacy Indicators
    c.tier1_capital,
    CASE WHEN bs.total_assets > 0 THEN (c.tier1_capital / bs.total_assets) * 100 ELSE NULL END AS leverage_ratio,
    CASE WHEN c.total_assets_weighted > 0 THEN (c.tier1_capital / c.total_assets_weighted) * 100 ELSE NULL END AS tier1_capital_ratio
    
FROM balance_sheet bs
LEFT JOIN loans l ON bs.REGN = l.REGN AND bs.report = l.report
LEFT JOIN loan_distribution ld ON bs.REGN = ld.REGN AND bs.report = ld.report
LEFT JOIN deposits d ON bs.REGN = d.REGN AND bs.report = d.report
LEFT JOIN npl n ON bs.REGN = n.REGN AND bs.report = n.report
LEFT JOIN llp p ON bs.REGN = p.REGN AND bs.report = p.report
LEFT JOIN liquid_assets la ON bs.REGN = la.REGN AND bs.report = la.report
LEFT JOIN income_data i ON bs.REGN = i.REGN AND SUBSTR(bs.report, 5) = SUBSTR(i.report, 5)
LEFT JOIN net_income ni ON bs.REGN = ni.REGN AND SUBSTR(bs.report, 5) = SUBSTR(i.report, 5)
LEFT JOIN capital_data c ON bs.REGN = c.REGN
ORDER BY bs.REGN, bs.DT, tier1_capital_ratio
```
::: -->

{{< pagebreak >}}

### Banki.ru Cypher {.appendix}


```{.cypher #lst-banki-schema .code-overflow-wrap code-line-numbers="true" lst-cap="Schema for the Banki.ru data"} 
LOAD CSV WITH HEADERS from  'file:///regn_ogrn_licence_filled_na.csv' as row
WITH * 
WHERE row.regn is not null 
WITH row
CALL (row) {
    WITH *, apoc.map.clean(row, ["№ п/п"], []) as props 
    WITH *, apoc.map.setEntry(props, 'inn', toInteger(props.inn)) as props 
    WITH *, apoc.map.setEntry(props, 'orgId', toString(toInteger(props.orgId))) as props 
    WITH *, apoc.map.setEntry(props, 'ogrn', toString(toInteger(props.ogrn))) as props 
    WHERE props.regn is not null
    MERGE (e:Ent:Bank {bank_regn:toString(row.regn)})
    SET e += props
} IN TRANSACTIONS OF 10 ROWS
RETURN * LIMIT 10;

CALL apoc.load.json('cbr_en.json') yield value
MERGE (b:Ent:Bank { bank_regn: value.regn_cbr })
WITH b, apoc.map.clean(value, ['reports_cbr'], []) AS props
 SET b += props
 SET b.sources = ['cbr_info']
RETURN b LIMIT 10;
```

{{< pagebreak >}}

```{.cypher #lst-banki-merge .code-overflow-wrap code-line-numbers="true" lst-cap="Merging the Banki.ru data into Neo4j"}
// :auto
CALL apoc.load.json('banki_ru_memory.jsonl') yield value
CALL (value) {
    MATCH (b:Bank { regn_cbr:value.regn_banki_memory })
    WITH b, value
    WITH b, apoc.map.clean(value, ['news_banki_memory'], []) AS banki_props, value

    SET b += banki_props
    SET b.sources = apoc.coll.toSet(b.sources + ['banki_ru'])

    WITH b, value
    UNWIND value.news_banki_memory AS news_item

        MERGE (n:News { url:news_item.url })
        MERGE (b)-[r:HAS_NEWS]->(n)
        SET r += news_item
        SET n += news_item
} IN transactions of 100 rows
RETURN * LIMIT 2;

// :auto 
CALL apoc.load.json('banki_ru_active.jsonl') yield value
CALL (value) {
    MATCH (b:Bank { regn_cbr:value.regn })
    WITH b, value
    SET b.sources = apoc.coll.toSet(b.sources + ['banki_ru'])

    WITH b, value
    UNWIND value.news AS news_item
        MERGE (n:News { url:news_item.url })
        MERGE (b)-[r:HAS_NEWS]->(n)
        SET r += news_item
        SET n += news_item
} IN TRANSACTIONS of 100 ROWS
RETURN * LIMIT 2;
```
{{< pagebreak >}}

### Cypher for storing network metrics {.appendix}


```{.cypher #lst-neo-5-hop-projection include="../../../data_processing/cypher/20_project_bank_ownership_mgmt.cypher" filename="../../../data_processing/cypher/20_project_bank_ownership_mgmt.cypher" lst-cap="Cypher query to create a projection of the graph with 5 hops from a bank node"}
```

{{< pagebreak >}}

```{.cypher #lst-network-metrics include="../../../data_processing/cypher/21_network_metrics.cypher" filename="../../../data_processing/cypher/21_network_metrics.cypher" lst-cap="Cypher query to calculate network metrics for the family, bank, and ownership network projection"}
```

{{< pagebreak >}}


```{.cypher #lst-complexity-metrics include="../../../data_processing/cypher/14_ownership_complexity.cypher" filename="../../../data_processing/cypher/14_ownership_complexity.cypher" lst-cap="Cypher query to calculate network metrics for the complexity of the ownership structure"}
```

{{< pagebreak >}}


```{.cypher .smaller #lst-family-ownership-metrics include="../../../data_processing/cypher/11_1_family_connections.cypher" filename="../../../data_processing/cypher/11_1_family_connections.cypher" lst-cap="Cypher query to calculate family ownership metrics"}
```

{{< pagebreak >}}


```{.cypher #lst-foreign-ownership-metrics include="../../../data_processing/cypher/13_foreign_connections.cypher" filename="../../../data_processing/cypher/13_foreign_connections.cypher" lst-cap="Cypher query to calculate foreign ownership metrics"}
```



::: {#refs}
:::
