---
title: "Banking on family: why family ownership matters for the survival of Russian banks"
crossref:
  lof-title: "List of figures"
  lot-title: "List of tables"
  lol-title: "List of code listings"
author: 
  - name: Alexander Soldatkin
    affiliations: 
      - name: "University of Oxford"  
        department: "Oxford School of Global and Area Studies"
    email: "alexander.soldatkin@sant.ox.ac.uk"  # Add your email here
abstract: |
  This study investigates how family kinship networks influence bank survival in Russia's institutional environment from 2004 to 2023. Employing a novel graph database methodology to map ownership structures and kinship relationships amongst bank stakeholders, we analyse the survival determinants of Russian banks through both logistic regression and Cox proportional hazards models, controlling for traditional CAMEL financial indicators. Our empirical analysis demonstrates that family network density, measured by family connection ratios, significantly enhances bank survival probability, with family connection ratios increasing survival odds by 63% in cross-sectional models and nearly doubling survival odds in time-varying specifications. Critically, these protective effects intensify during periods of systemic stress, with crisis interactions revealing that dense family networks provide 26.6% additional survival protection during the 2008 financial crisis and 2014-15 sanctions periods. Conversely, whilst foreign ownership provides extraordinary protection under normal conditions (482% increase in survival odds), it transforms into a significant vulnerability during geopolitical crises, with each percentage point of foreign ownership reducing survival odds by 28.1% during stress periods. These findings illustrate how informal governance mechanisms substitute for weak formal institutions in transitional economies, demonstrating that kinship-based coordination networks serve as crucial institutional backstops when conventional market and regulatory mechanisms falter.
  \vspace{10em}

date: 2025-06-05
date-format: "long"
keywords: 
  - "Russian banking"
  - "family ownership"
  - "kinship networks"
  - "bank survival"
  - "graph database"
  - "social network analysis"
  - "Cox proportional hazards model"
  - "logistic regression"
  - "political economy"

format:
  # cambridge-medium-pdf: 
  pdf:
    keep-tex: true
    pdf-engine: lualatex
    toc: true
    toc-title: "Contents"
    toc-depth: 2
    number-sections: true
    number-depth: 4
    # mainfont: "CMU Bright"
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
        \usepackage{ntheorem}
        \theoremseparator{:}
        \newtheorem{hyp}{Hypothesis}
        \renewcommand{\arraystretch}{1.2}
lang: "en"
filters: 
    - quarto-ext/include-code-files
execute:
  enabled: true
jupyter:
  kernel: factions-env
---


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

## Tables, figures, and code listings {.unnumbered}

\listoftables


\listoffigures


\listoflistings

{{< pagebreak >}}

## Introduction {.unnumbered}

The Russian banking sector's unique institutional environment presents a compelling case study for examining the role of ownership and kinship-based coordination networks in bank survival. From a peak of about 1,525 active banks in 1996 (see @fig-bank-failures-cumulative), the sector has contracted to 309 institutions[^CBR] by the end of 2025, and around 80% of all once active banks cumulatively have perished since the inception of the banking industry. The persistent high failure rates amidst the presence of formal regulatory frameworks suggest that conventional financial determinants alone cannot adequately explain institutional survival patterns. Instead, informal relationship networks--—particularly those based on family connections--—may play a crucial role in mediating institutional resilience and crisis recovery. 

[^CBR]: Latest data [from the Central Bank of Russia (CBR)](https://www.cbr.ru/banking_sector/#:~:text=В%20России%20309%20действующих%20банков,и%2043%20небанковских%20кредитных%20организаций.&text=Банки%20и%20небанковские%20кредитные%20организации,лицензий%2C%20которые%20выдаются%20Банком%20России.) as of 1 May 2025. As illustrated in @fig-bank-failures-cumulative, the Russian banking sector has experienced a tumultuous history of rapid development and likewise rapid failures since the 1990s, with significant spikes in bank closures occurring during periods of economic crisis and regulatory tightening. With a peak of 1,525 active banks in 1996-96, the sector has seen a steady decline in the number of firms, with a fall of about 20% by 1999. The number of active banks then somewhat plateaued until 2004, when a new steady wave of closures began under the leadership of Sergey Ignatyev at the Central Bank, who occupied his position from 2002 to 2013. The gradient further steepened with the arrival of Elvira Nabiullina as the head of the Bank of Russia in 2013, who started off her tenure with 896 active banks under her auspices and has since overseen the closure of more than 500 institutions, with the number of active banks falling to 309 by mid-2025. The primary reasons for closure have included bankruptcy (which usually means a combination of having its licence revoked by the Central Bank and some tax investigations), being closed by the tax service, or voluntary liquidation by the shareholders. The 'Other' Category in the plot refers to banks that have not been able to increase their capitalisation in line with the Central Bank's requirements, and the 'Reorganisation' category refers to banks that have merged with other institutions or have been taken over by either the Central Bank or the Deposit Insurance Agency (DIA) in order to be restructured. 


Existing investigations of Russian banking instability have concentrated predominantly upon conventional financial determinants: capital adequacy ratios, profitability metrics, asset quality indicators, and liquidity management practices—supplemented by political economy variables encompassing electoral cycles [@fungacova_PoliticsBankFailures_2022], regional corruption indices [@weill_HowCorruptionAffects_2011], factional associations [@soldatkin_FactionalismCompetitionEfficiency_2020], and strategic orientation [@barajas_SurvivalRussianBanks_2023]. Whilst these empirical contributions have substantially advanced understanding of institutional dynamics within Russia's idiosyncratic political-economic context, they have systematically neglected a potentially fundamental governance mechanism that may prove central to comprehending survival patterns: family ownership structures and kinship-based coordination networks. This remains a substantial theoretical and empirical oversight, particularly considering the extensive scholarly documentation establishing family ownership as a predominant organisational form across diverse institutional and geographic contexts, with demonstrable effects upon firm performance trajectories, strategic decision-making processes, and crisis resilience mechanisms [@anderson_FoundingFamilyOwnershipFirm_2003; @villalonga_HowFamilyOwnership_2006; @khanna_EstimatingPerformanceEffects_2001]. The absence of a comprehensive analytical framework integrating network factors into the study of Russian banking dynamics represents a significant empirical gap, particularly given the documented importance of informal relationships in diverse economic contexts [@ledeneva_RussiaEconomyFavours_1998]. 

::: {#fig-bank-failures-cumulative .smaller }

![](./figures/bank_closures_cumulative.pdf){width=100%}

```{=latex}
\tiny{\textit{Source:} calculations by the author based on data from the Central Bank of Russia (CBR) and Reputation.ru.}
```

Cumulative number of bank failures in Russia from 1989 to 2023.

:::

The primary research question motivating this paper concerns whether family ownership structures and kinship-based coordination networks exert measurable influence upon bank survival probabilities in Russia. This analytical inquiry assumes exceptional theoretical and practical significance given Russia's distinctive institutional environment, characterised by persistently weak formal governance structures, elevated regulatory uncertainty, and systematic political interference in economic decision-making processes—institutional conditions that extant theoretical literature suggests should systematically amplify the relative importance of alternative coordination mechanisms, including family-based governance networks.

This investigation systematically integrates three distinct yet interconnected research areas that have previously evolved in relative isolation. Firstly, the comprehensive literature examining Russian banking failures has established analytical frameworks for understanding financial, political, and competitive determinants of institutional survival, yet has failed to incorporate relationship-based governance mechanisms beyond the narrow scope of political factional analysis. Secondly, the family business literature has developed theoretically robust frameworks for analysing how kinship networks influence firm performance trajectories, but has not been systematically applied to financial institutions in Russia. Thirdly, the emerging research investigating factional networks within Russian banking demonstrates the empirical importance of informal relationship structures whilst neglecting to explore how family connections intersect with, complement, or substitute political associations.

Our theoretical contribution lies in synthesising these disparate literature streams to construct a deeper analytical framework for understanding family networks as governance mechanisms in the context of institutional uncertainty. We posit that family ownership in Russian banking serves multiple coordinated functions: providing alternative information transmission channels during periods of regulatory inconstancy, creating informal insurance mechanisms during episodes of financial distress, and establishing coordination platforms that substitute for underdeveloped market-based coordination mechanisms.

This paper combines two distinct quantitative research methods: survival analysis using Cox proportional hazards and logistic regression, as well as detailed network mapping of family relationships amongst Russian bank ownership and senior management. Our empirical strategy leverages comprehensive datasets spanning the period 2007-2023, incorporating traditional financial performance indicators, detailed ownership structures, management composition data, and systematically constructed measures of family network connectivity derived through network analysis of underexplored corporate governance documentation from the Central Bank. Our analytical approach integrates conventional survival modelling techniques with advanced network analysis methodologies, enabling precise isolation of family relationship effects whilst controlling for the extensive range of financial, political, and institutional factors identified within existing scholarly literature. Furthermore, we employ a novel data management approach using a graph database (in Neo4j) for computing network metrics alongside storing metadata on ownership and management relationships, helping integrate diverse data sources and enabling efficient querying of network data. 

In what follows, we test two interrelated propositions. First **(H1)**, we posit that banks embedded in denser kinship networks—measured by a higher family-connection ratio—enjoy significantly lower hazard rates of failure, as informal family ties provide both reputational insurance and liquidity backstops when formal institutions falter. Second **(H2)**, we expect this 'family dividend' to be most pronounced during periods of systemic stress (e.g., the 2008 financial crisis and the 2014–15 sanctions shock), when state regulators lean more heavily on informal mechanisms to shore up stability. 

Section 1 presents a comprehensive literature review examining three interconnected research domains: empirical determinants of Russian bank failures, family ownership and business group dynamics, and the theoretical integration of these perspectives within our analytical framework. Section 2 develops testable hypotheses regarding family network effects upon bank survival probabilities, derived from the theoretical synthesis. Section 3 describes our novel graph database approach to data construction, incorporating ownership structures, management composition, and systematically constructed measures of family network connectivity. Section 4 explains our methodological approach, including survival analysis using logistic regression and Cox proportional hazards models alongside detailed network mapping techniques. Section 5 presents the primary empirical findings, conducts extensive robustness testing across multiple model specifications, and explores alternative econometric approaches. Section 6 discusses the implications of our findings, and the last section concludes. 

## Literature review and hypotheses

This literature review examines three interconnected research domains essential for understanding bank survival in Russia's unique institutional context. First, we analyse the established determinants of Russian bank failures, encompassing traditional financial indicators and institutional factors. Second, we explore the role of ownership structures and state/foreign connections, drawing from research on factional networks within Russian banking. Third, we examine the broader literature on family ownership and business group dynamics, which provides theoretical foundations for understanding how kinship networks and informal governance mechanisms influence firm survival across diverse institutional contexts. This tripartite approach enables us to synthesise insights from conventional banking research with emerging understanding of network-based governance mechanisms, ultimately informing our investigation of how familial and ownership connections affect bank survival in Russia.

### Failures of Russian banks 

The empirical literature on Russian banking demonstrates some consistency in identifying fundamental determinants of institutional survival, whilst revealing the distinctive influence of political and network factors absent from conventional banking research. This foundation provides the analytical framework for our subsequent examination of ownership networks and familial connections.

#### CAMEL factors and their role in bank survival {.unnumbered}

Empirical investigations spanning the post-transition period consistently identify bank size, profitability, and capital adequacy as primary predictors of institutional viability. The evidence reveals a robust negative relationship between bank size and the probability of failure, with coefficients ranging from -0.236 to -0.385 across multiple studies [@barajas_SurvivalRussianBanks_2023; @fungacova_PoliticsBankFailures_2022; @fungacova_DoesCompetitionInfluence_2013a]. This relationship corroborates the "too-big-to-fail" hypothesis within the Russian context, suggesting that larger institutions benefit from implicit state guarantees and enhanced operational resilience.

Profitability metrics, particularly return on assets (ROA), demonstrate substantial explanatory power across studies, with negative coefficients on failure probability ranging from -11.999 to -82.3, indicating that profitable institutions enjoy significantly better survival prospects. The magnitude of these effects underscores the critical importance of operational efficiency in the fragmented Russian banking landscape. Similarly, capital adequacy ratios consistently exhibit negative relationships with failure probability, though the coefficient magnitudes vary considerably across studies, potentially reflecting evolving regulatory frameworks and measurement methodologies.

Liquidity management emerges as another fundamental determinant, with liquid assets ratios demonstrating strong negative correlations with failure probability (coefficients: -1.93 to -2.39). This finding assumes particular significance given the historical volatility of Russian financial markets and the propensity for sudden liquidity crises. Asset quality, conversely, exhibits the expected positive relationship with failure probability, as outsized non-performing loan ratios (NPL) consistently predict institutional distress.

#### Ownership structures and control mechanisms {.unnumbered}

Building upon these fundamental financial indicators, the literature reveals considerable complexity regarding ownership effects on Russian bank performance. Foreign ownership demonstrates consistently protective effects, with foreign control reducing failure probability significantly [@barajas_SurvivalRussianBanks_2023]. This finding aligns with theoretical expectations regarding superior risk management practices and access to international capital markets. State ownership presents more nuanced patterns, with studies documenting both protective effects for large state-controlled institutions and potential inefficiencies arising from political interference.

Strategic orientation factors introduce additional analytical complexity. The asymmetric effects of corporate versus retail focus demonstrate that whilst corporate deposit concentration reduces failure probability, corporate lending orientation increases the risk of bankruptcy [@barajas_SurvivalRussianBanks_2023]. This paradox suggests sophisticated market dynamics wherein corporate relationships provide funding stability whilst simultaneously exposing institutions to concentrated credit risks.

These ownership effects provide the foundation for understanding more complex network-based governance mechanisms, including the factional associations and informal power structures that distinguish Russian banking from conventional institutional frameworks.

#### Political economy and institutional environment {.unnumbered}

The incorporation of political economy factors represents a significant advancement in understanding Russian banking dynamics, revealing systematic patterns that extend beyond traditional financial metrics. Electoral cycle research provides compelling evidence that bank failures cluster temporally, with institutions enjoying enhanced survival prospects during pre-election periods [@fungacova_PoliticsBankFailures_2022]. These findings suggest systematic political interference in supervisory decision-making, with failure probabilities declining by factors of 2-3 times during politically sensitive periods.

Regional corruption measures add another dimension of institutional analysis, with higher corruption levels consistently hampering bank lending capacity [@weill_HowCorruptionAffects_2011]. The coefficients, ranging from -0.182 to -0.340, indicate that corruption operates as a significant impediment to efficient financial intermediation, creating an environment where personal relationships and informal networks assume heightened importance for institutional survival.

#### Market structure and competitive dynamics {.unnumbered}

Competition research yields counterintuitive findings regarding market structure effects, further highlighting the unique characteristics of Russian banking. The Lerner index investigations demonstrate that increased competition paradoxically enhances failure probability, with coefficients ranging from -1.460 to -3.364 [@fungacova_DoesCompetitionInfluence_2013a]. This evidence supports the "competition-fragility" hypothesis, suggesting that competitive pressures reduce franchise values and encourage excessive risk-taking behaviours amongst Russian banks.

These competitive dynamics interact with the institutional environment to create conditions where traditional market mechanisms may prove insufficient for ensuring institutional stability, thereby elevating the importance of alternative governance mechanisms including network relationships and informal coordination.

#### Factional networks and informal power structures {.unnumbered}

Recent studies have unveiled sophisticated informal influence mechanisms operating within Russian banking, providing crucial insights into how relationships transcend conventional ownership categories. @soldatkin_FactionalismCompetitionEfficiency_2020 provides evidence regarding the dual-layered nature of factional influence. Media-based factional associations demonstrate overwhelmingly positive effects on institutional performance, with fully faction-associated banks enjoying approximately 1.2 billion roubles in additional profits and asset bases 195 times larger than non-associated counterparts. This study relied on a natural language processing (NLP) approach to identifying factional connections, and may have been prone to misclassifying some banks as faction-associated, but the results are still worth considering. 

Critically, these media associations correlate with substantially reduced licence revocation probabilities (coefficients: -330.4 to -385.0), suggesting that public visibility of factional connections serves as an implicit guarantee of institutional support. This finding implies sophisticated signalling mechanisms wherein media coverage of political connections provides protective effects through reputation and implicit state backing.

Ownership-based factional influence presents markedly different patterns. Whilst factional ownership correlates positively with total assets, it demonstrates inverse relationships with profitability ratios, suggesting potential agency costs and resource misallocation within faction-controlled institutions. The granular analysis reveals heterogeneous effects across faction types, with siloviki ownership providing protective effects against licence revocation, whilst government/presidential faction ownership paradoxically increases risks of termination.

These factional dynamics establish the conceptual foundation for examining how family relationships and kinship networks—representing another form of informal governance mechanism—might influence institutional survival. The transition from faction-based to family-based analysis requires understanding how interpersonal relationships create alternative governance structures that can substitute for or complement formal institutional mechanisms.

#### Summary {.unnumbered}

In sum, the empirical literature on Russian banking failures establishes a robust foundation of financial, political, and institutional determinants that shape survival probabilities. However, due to data constraints up to now, it has not been possible to quantify the extent of family ownership and kinship networks within the sector, nor to systematically examine how these informal governance mechanisms interact with traditional financial indicators and political factors. What follows is an account of family ownership and management literature, which provides the theoretical foundations for understanding how family networks may serve as alternative governance mechanisms in the context of Russian banking.

### Family ownership 

#### Theoretical foundations and definitional frameworks {.unnumbered}

The theoretical foundations underlying family firm research present a compelling departure from the conventional Anglo-American model of dispersed ownership and professional management that has historically dominated corporate governance discourse. As empirical evidence accumulates across diverse institutional contexts, we observe that family firms constitute a predominant organisational form globally, challenging the universality of agency theory frameworks developed primarily from observations of publicly-held corporations in the United States and United Kingdom [@barontini_EffectFamilyControl_2006; @gomez-mejia_BindThatTies_2011; @yoshikawa_FamilyControlOwnership_2010].

Continental European markets, East Asian economies, and substantial portions of large American corporations exhibit significant family influence, with empirical studies documenting families present in one-third of S&P 500 firms [@anderson_FoundingFamilyOwnershipFirm_2003; @bertrand_MixingFamilyBusiness_2008]. Western European markets demonstrate even more pronounced family control, with nearly half of firms operating under family governance structures [@faccio_UltimateOwnershipWestern_2002; @yoshikawa_FamilyControlOwnership_2010]. These observations suggest that family influence represents not merely a transitional organisational form, but rather a persistent governance mechanism under specific institutional conditions—conditions that may closely parallel those observed in contemporary Russian banking.

The empirical literature reveals considerable heterogeneity in defining what constitutes a "family firm," employing diverse proxies that reflect varying theoretical emphases [@gomez-mejia_BindThatTies_2011; @miller_LostTimeIntergenerational_2003]. This definitional complexity parallels the challenges in identifying factional networks within Russian banking, where influence mechanisms may operate through ownership, management, or more subtle relationship channels.

#### Socioemotional wealth and non-financial motivations {.unnumbered}

The concept of socioemotional wealth (SEW) explains the potential non-financial or affective endowments that family owners derive from their enterprises [@gomez-mejia_BindThatTies_2011; @miller_LostTimeIntergenerational_2003]. This framework acknowledges that family owners may prioritise non-economic utilities alongside traditional financial objectives—--a perspective highly relevant for understanding Russian banking, where political and social considerations often influence business decisions. The preservation of SEW combines emotional attachment, legacy considerations, maintenance of family control, reputational concerns, and social ties, all of which influence managerial decision-making in ways that may diverge from pure profit maximisation [@gomez-mejia_BindThatTies_2011]. These motivations can ensure governance mechanisms that prioritise long-term relationships over short-term financial gain, potentially conferring additional stability on the institution and making it less likely to fail. 

#### Institutional context and implications for performance {.unnumbered}

The relationship between family ownership and firm performance demonstrates considerable context dependence, with empirical evidence producing mixed results across institutional environments [@barontini_EffectFamilyControl_2006; @gomez-mejia_BindThatTies_2011; @yoshikawa_FamilyControlOwnership_2010]. Positive performance effects appear predominantly in environments characterised by institutional underdevelopment, where family networks provide valuable coordination and information-sharing functions [@anderson_FoundingFamilyOwnershipFirm_2003; @khanna_EstimatingPerformanceEffects_2001].

Business group research offers particularly relevant insights, with group affiliation demonstrating significant country-specific effects—positive implications for performance in emerging markets such as India, Indonesia, and Taiwan, but negative or neutral effects in more developed institutional environments [@khanna_EstimatingPerformanceEffects_2001]. These differential effects relate directly to institutional development levels, with group affiliation providing valuable intermediation services in contexts with underdeveloped capital markets and weak regulatory frameworks [@frye_GoverningBankingSector_2006]---conditions that closely characterise the Russian banking environment.

#### Generational dynamics and network evolution {.unnumbered}

Recent research has identified generational transitions as critical moderating factors in family firm performance, with founder-controlled corporations consistently demonstrating superior performance compared to descendant-managed enterprises [@villalonga_HowFamilyOwnership_2006; @bertrand_MixingFamilyBusiness_2008]. This generational distinction assumes particular relevance for understanding Russian banking, where many institutions established during the 1990s transition period may now be experiencing first-generation succession dynamics.

The mechanisms underlying performance variation across generations include potential agency conflicts, reduced managerial quality due to limited selection pools, and increased emphasis on relationship preservation over financial performance [@bertrand_MixingFamilyBusiness_2008]. Particularly striking evidence from Thai business groups demonstrates that family size and composition significantly influence performance outcomes, with each additional son reducing ROA by -0.34 coefficient points [@bertrand_MixingFamilyBusiness_2008].

#### Network effects and survival mechanisms {.unnumbered}

The literature demonstrates that family ownership enhances network formation propensity and creates superior crisis recovery mechanisms through enhanced social capital [@ghinoi_FamilyFirmNetwork_2024; @lin_SocialNetworksListed_2022]. These network effects operate through multiple channels: information sharing, mutual support during financial distress, coordinated strategic decision-making, and enhanced access to informal credit markets.

Network centrality research reveals that higher centrality positions correlate with lower hazard rates and improved recovery prospects during institutional crises [@bagley_NetworksGeographySurvival_2019; @lin_SocialNetworksListed_2022]. This evidence suggests that family networks may provide institutional substitutes for formal governance mechanisms, particularly valuable in environments characterised by regulatory uncertainty and weak formal institutions.

### Summary and research gaps {.unnumbered}

This review of literature across Russian banking and family ownership reveals several critical research gaps that our study addresses. 

First, whilst the Russian banking literature extensively documents political and ownership effects on survival, it has not systematically examined how kinship networks and family relationships create alternative governance mechanisms. 

Second, the factional ownership research demonstrates the importance of informal relationships but does not explore how family connections intersect with or complement political associations. Additionally, previous measures of such associations have been rather inexact and prone to misclassification, which this study remedies. 

Third, the family ownership literature provides robust theoretical frameworks for understanding network-based governance but has not been applied to banking institutions in transitional economies characterised by weak formal institutions and high political interference. Our study bridges these gaps by incorporating family network characteristics into the analysis of Russian bank survival, thereby extending both the empirical understanding of Russian banking dynamics and the theoretical application of family governance mechanisms to financial institutions.

The synthesis of these streams of research suggests that family networks may serve as crucial institutional substitutes in the Russian banking context, providing coordination, information-sharing, and risk-mitigation functions that complement formal governance mechanisms. This theoretical integration informs our empirical approach and hypothesis development, enabling us to examine how family connections interact with traditional financial indicators and political factors to influence bank survival outcomes.

## Hypotheses

The above synthesis of the current state of research on banking outcomes has led us to propose the following hypotheses regarding the influence of family ownership and kinship networks on bank survival in Russia:
<!-- \begin{hyp}[H\ref{hyp:first}] \label{hyp:first}
Banks embedded within family ownership networks demonstrate superior survival prospects compared to banks lacking familial connections, controlling for traditional financial performance indicators.
\end{hyp} -->

```{=latex}
\begin{hyp}\label{hyp:first}
Banks embedded within family ownership networks demonstrate superior survival prospects compared to banks lacking familial connections, controlling for traditional financial performance indicators.
\end{hyp}
```

This hypothesis builds directly upon the family ownership literature demonstrating positive performance effects in weak institutional environments [@khanna_EstimatingPerformanceEffects_2001; @anderson_FoundingFamilyOwnershipFirm_2003], whilst addressing the identified gap regarding family networks in Russian banking. The theoretical foundation rests on the institutional substitution argument—--that family networks provide coordination, information-sharing, and mutual support mechanisms that compensate for deficiencies in formal governance structures. Given Russia's documented institutional weaknesses, including corruption, political interference, and regulatory uncertainty, family networks should function as alternative governance mechanisms that enhance institutional resilience.
The hypothesis permits empirical testing through logistic regression and Cox survival analysis comparing banks with varying degrees of family network embeddedness, whilst controlling for the established CAMEL factors and political variables documented in the Russian banking literature. This approach extends the factional network findings of @soldatkin_FactionalismCompetitionEfficiency_2020 by examining kinship-based rather than political association networks.

```{=latex}
\begin{hyp}\label{hyp:second}
Banks positioned within densely connected family network clusters demonstrate enhanced survival prospects compared to banks with sparse family connections, with effects mediated through improved access to coordinated strategic decision-making.
\end{hyp}
```

This hypothesis incorporates insights from network structure research [@vitali_CommunityStructureGlobal_2014; @bagley_NetworksGeographySurvival_2019] to examine how the topology of family relationships influences survival outcomes. The theoretical foundation emphasises that network benefits derive not merely from family ownership per se, but from positioning within broader kinship structures that enable resource sharing, information transmission, and coordinated responses to regulatory pressures.

The hypothesis distinguishes between banks with isolated family connections and those embedded within comprehensive family network clusters, predicting that network density and centrality measures will correlate positively with survival prospects. This approach parallels the factional network research demonstrating differential effects of media visibility versus ownership concentration, suggesting that family network benefits are based on network-topological characteristics rather than simple presence.

## Data

::: {#fig-database-schema-simplified fig-cap="A simplified schema of the Neo4j graph database of ownership and management of Russian banks"}

![](./figures/database_schema.pdf)

:::

This study uses a unique graph database of ownership and management of Russian banks which consists of ownership and control statements by the CBR; compliance data from various government sources compiled by Repuration.ru, and accounting statements from the CBR for CAMEL variables. The full description of the dataset building process is documented in a separate paper [REFERENCE]. @fig-database-schema-simplified presents a simplified schema from the database, which is based on the property graph model. Compared to traditional relational database management systems, which uses a combiantion of primary and foreign keys, a graph gatabase relies on nodes and relationships with their embedded metadata to be able to traverse the graph and retrieve the required connections alongside their data. 

In @fig-database-schema-simplified, we can observe that there are `:Bank` nodes which are owned or managed by `:Person` nodes, governemnt-related nodes such as a `:MunicipalSubject`, `:StatePropMgmt`, or `:CentralBank` nodes. `:MANAGEMENT` relationships contain metadata on the status of those relationships (whether they are active or not), their type (the name of a person's position), and the date associated with that position. The `Size` property is equal to 1 if the person still occupies that position and 0.1 if they do not. `:OWNERSHIP` relationships contain similar metadata on dates and actuality of the data, and the `Size` property is responsible for the percatage of shares held. `:FAMILY` relationships contain data on the type of the relationship and the source of the data used to obtain it: either the CBR ownership statements or imputation based on last names and patronymics[^patronymics]. 

[^patronymics]: The family relationships were obtained from the full names and patronymics of the owners in the CBR statements, as well as imputed based on the Levenshtein distance, a string similarity metric [@yujian_NormalizedLevenshteinDistance_2007], of their surnames with a cutoff similarity value of 0.88 for last names and 0.55 for patronymics, which were chosen as a good middle ground missing fewer actual family relationships and not including spurious matches. The full query for this procedure can be found in @lst-family-heuristics.   

## Methodology


### Metrics

In this paper, we examine financial metrics commonly used in the literature on bank performance and survival---the so-called CAMEL factors, primarily comprising accounting ratios. Apart from those, we incorporate a suite of measurements based on familial ties, foreign and state ownership, an overall ownership complexity score, and network topology metrics. The complete list of metrics is presented in @tbl-metrics-description, and the key to reading the formulae can be found in @tbl-metrics-notation. Here we present a brief description of the most important metrics used in the analysis. 


#### CAMEL factors

::: {#tbl-camel-metrics-description tbl-cap="A brief description of the main CAMEL metrics used in the analysis."}

| Metric | Description |
|--------|-------------|
|**C**apital adequacy|
| $\frac{Tier1}{Assets}$ | Tier 1 capital ratio: proportion of highest-quality capital relative to total assets |
|**A**sset quality|
| $LR(b)$ | Leverage ratio: measure of financial leverage and capital structure stability |
| $\frac{NPL}{Loans}$ | Non-performing loans ratio: proportion of loans in default or close to default |
| $\frac{LLP}{Loans}$ | Loan loss provisions ratio: provisions for expected credit losses relative to total loans |
|**M**anagement quality|
| $\frac{Cost}{Income}$ | Cost-to-income ratio: operational efficiency measure comparing costs to income |
| $\frac{NIE}{Assets}$ | Non-interest expense ratio: operational expenses relative to total assets |
|**E**arnings||
| $\frac{Revenue}{Assets}$ | Asset turnover ratio: efficiency of asset utilisation in generating revenue |
| $ROA(b)$ | Return on assets: profitability measure indicating earnings per unit of assets |
| $ROE(b)$ | Return on equity: profitability measure indicating earnings per unit of equity |
| $NIM(b)$ | Net interest margin: difference between interest earned and paid, relative to assets |
|**L**iquidity|
| $\frac{LA}{TA}$ | Liquid assets ratio: proportion of easily convertible assets to total assets |
| $\frac{Loans}{Deposits}$ | Loan-to-deposit ratio: measure of liquidity and funding structure efficiency |

:::

The selection of these CAMEL indicators presented in @tbl-camel-metrics-description reflects their established significance in banking supervision and their capacity to capture fundamental dimensions of institutional financial health within the Russian banking context. However, the interpretation of these metrics requires careful consideration of the unique institutional environment and potential regulatory endogeneity effects that may distort conventional analytical frameworks.

**Capital adequacy metrics** such as the Tier 1 capital ratio and leverage ratio ostensibly measure a bank's financial resilience and capacity to absorb losses. A _high capital ratio_ may indicate $(1)$ conservative management practices and robust financial positioning that enhances survival prospects during economic stress, or $(2)$ regulatory mandates requiring specific institutions to maintain elevated capital buffers as part of systemic risk management strategies. Conversely, a _low capital ratio_ might reflect $(1)$ aggressive growth strategies and efficient capital deployment, or $(2)$ deteriorating financial conditions that have eroded the institution's capital base through operational losses or regulatory sanctions.

**Asset quality indicators** including non-performing loans ratios and loan loss provisions capture the credit risk embedded within a bank's portfolio. _Elevated NPL ratios_ may signify $(1)$ deteriorating economic conditions affecting borrower repayment capacity, or $(2)$ previous aggressive lending practices that prioritised growth over credit quality. However, within the Russian context, high NPL ratios might alternatively reflect $(3)$ banks' involuntary acquisition of distressed loan portfolios during regulatory consolidation processes, thereby transforming asset quality metrics into indicators of regulatory burden rather than management competence.

**Management quality measures** such as cost-to-income ratios and operational efficiency indicators theoretically reflect managerial competence and strategic effectiveness. _Superior cost efficiency_ may indicate $(1)$ skilled management capable of optimising operational processes and maintaining competitive positioning, or $(2)$ banks benefiting from economies of scale or regulatory advantages that reduce operational burdens. Conversely, _poor efficiency metrics_ might reflect $(1)$ inadequate management capabilities or adverse market conditions, or $(2)$ banks bearing disproportionate regulatory compliance costs or mandated participation in sector-wide policy implementation.

**Earnings indicators** including return on assets, return on equity, and net interest margins measure profitability and revenue generation effectiveness. _Strong profitability metrics_ may reflect $(1)$ successful business strategies and competitive positioning within dynamic market conditions, or $(2)$ regulatory forbearance or implicit subsidies that enhance reported earnings. However, _weak earnings performance_ might indicate $(1)$ challenging market conditions or strategic missteps, or $(2)$ banks absorbing losses from regulatory mandates requiring them to support distressed institutions or implement policy objectives that prioritise financial stability over profitability.

**Liquidity measures** such as liquid assets ratios and loan-to-deposit ratios assess a bank's capacity to meet short-term obligations and funding stability. _High liquidity ratios_ may indicate $(1)$ prudent risk management and preparation for potential funding stress, or $(2)$ inability to deploy capital effectively in lending activities due to market constraints or regulatory restrictions. _Low liquidity ratios_ might reflect $(1)$ efficient capital deployment and strong lending growth, or $(2)$ funding pressures arising from deposit outflows or limited access to interbank markets during periods of financial stress.

The interpretation of these CAMEL indicators within the Russian banking sector requires explicit acknowledgement that regulatory intervention and state-directed policies may systematically distort the relationship between financial metrics and institutional performance. Banks exhibiting apparently strong CAMEL indicators may be disproportionately selected for participation in regulatory stabilisation efforts, whilst institutions with weaker metrics might benefit from implicit state support that enhances survival prospects despite underlying financial vulnerabilities. This institutional context necessitates careful analytical consideration of temporal dynamics and regulatory policy evolution when employing CAMEL indicators as predictors of bank survival or performance within an economic environment characterised by extensive state intervention in the financial sector.

::: {#tbl-metrics-notation tbl-cap="A key for reading formulae in @tbl-metrics-description."}

| Symbol | Description |
|--------|-------------|
| $b$ | Specific bank of interest |
| $D_b$ | Set of direct owners of bank $b$ |
| $\omega_i$ | Ownership value (face value) held by owner $i$ |
| $\mathbf{1}_{F}(i)$ | Indicator function equals 1 if owner $i$ has family connections, 0 otherwise |
| $\phi(v)$ | Function indicating if entity $v$ is foreign (1) or domestic (0) |
| $N_F(i)$ | Set of family members connected to owner $i$ |
| $V$ | Set of all nodes in the graph |
| $P_b$ | Set of ownership paths to bank $b$ (up to 5 hops) |

:::

#### Network topology 

As per the extensive network science literature [@newman_StructureFunctionComplex_2003], we use metrics presented in @tbl-network-metrics-description to measure the position of a bank in the ownership network, as implemented in the Neo4j graph database [@robinson_GraphDatabases_2015]. 

::: {#tbl-network-metrics-description tbl-cap="A brief description of the main network metrics used in the analysis."}

| Metric | Description |
|--------|-------------|
| $C_{in}(v)$ | In-degree centrality: number of direct owners or managers of bank $b$ |
| $C_{out}(v)$ | Out-degree centrality: number of banks or companies owned by bank $b$ |
| $C_{close}(v)$ | Closeness centrality: average distance to all other banks nodes in the network [@wasserman_SocialNetworkAnalysis_1994]|
| $C_{between}(v)$ | Betweenness centrality: number of shortest paths between all pairs of nodes that pass through bank $b$ [@brandes_CentralityEstimationLarge_2007] |
| $C_{eigen}(v)$ | Eigenvector centrality: measures the influence of a bank based on the strength of its connections [@bonacich_UniquePropertiesEigenvector_2007]|
| $PR(v)$ | PageRank: measures the influence of a bank based on the strength of its connections, with an additional jump probability compared to $C_{eigen}(v)$ [@manaskasemsak_EfficientPartitionBasedParallel_2005] |

:::

The choice of these metrics is dictated by their ability to capture different aspects of a bank's position in the ownership and management network, such as its connectivity, influence, and centrality. In-degree and out-degree are simple measures of the number of direct incoming and outgoing connections a bank has, which can indicate the number of diverse interests in its immediate ownership structure. Such a distributed nature of bank ownership can have multiple interpretations: a _high in-degree_ may indicate that $(1)$ the bank is owned by a large number of small shareholders, which may lead to a more democratic governance structure and less concentration of power. Conversely, $(2)$ it may signal an attempt at deliberate obfuscation of ultimate control where there are numerous interconnected entities, either people or companies, with a small number of actual decision-makers. A _high out-degree_ may be the sign of $(1)$ a bank that is actively expanding its ownership portfolio, which may be the result of having a healthy balance sheet and a willingness to take on risk, or $(2)$ it may have been pushed to take on ownership stakes in failing banks as part of the Central Bank's clean-up policy. 

Closeness centrality measures how quickly a bank can reach all other nodes in the network, be it a person, a company, another bank, or a government entity. Similarly to degree centrality, there are multiple interpretations of this measure: a _high closeness centrality_ may $(1)$ indicate that the bank is well-connected and can quickly access information and resources, which may be beneficial for its survival. Conversely, $(2)$ it may also indicate that the bank is too close to other banks, which may lead to contagion effects in case of industry consolidataion or a systemic crisis. 

Eigenvector centrality and PageRank are more sophisticated measures that take into account the relative influence of a bank's connections, rather than just their raw count. These metrics reflect the principle that relationships with powerful stakeholders confer greater influence than relationships with peripheral actors. In the Russian context, high eigenvector centrality may be a sign that a bank is $(1)$ owned or managed by individuals with significant political connections, $(2)$ that the banks positioned to benefit from relationships with systemically important institutions, or $(3)$ that such a position is the result of the Central Bank's cleansing policy. 

Betweenness centrality measures how often a bank lies on the shortest path between other nodes that would otherwise be in disparate parts of the network. Some potential interpretations of a _high betweenness centrality_ are that the bank is $(1)$ a key intermediary in the ownership network, $(2)$ a potential bottleneck for information flow, or $(3)$ a potential target for regulatory scrutiny due to its central position. Alternatively, $(4)$ banks occupying high betweenness positions may be compelled to facilitate ownership transfers, asset redistributions, or management transitions that serve regulatory objectives rather than the institution's strategic interests. The apparent network centrality reflects systemic utility to regulators rather than competitive market positioning.

In sum, the interpretation of these network centrality measures is fraught with ambiguity, as they may either reflect strategic positioning or result _ipso facto_ from Central Bank policy interventions. The latter may have been implemented to ensure that the banking sector remains stable and resilient, but may also lead to unintended consequences such as increased concentration of ownership or reduced competition. This complexity necessitates a more judicious approach to constructing metrics, which is why we also include family, state, and foreign ownership metrics, alongside a comprehensive ownership complexity score, which are described below.

#### Family ownership/management indicators {.unnumbered}

::: {#tbl-family-ownership-indicators tbl-cap="A brief description of the main family ownership indicators used in the analysis."}

| Metric | Description |
|--------|-------------|
| $FOP(b)$ | Family ownership percentage: proportion of bank ownership held by family-connected entities |
| $\rho_F(b)$ | Family connection ratio: density of family relationships relative to total ownership structure |
| $\|F_b\|$ | Total family connections: absolute count of family relationships amongst bank stakeholders |
| $FOV_d(b)$ | Direct family ownership value: monetary value of ownership stakes held by family members |
| $\|C_F(b)\|$ | Family-controlled companies: number of companies controlled by family members with ownership stakes |

:::

The selection of family ownership indicators reflects their theoretical capacity to capture kinship-based governance mechanisms that may substitute for formal institutional frameworks within transitional economic environments. However, the interpretation of these metrics requires sophisticated understanding of how family networks operate within the specific regulatory and political economy context of Russian banking, where informal relationships may either enhance institutional resilience or create vulnerabilities to regulatory intervention.

**Family ownership concentration measures** such as family ownership percentage and direct family ownership value ostensibly indicate the extent of kinship-based control within institutional governance structures. _High family ownership concentration_ may signify (1) effective informal governance mechanisms that provide enhanced monitoring, long-term strategic orientation, and crisis resilience through family network support, or (2) potential agency conflicts arising from concentrated control that prioritises family interests over broader stakeholder welfare or regulatory compliance. Conversely, _dispersed family ownership_ might reflect (1) professional management structures with reduced family interference in operational decisions, or (2) deliberate obfuscation of ultimate beneficial ownership through complex family network structures designed to circumvent regulatory scrutiny.

**Family network density indicators** including the family connection ratio provide crucial insights into the quality versus quantity of kinship relationships within ownership structures. _Dense family networks_ characterised by high connection ratios may indicate (1) cohesive family governance that facilitates coordinated strategic decision-making and resource mobilisation during financial stress, or (2) potential coordination failures arising from competing family interests or generational conflicts that complicate institutional management. The empirical evidence suggesting negative relationships between absolute family connection counts and survival probability illuminates the critical distinction between network quality and quantity, wherein extensive but dispersed family involvement may create governance complications rather than coordination benefits.

**Family-controlled intermediary structures** reflected in family-controlled company counts capture the sophistication of family network organisation and potential regulatory arbitrage mechanisms. _Complex family intermediary structures_ may indicate (1) sophisticated strategic planning that utilises family networks to optimise regulatory compliance, tax efficiency, or risk management, or (2) deliberate opacity mechanisms designed to obscure ultimate beneficial ownership and complicate regulatory oversight. Within the Russian institutional context, such structures might alternatively reflect (3) family networks' adaptive responses to evolving regulatory frameworks that require sophisticated ownership engineering to maintain effective control whilst satisfying formal compliance requirements.

#### State ownership indicators


::: {#tbl-state-ownership-indicators tbl-cap="A brief description of the main state ownership indicators used in the analysis."}

| Metric | Description |
|--------|-------------|
| $SOP(b)$ | State ownership percentage: proportion of bank ownership held by state entities |
| $SOV_d(b)$ | State direct ownership value: monetary value of direct state ownership stakes |
| $SCC(b)$ | State-controlled companies: number of state-controlled entities with ownership stakes |
| $SCP(b)$ | State control paths: number of ownership pathways through which state influence operates |

:::

State ownership indicators capture the extent and sophistication of government involvement in banking sector governance, reflecting both explicit policy objectives and implicit regulatory preferences that may substantially influence institutional survival prospects. The interpretation of these metrics requires careful consideration of the evolving relationship between state authorities and financial institutions within Russia's state-directed economic development framework.

**Direct state ownership measures** including state ownership percentage and direct ownership value represent the most transparent mechanisms through which government authorities exercise influence over banking sector operations. _High direct state ownership_ may indicate (1) explicit government strategic interest in maintaining control over systemically important financial institutions to implement macroeconomic policy objectives, or (2) regulatory intervention in distressed institutions where state ownership reflects crisis management rather than strategic investment. However, _limited direct state ownership_ might reflect (1) government preference for indirect influence mechanisms that maintain operational autonomy whilst preserving policy coordination capacity, or (2) deliberate regulatory strategies that avoid explicit state control whilst maintaining informal influence through alternative channels.

**Indirect state influence mechanisms** captured through state-controlled company counts and control pathway measures reveal the sophistication of government involvement in banking sector governance. _Complex state control structures_ may signify (1) strategic institutional design that enables flexible policy implementation whilst maintaining arm's-length relationships with individual institutions, or (2) regulatory arbitrage mechanisms that circumvent formal constraints on state ownership whilst preserving effective government influence. The multiplicity of state control pathways might alternatively indicate (3) institutional legacy effects from privatisation processes that created complex ownership structures linking state entities with nominally private financial institutions.

**State involvement temporal dynamics** require particular analytical attention given the evolving nature of Russian state-banking relationships. State ownership indicators may reflect different causal mechanisms across temporal periods, with early post-transition state involvement potentially representing privatisation residuals, whilst contemporary state ownership might indicate strategic re-nationalisation efforts or crisis intervention responses.

#### Foreign ownership/management indicators {.unnumbered} 

::: {#tbl-foreign-ownership-indicators tbl-cap="A brief description of the main foreign ownership indicators used in the analysis."}

| Metric | Description |
|--------|-------------|
| $FOP_d(b)$ | Foreign direct ownership percentage: proportion of direct ownership by foreign entities |
| $FOP_t(b)$ | Total foreign ownership percentage: combined direct and indirect foreign ownership |
| $FEC_d(b)$ | Foreign entity count: number of foreign entities with direct ownership stakes |
| $FCC(b)$ | Foreign-controlled companies: number of foreign-controlled entities with ownership stakes |
| $FCD(b)$ | Foreign country diversity: number of different countries represented in ownership structure |

:::

Foreign ownership indicators reflect the international integration of Russian banking institutions and potential sources of external capital, expertise, and diplomatic protection that may influence survival prospects. However, the interpretation of these metrics requires explicit consideration of geopolitical dynamics and evolving regulatory frameworks that may systematically alter the relationship between foreign involvement and institutional outcomes.

**Foreign ownership concentration measures** including direct and total foreign ownership percentages capture the extent of international capital participation in Russian banking sector development. _High foreign ownership concentration_ may indicate (1) access to international capital markets, advanced risk management practices, and professional governance standards that enhance institutional resilience, or (2) potential vulnerability to geopolitical tensions or diplomatic conflicts that may precipitate regulatory retaliation against foreign-controlled institutions. The substantial protective effects observed empirically suggest that foreign ownership provides significant survival advantages, potentially through (3) implicit diplomatic protection that constrains regulatory intervention against institutions with significant international stakeholder interests.

**Foreign stakeholder diversity indicators** reflected in foreign entity counts and country diversity measures capture the sophistication and risk distribution of international involvement. _Diversified foreign ownership_ across multiple countries and entities may provide (1) portfolio risk reduction effects that insulate institutions from country-specific political or economic shocks, or (2) enhanced negotiating position with regulatory authorities who must consider multiple international relationships when contemplating intervention decisions. Conversely, _concentrated foreign ownership_ might indicate (3) strategic partnerships with specific international institutions that provide specialised expertise or market access, or (4) potential vulnerability to bilateral diplomatic tensions that could precipitate regulatory complications.

**Foreign control mechanism sophistication** captured through foreign-controlled company indicators reveals the complexity of international involvement in Russian banking governance. _Sophisticated foreign control structures_ may reflect (1) strategic institutional design that optimises regulatory compliance whilst maintaining effective international oversight and coordination, or (2) regulatory arbitrage mechanisms that enable foreign stakeholders to exercise influence whilst satisfying formal restrictions on foreign ownership in strategically sensitive sectors. The temporal evolution of these indicators requires particular attention given the dynamic geopolitical environment affecting international investment in Russian financial institutions, with recent regulatory changes potentially altering the relationship between foreign involvement and institutional survival prospects.

### Expected relationships with bank survival

Based on the existing literature as it is applied to the Russian context (see [@tbl-survival-factors-literature]), we can hypothesise the direction of that relationship with bank survival prospects. 

Firstly, family ownership indicators are expected to correlate positively with the likelihood of survival, as family connections provide informal governance mechanisms that enhance institutional resilience in the face of regulatory uncertainty and political interference. The family ownership percentage ($FOP(b)$) and direct family ownership value ($FOV_d(b)$) are expected to have positive coefficients in survival models, indicating that banks with higher family ownership are less likely to fail. @faccio_PoliticallyConnectedFirms_2006 posits that political connections can enhance the prospects of regulatory forbearance and preferential treatment, which may also apply to family connections in the Russan context. 

Secondly, foreign ownership metrics are expected to demonstrate a similar protective effect against failure, in line with the findings of @barajas_SurvivalRussianBanks_2023. The total foreign ownership percentage ($FOP_t(b)$) and direct foreign ownership value ($FOV_d(b)$) are anticipated to have positive coefficients due to a more direct access international capital markets and diversified risk profiles, in addition to the potential for foreign entities to have a more direct channel of communication with the Russian state through diplomatic and informal channels, especially if the said foreign entity is not just a foreign commercial entity, but a state-owned bank or a sovereign wealth fund. Such survival prospects may also be explained by regulatory forebearance [@claeys_BankSupervisionRussian_2007; @claeys_OptimalRegulatoryDesign_2005], where the Central Bank may be more lenient towards foreign-owned banks due to their perceived importance for the Russian economy or geopolitical considerations---that is, a bank may indeed be 'too foreign to fail'. At the same time, we have to be mindful of the exact nature of those foreign connections and the environment in which those foreign banks were operating at the time: banks from 'friendly' countries such as China or Kazakhstan may have been more likely to receive regulatory forbearance, whereas banks from 'unfriendly' states that imposed sanctions on Russian government officials, certain wealthy individuals, state-owned assets, and banks may have been more likely to be subject to reciprocal measures from the Russian government. 

Thirdly, network centrality measures are expected to have a less clear-cut effect on the survival outcomes as they may represent the consequences of the clean-up policy of the Central Bank. In-degree centrality ($C_{in}(v)$) might indicate the number of direct owners or managers, which may be higher if the bank has gone through a restructuring process and may thus have more ownership connections to other banks which may have been forced to take on their balance sheet. Out-degree centrality ($C_{out}(v)$) may conversely indicate that the bank is on the other end of such actions, i.e. that due to a healthier balance sheet, it may have taken on ownership stakes in other banks. PageRank ($PR(v)$) and eigenvector centrality ($C_{eigen}(v)$), both of which measure the influence of a node based on the strength of its connections, are expected to have positive coefficients as they take into account the `Size` property of the `:OWNERSHIP` relationship, ie. looking at the ownership stakes of the owners, rather than just the number of connections. Again, the resulting metric may be the result of CBR policies where the causality may have been reversed, i.e. the CBR may have incentivised those banks to take on ownership stakes in failing banks, rather than the other way around. Similarly, banks with high closeness and betweenness centrality measures ($C_{close}(v)$ and $C_{between}(v)$) may have obtained such a position due to a healthy balance sheet, a relatively high number of political or administrative connections, or both [@faccio_PoliticallyConnectedFirms_2006].  

Finally, ownership complexity metrics are expected to correlate positively with survival prospects. The ownership complexity score ($C_b$), which combines average path length and unique owners in the immediate vicinity of a bank, is a proxy for diverse interests and a more convoluted ownership structure, which in turn may confer resilience on the bank by providing more opportunities to make amends for any potential wrongdoings in front of the Central Bank. With that in mind, we also have to be aware that the ownership complexity score may also be similarly influenced by the CBR policies and needs to take temporal changes into account. 

### Model specifications 

To study the possible determinants of bank survival, we employ a series of logistic regression models that interatively incorporate the metrics described above (see tables [-@tbl-camel-metrics-description; -@tbl-network-metrics-description; -@tbl-family-ownership-indicators, -@tbl-state-ownership-indicators; -@tbl-foreign-ownership-indicators]). First, we take a cross-sectional approach to model bank survival as a baseline for iterating on model specifications and not incorporating CAMEL indicators at this stage. The dependent variable is a binary indicator for whether the bank in question survived until the end of 2023, which is the end of the period covered by the data set. To avoid potential issues with multicollinearity, not every indicator is included in every model, and instead we specify combinations of factors that are theoretically justified and do not overlap in interpretation. 

The baseline model only includes bank age as a predictor. Subsequent models add the linear combinations of the respective family, state, and foreign ownership indicators, network centrality metrics, and the ownership complexity score. The full list of model specifications is presented in @tbl-simple-logistic-results.

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Family}] \label{eq:family} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{State}] \label{eq:state} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Foreign}] \label{eq:foreign} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Topology}] \label{eq:topology} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Opacity}] \label{eq:opacity} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Family} + \text{State}] \label{eq:family_state} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{Family} + \text{Foreign}] \label{eq:family_foreign} \\
\text{logit}(P(\text{survival})) &= \beta_0 + \beta_1 \times Age(b) + [\text{State} + \text{Foreign}] \label{eq:state_foreign} 
\end{align}
```

Similarly, we specify time-variable models that incorporate the linear combination of CAMEL indicators and the previously described ownership and network metrics. We also add a dummy for the crisis years of 2008-2009 and 2014-2015 to raw models to capture the effect of the Global Financial Crisis, the impact of Crimea-related sanctions, the the subsequent economic downturn. Furthermore, we specify an interaction effects model with crisis and family, state, and foreign ownership variables to account for the probability of survival under a certain ownership paradigm. The full list of model specifications and results is reported in @tbl-time-variable-logistic-results. 

## Results 

### Cross-sectional logistic regression results

::: {#fig-simple-model-effects-comparison fig-cap="Comparison of the effects of family ownership, foreign ownership, and network centrality metrics on bank survival in logistic regression models (only significant coefficients included)"}

![](./figures/simple_model_effects_comparison.pdf)

:::

Based on the comprehensive analysis of 14 different model specifications in @tbl-logistic-regression-results, we examine bank survival determinants ranging from simple baseline models to complex theoretical frameworks. The models are presented in order of increasing performance, as measured by the Akaike Information Criterion (AIC).


#### Model (1): Age only (Baseline)

The simplest baseline model includes only bank age as a predictor, establishing the fundamental relationship between institutional maturity and survival prospects. The model specification is:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) = -5.161 + 0.173 \times Age(b)
\end{align}
```

The intercept of $-5.161^{***}$ indicates that a hypothetical bank with zero years of operation would have extremely low survival odds (approximately 0.6% probability). The age coefficient of $0.173^{***}$ demonstrates a strong positive relationship between bank maturity and survival likelihood. Specifically, each additional year of operation increases the log-odds of survival by 0.173, corresponding to an 18.9% increase in survival odds ($\exp(0.173) = 1.189$). For practical interpretation, a 10-year difference in bank age translates to approximately 5.6 times higher survival odds.

Despite its simplicity, this baseline model achieves substantial explanatory power with a $Pseudo\ R^2$  of 0.299, explaining nearly 30% of the variance in survival outcomes. It also demonstrates the strongest classification performance across all models, with an $F_1$ score of 0.73, precision of 0.81, and recall of 0.67. This superior predictive performance suggests that bank age captures fundamental institutional stability that proves difficult to improve upon with additional variables.

#### Model (2): Topology (Network centrality)

The topology model tests whether network centrality measures predict bank survival, incorporating various measures of structural position within the banking network:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -4.498 + 0.157 \times Age(b) \\
& + 0.095 \times C_{out}(v) - 0.604 \times C_{close}(v) \\
&- 4.295 \times C_{eigen}(v)
\end{align}
```


The results reveal a striking pattern that contradicts conventional network theory expectations. The closeness centrality coefficient ($-0.604^{**}$) indicates that banks positioned closer to other institutions in the network face significantly lower survival prospects. Each unit increase in closeness centrality reduces survival log-odds by 0.604, corresponding to a 45% decrease in survival odds. Similarly, eigenvector centrality ($-4.295^*$) shows a massive negative effect, suggesting that banks connected to influential network nodes are substantially more likely to fail.

Conversely, out-degree centrality ($0.095^{**}$) demonstrates a positive effect, indicating that banks with more outgoing ownership connections have better survival prospects. This pattern strongly supports the endogeneity hypothesis discussed in the theoretical framework: rather than indicating strength, high centrality positions may reflect banks' roles as 'network firefighters' in the Central Bank's cleanup operations, forced to absorb failing institutions or take on distressed assets.

The model achieves a modest improvement in explanatory power ($Pseudo\ R^2 = 0.311$) over the baseline but suffers in classification performance ($F_1 = 0.69$), with notably reduced recall (0.61). This performance trade-off suggests that while network measures add explanatory value, they introduce noise that reduces practical predictive accuracy.

#### Model (3): Opacity as insurance

This model tests the hypothesis that ownership complexity and family connection density provide "insurance" against regulatory intervention through negotiation opportunities:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -5.058 + 0.151 \times Age(b) \\
& + 0.069 \times C_b + 0.001 \times |F_b|
\end{align}
```

The ownership complexity score ($0.069^{***}$) demonstrates a significant positive effect on survival probability. Each unit increase in complexity score raises survival log-odds by 0.069, representing a 7.1% increase in survival odds. This finding supports the theoretical prediction that complex ownership structures provide banks with more opportunities to negotiate favorable outcomes with regulators, potentially through multiple ownership layers that create ambiguity about ultimate control and responsibility.

However, the total family connections variable (0.001) proves non-significant, suggesting that raw family connection counts do not independently contribute to survival beyond what complexity captures. This pattern indicates that the quality and structure of relationships matter more than their simple quantity.

The model maintains similar explanatory power to the topology model ($Pseudo\ R^2 = 0.311$) but with improved $AIC$ (1289.90 vs. 1297.40), indicating better model fit when adjusting for the number of parameters. Classification performance ($F_1 = 0.67$) falls between the baseline and topology models, suggesting that opacity measures provide meaningful but limited predictive improvement.

Across these initial three models, several patterns emerge that will prove consistent throughout the analysis. First, bank age remains the most robust and significant predictor, with coefficients ranging from 0.151 to 0.173 across specifications. Second, the trade-off between explanatory power and predictive performance becomes apparent, with more complex models improving statistical fit while potentially reducing practical classification accuracy. Third, the counterintuitive network centrality results provide early evidence supporting the institutional context hypothesis that network positions in Russian banking reflect regulatory interventions rather than market-driven competitive advantages.


#### Model (4): State control

This model examines how various dimensions of state involvement affect bank survival prospects:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -4.971 + 0.159 \times Age(b) + 0.314 \times SCC(b) \\
&\quad + 0.011 \times SOP(b) + 0.000 \times SOV_d(b) - 0.000 \times SCP(b)
\end{align}
```

The results reveal that state-controlled companies ($0.314^{***}$) provide the most substantial protective effect among state-related variables. Each additional state-controlled company in a bank's ownership network increases survival log-odds by 0.314, representing a 37% increase in survival odds (exp(0.314) = 1.369). This finding suggests that connections to state-controlled entities—whether through direct ownership stakes or indirect control relationships—confer significant survival advantages, likely through preferential regulatory treatment or access to state resources during financial distress.

In contrast, direct state ownership measures prove largely insignificant. The state ownership percentage coefficient ($0.011$) lacks statistical significance, as do state direct ownership value ($0.000$) and state control paths ($-0.000$). This pattern indicates that formal state ownership stakes matter less than informal connections through state-controlled intermediaries, supporting theories about the importance of relationship-based governance in the Russian institutional context.

The model demonstrates improved explanatory power ($Pseudo\ R^2 = 0.314$) and better model fit ($AIC = 1287.03$) than complexity-only specifications. However, classification performance suffers slightly ($F_1 = 0.66$, $Recall = 0.58$), suggesting that while state connections provide statistical explanatory value, they may not translate directly into improved predictive accuracy.

#### Model (5): Family ownership

This model focuses specifically on family ownership stakes and control structures, distinguishing between direct ownership percentages and control through family-controlled companies:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -4.959 + 0.146 \times Age(b) \\
& + 0.052 \times |C_F(b)| \\
& + 0.008 \times FOP(b) + 0.046 \times C_b 
\end{align}
```

Family-controlled companies ($0.052^{**}$) demonstrate a significant positive effect on survival probability. Each additional family-controlled company increases survival log-odds by 0.052, corresponding to a 5.3% increase in survival odds. This effect, while statistically significant, proves more modest than state-controlled company effects, suggesting that family control networks provide meaningful but less powerful protection than state connections.

The family ownership percentage ($0.008^{*}$) shows a marginally significant positive effect, with each percentage point increase in family ownership raising survival log-odds by 0.008, or approximately 0.8% higher survival odds. This relatively small effect size indicates that the magnitude of family ownership matters less than the structural complexity through which it operates.

Notably, the ownership complexity coefficient ($0.046^{**}$) remains significant but with reduced magnitude compared to the complexity-only model (0.071 vs. 0.046), suggesting that family ownership partially mediates the complexity effect. This pattern supports theoretical predictions that family networks utilize complex structures strategically to enhance their influence and protection.

The model achieves the strongest performance among single-factor specifications ($Pseudo\ R^2 = 0.315$, $AIC = 1284.04$), indicating that family ownership structures capture important survival determinants. Classification performance ($F_1 = 0.66$) remains consistent with other complex models, though with slightly reduced recall ($F_1 = 0.66$, $Recall = 0.58$).

#### Model (6): Family networks

This comprehensive family model incorporates multiple dimensions of family involvement to test which aspects of family networks most effectively predict survival:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -5.014 + 0.146 \times Age(b) + 0.463 \times \rho_F(b) \\
&\quad + 0.062 \times C_b + 0.001 \times |D_b| - 0.002 \times |F_b|
\end{align}
```

The family connection ratio ($0.463^{***}$) emerges as the strongest family-related predictor, with each unit increase in family network density raising survival log-odds by 0.463, corresponding to a 59% increase in survival odds ($\exp(0.463) = 1.589$). This substantial effect size confirms that the intensity of family relationships within ownership structures, rather than their absolute quantity, drives survival advantages. The connection ratio captures how deeply embedded family networks are relative to the total ownership structure, suggesting that concentrated family influence provides more effective informal governance than dispersed family presence.

Intriguingly, total family connections ($-0.002^{**}$) exhibits a significant negative coefficient, indicating that raw family connection counts actually reduce survival probability when controlling for family network density. This counterintuitive finding supports the theoretical distinction between network quality and quantity: while dense family networks (high ratio) enhance survival through effective informal monitoring and resource mobilisation, extensive but dispersed family connections (high absolute count) may create coordination problems, conflicts of interest, or regulatory scrutiny that ultimately harm the institution.

The ownership complexity coefficient ($0.062^{***}$) maintains significance with moderate attenuation from single-factor models, while direct owners ($0.001$) proves statistically insignificant. This pattern suggests that family networks and complexity operate through partially overlapping mechanisms, with family relationships providing some of the negotiation advantages traditionally attributed to structural complexity.

The model achieves strong performance ($Pseudo\ R^2 = 0.315$, $AIC = 1283.01$) that improves substantially on single-factor family specifications, indicating that the tension between family network quality and quantity represents an important theoretical distinction for understanding informal governance mechanisms.

#### Model (7): Institutional substitution

This parsimonious model provides a clean test of the core institutional substitution hypothesis by focusing exclusively on the most theoretically relevant family network measure:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) &= -5.046 + 0.148 \times Age(b) \\
& + 0.490 \times \rho_F(b) + 0.066 \times C_b 
\end{align}
```

The family connection ratio ($0.490^{***}$) demonstrates an even stronger effect than in the comprehensive family model, with survival log-odds increasing by 0.490 per unit increase in network density, representing a 63% increase in survival odds ($\exp(0.490) = 1.633$). This enhanced effect size when isolated from competing family measures confirms that family network density captures the essential mechanism through which family relationships substitute for weak formal institutions in the Russian banking environment.

The ownership complexity coefficient ($0.066^{***}$) maintains strong significance and consistent magnitude across specifications, reinforcing its role as a complementary survival mechanism. The age effect ($0.148^{***}$) remains robust, indicating that institutional maturity and informal governance networks operate through distinct but mutually reinforcing channels.

This streamlined specification achieves identical explanatory power to the comprehensive family model ($Pseudo\ R^2 = 0.315$) while substantially improving model fit ($AIC = 1281.46$ vs. 1283.01), demonstrating the theoretical and statistical value of focusing on network quality rather than attempting to capture all dimensions of family involvement. Classification performance ($F_1 = 0.67$) remains consistent with other complexity models.

#### Model (9): Foreign ownership

This model examines how foreign ownership affects bank survival, incorporating both the magnitude and diversity of foreign involvement:

```{=latex}
\begin{align}
\text{logit}(P(\text{survival})) = &-5.056 + 0.153 \times Age(b) \\
& + 1.762 \times FOP_d(b) + 0.051 \times FCD(b) 
\end{align}
```

Foreign direct ownership percentage ($1.762^{***}$) emerges as the single most powerful predictor encountered across all model specifications. The coefficient indicates that a complete transition from 0% to 100% foreign direct ownership (a change of 1.0 in the fractional variable) increases survival log-odds by 1.762, corresponding to a 482% increase in survival odds ($\exp(1.762) = 5.82$). For more practical interpretation, each 1 percentage point increase in foreign ownership (a change of 0.01 in the variable) raises survival log-odds by 0.01762, representing approximately a 1.78% increase in survival odds ($\exp(0.01762) = 1.0178$). This massive effect size indicates that foreign ownership provides extraordinary protection against bank failure, far exceeding the protective effects of any domestic relationship or structural characteristic examined thus far.

The magnitude of this foreign ownership effect suggests multiple reinforcing mechanisms operating simultaneously. Foreign owners likely provide superior access to international capital markets, advanced risk management practices, and professional governance standards. Additionally, in the Russian context, foreign ownership may confer diplomatic protection that makes regulatory authorities more cautious about forced closures or aggressive intervention, particularly when foreign entities represent major international financial institutions or sovereign wealth funds---alternatively, such foreign entities may be less inclined to engage in opportunistic behaviour that could destabilise the institution.

Foreign country diversity ($0.051^{***}$) provides an additional significant protective effect, with each additional foreign country represented in the ownership structure increasing survival log-odds by 0.051, or approximately 5.2% higher survival odds. This finding supports portfolio theory applications to bank ownership: diversified foreign ownership reduces dependence on any single country's economic conditions or diplomatic relationships, providing multiple sources of support during distress periods.

The model achieves the strongest performance among single-factor specifications ($Pseudo\ R^2 = 0.333$, $AIC = 1247.53$), representing a substantial improvement over family and state models. Classification performance improves slightly ($F_1 = 0.65$, $ROC\ AUC = 0.87$), though recall remains constrained ($0.57$), suggesting that while foreign ownership provides powerful protection, it may not capture all dimensions of survival risk.

### Time-varying logistic regression models with CAMEL indicators

::: {#fig-logistic-time-series-models}

![](./figures/logistic_time_effect_plot.pdf)

`\small{\textit{NB:} The significance of the coefficients is different from the previous plots, here $^{***}$ indicates $p < 0.001$, $^{**}$ indicates $p < 0.01$, and $^{*}$ indicates $p < 0.05$.}`{=latex}

Comparison of the effects of family ownership, foreign ownership, and network centrality metrics on bank survival in time-varying logistic regression models (only significant coefficients included)

:::

::: {#fig-logistic-tv-forest-plot fig-scap="Forest plot of the effects of CAMEL factors, network topology, and ownership/management variables on bank survival in time-varying logistic regression models" }

![](./figures/logistic_tv_forest_plot.pdf){out-width="120%" fig-align="center"}


Forest plot of the effects of CAMEL factors, network topology, and ownership/management variables on bank survival in time-varying logistic regression models.

:::

The time-varying logistic regression models presented in @fig-logistic-time-series-models and @fig-logistic-tv-forest-plot extend the previous cross-sectional analysis by incorporating CAMEL indicators to control for bank performance and risk management factors. The models are ordered by increasing performance, as measured by the Akaike Information Criterion (AIC). Here, we focus on groups of models and their relative performance. 

#### Single-factor models

The family ownership models reveal a complex and somewhat counterintuitive pattern of relationships with bank survival prospects that diverges from theoretical expectations in several key respects. The family connection ratio ($\rho_F(b)$) demonstrates a robust positive association with survival ($\beta = 0.626$, $p < 0.001$), suggesting that banks with denser family networks among their ownership structures exhibit significantly enhanced resilience. This coefficient translates to an odds ratio of approximately 1.87, indicating that a one-unit increase in the family connection ratio nearly doubles the odds of survival—a substantial protective effect that aligns with theoretical predictions regarding the informal governance mechanisms inherent in kinship-based ownership structures. However, the family ownership percentage ($FOP_{(b)}$) exhibits a statistically significant but economically modest negative relationship with survival ($\beta = -0.002$, $p < 0.001$), which contradicts the anticipated positive correlation posited in the literature. This seemingly paradoxical finding suggests that whilst the density of family connections confers advantages, the absolute concentration of ownership within family networks may actually increase vulnerability, potentially reflecting the risks associated with overly concentrated decision-making authority or insufficient diversification of ownership interests.

The network topology models present an equally nuanced picture, with centrality measures demonstrating predominantly negative associations with survival prospects that challenge conventional assumptions about the protective value of network positioning. Closeness centrality exhibits a particularly pronounced negative effect ($\beta = -0.291$, $p < 0.001$), corresponding to an odds ratio of approximately 0.75, which indicates that banks occupying more central positions in the ownership network face substantially increased failure risks. This finding suggests that proximity to other network actors may expose banks to contagion effects or regulatory scrutiny rather than providing the anticipated benefits of information flow and resource access. Similarly, betweenness centrality demonstrates a negative coefficient, albeit of considerably smaller magnitude, whilst PageRank centrality also correlates negatively with survival. The sole exception is out-degree centrality ($\beta = 0.048$, $p < 0.001$), which shows a positive association, implying that banks with more extensive outward ownership connections—--those that own stakes in other entities—--enjoy enhanced survival prospects. This pattern may reflect our endogeneity hypothesis, where banks with healthier balance sheets are more likely to take on ownership stakes in other institutions, either voluntarily or as part of the Central Bank's clean-up operations.

The state ownership and structural complexity models reveal the most pronounced effects across the single-factor specifications, with state-related variables demonstrating both the strongest positive and negative associations with survival outcomes. State-controlled companies exhibit a robust positive relationship with survival ($\beta = 0.308$, $p < 0.001$), translating to an odds ratio of approximately 1.36, which suggests that banks with connections to state-controlled entities benefit from substantial protective effects, potentially reflecting regulatory forbearance or preferential treatment consistent with political connection theories. Conversely, state control paths demonstrate a negative coefficient, indicating that indirect state influence through complex ownership chains may actually increase vulnerability, possibly due to the associated bureaucratic inefficiencies or conflicting political pressures. The ownership complexity score shows a positive association ($\beta = 0.037$, $p < 0.001$), supporting theoretical expectations that more convoluted ownership structures provide resilience through diversified interests and multiple avenues for regulatory negotiation. Consistent with corss-sectional findings, the the lifespan variable ($\beta = 0.235$, $p < 0.001$) produces an odds ratio of approximately 1.26, demonstrating that each additional year of operation substantially enhances survival prospects.

#### Multiple-factor models

The introduction of comprehensive financial controls in the multiple factor specifications fundamentally alters the coefficient landscape, revealing that many of the relationships observed in single-factor models operate through distinct mechanisms when accounting for banks' underlying financial performance. The financials-only model (Model 6) establishes a robust baseline with a Pseudo $R^2$ of 0.306, demonstrating that traditional banking performance metrics capture substantial explanatory power for survival outcomes. When family variables are subsequently introduced (Model 9), the family connection ratio maintains its positive association ($\beta = 0.755$, $p < 0.001$) whilst actually increasing in magnitude relative to the single-factor specification, suggesting that the protective effects of family networks operate independently of—and perhaps synergistically with—financial performance indicators. However, the family ownership percentage exhibits a notable shift, moving from negative to non-significant when financial controls are present, indicating that the apparent vulnerability associated with concentrated family ownership may have been confounded by underlying financial weaknesses rather than representing a genuine causal mechanism.

The combined ownership model (Model 7) reveals particularly intriguing dynamics when family, state, and foreign ownership variables are simultaneously considered alongside financial controls. Foreign direct ownership percentage maintains a substantial positive coefficient ($\beta = 1.646$, $p < 0.001$), corresponding to an odds ratio exceeding 5.0, which positions it amongst the most potent protective factors in the entire specification. This effect proves remarkably stable across various model configurations, suggesting robust benefits from foreign capital participation. Conversely, the total foreign ownership percentage demonstrates a consistently negative coefficient across multiple specifications, implying that whilst concentrated foreign ownership provides benefits, more diffuse foreign participation may introduce vulnerabilities, possibly reflecting the distinction between strategic foreign investors and portfolio-level foreign holdings. The state ownership variables exhibit similar complexity, with state-controlled companies maintaining strong positive associations whilst state ownership percentages show more modest effects, suggesting that institutional form matters more than mere ownership concentration.

The comprehensive model incorporating family, state, and foreign factors alongside financial controls (Model 10) achieves the highest explanatory power with a Pseudo $R^2$ of 0.347, representing a substantial improvement over the financials-only baseline. Within this specification, the ownership complexity score emerges as a significant predictor, though its coefficient diminishes considerably compared to simpler models, suggesting that some of its apparent importance derives from correlation with other ownership characteristics. Most notably, the family connection ratio retains statistical significance and economic importance even when competing with the full array of financial, state, and foreign variables, with its coefficient remaining substantial though somewhat attenuated. This persistence across increasingly demanding specifications provides compelling evidence that family network effects represent genuine protective mechanisms rather than proxies for unmeasured financial or political advantages. 

#### Crisis years and interaction effects

The incorporation of crisis interaction terms reveals fundamental shifts in the protective mechanisms afforded by different ownership structures during periods of systemic financial stress, with the 2008-09 global financial crisis and the 2014-15 sanctions-induced crisis serving as natural experiments for examining the resilience of various governance arrangements. The baseline crisis effect demonstrates a consistently negative association with survival across specifications ($\beta = -0.054$, $p < 0.001$, $OR=0.947$ in Model 11), confirming that these periods of macroeconomic turbulence substantially elevated failure risks for Russian banks---this indicates that during crisis periods, the odds of survival decreased by $\approx 5.3\%$. However, the interaction terms reveal that this crisis impact varied dramatically across different ownership configurations, with some structures providing enhanced protection during stress periods whilst others became sources of vulnerability that contradicted their beneficial effects during normal economic conditions.

The crisis interaction with family connection ratio ($\beta = 0.236$, $p < 0.001$, $OR = 1.266$ in Model 10) demonstrates that the protective effects of dense family networks actually intensified during crisis periods by approximately 26.6% beyond the baseline family effect. For banks at the 75th percentile of family connection ratio (approximately 0.21), this interaction effect translates to an additional 5.6 percentage point increase in survival probability during crisis periods, bringing up their predicted probability of survival from roughly 68% to 74%. This finding aligns with theoretical expectations regarding the counter-cyclical benefits of social capital, as family networks may have facilitated more rapid information flow, coordinated responses to emerging threats, and access to emergency resources through informal channels. Conversely, the family ownership percentage crisis interaction exhibits more modest and inconsistent effects across specifications, indicating that concentrated family ownership per se did not provide the same level of protection during stress periods as the relational density captured by the connection ratio.

Perhaps most striking are the dramatically divergent crisis responses exhibited by foreign ownership variables, which reveal the critical importance of geopolitical context in determining the protective value of international connections. Foreign direct ownership percentage demonstrates a substantial negative crisis interaction ($\beta = -0.330$, $p < 0.001$, $OR=0.719$ in Model 12), indicating that what appeared as a protective factor during normal periods became a significant vulnerability during the crisis episodes—--particularly relevant given that both crisis periods coincided with deteriorating relationships between Russia and Western nations. During those periods, each percentage point increase in foreign direct ownership reduced survival odds by 28.1%. This reversal suggests that foreign ownership benefits, whilst substantial during periods of international cooperation, may transform into liabilities when geopolitical tensions escalate, potentially reflecting both direct regulatory pressure and indirect effects through constrained access to international capital markets. In stark contrast, state ownership crisis interactions generally exhibit positive coefficients, with state-controlled companies showing particularly robust enhanced protection during stress periods ($\beta = 0.436$, $p < 0.001$, $OR=1.547$), reinforcing the notion that proximity to state power becomes increasingly valuable as external options diminish. For banks at the 75th percentile of state-controlled company connections, this translates to approximately 12 percentage points of additional survival probability during crises. These divergent crisis responses underscore that the relative ranking of protective mechanisms shifts fundamentally during periods of systemic stress, with domestic political connections gaining primacy over international financial relationships, whilst family networks demonstrate remarkable stability in their protective capacity across varying economic conditions.

### Cox time-varying proportional hazards models

Given the strong performance of the logistic regression models, it is safe to assume that the survival outcomes are significantly influenced by ownership type and some family-related network measures. It is therefore important to test the robustness of those findings in a time-dependent setting and control for CAMEL indicators, which can be done using the time-varying Cox proportional hazards model with the ownership data matched to bank-quarters instead of the cross-sectional nature of the above logistic regression models.

As demonstrated in @fig-cox-tv-forest-plot, most of the coefficients are stable regardless of model specification, which reinforces the conclusions drawn from the logistic regressions. The Cox models, which analyse the hazard rate of bank failure over time, largely corroborate the primary findings. Specifically, the family connection ratio and ownership percentage both exhibit a protective effect, with hazard ratios consistently below one. A similar protective pattern is observable for foreign and state ownership, suggesting their beneficial influence on bank longevity persists even when subjected to this more granular, time-varying analysis. Conversely, the findings for network centrality metrics once again support our endogeneity hypothesis; whilst out-degree centrality is associated with a lower hazard of failure, betweenness and closeness centrality appear to increase it, lending further credence to the notion that such positions are indicative of regulatory burdens rather than strategic advantage. In sum, the time-varying Cox models confirm that the primary ownership and network dynamics identified in the cross-sectional analysis are robust determinants of bank survival over time.

A more detailed examination of the coefficients in @tbl-cox-tv-regressions, however, reveals several crucial nuances and some divergences from the cross-sectional results. Indeed, the network centrality findings offer the strongest corroboration of our earlier conclusions. The consistently positive and significant coefficient for closeness centrality ($C_{close}(v)$) across specifications (e.g., $0.214^{***}$ in the Financial + topology model) indicates that greater network proximity significantly increases the hazard of failure. This reinforces our 'network firefighter' hypothesis, whereby such centrality is not a strategic asset but a liability imposed by regulatory intervention. Similarly, the negative coefficient on out-degree centrality ($C_{out}(v)$) is robust ($-0.171^{***}$), confirming that banks with more extensive outward ownership connections, likely the healthier institutions, enjoy a lower risk of failure.

Conversely, the coefficients for family and foreign ownership introduce a more complex picture than the one suggested by the logistic models. The family connection ratio ($\rho_F(b)$), previously our most consistent protective variable, now shows a more ambiguous effect. Whilst it demonstrates a significant protective effect (a negative coefficient of $-0.051^{***}$) when topology variables are included, it presents as a risk factor in other specifications (e.g., $0.081^{***}$ in the baseline family model). Such sensitivity suggests its protective nature is highly conditional on other network and financial characteristics.

Perhaps most striking is the clear reversal observed for foreign direct ownership ($FOP_d(b)$). What appeared as the most powerful protective shield in the cross-sectional analysis now presents as a significant and robust hazard factor, with a large positive coefficient of $0.127^{***}$ in the main ownership specification. This divergence is not necessarily a contradiction but rather elucidates a critical temporal dynamic that a static model cannot capture. It is plausible that this finding reflects a selection effect; that is, foreign capital may be more likely to enter institutions that are already vulnerable or have a higher latent risk profile, an attribute which only becomes apparent when analysing failure risk over time. Thus, the apparent protection of foreign ownership in a cross-sectional view may be a methodological artefact, whilst the time-series analysis reveals its association with an elevated underlying hazard rate.

{{< pagebreak >}}

<!-- `\begin{landscape}`{=latex} -->

::: {.landscape #fig-cox-tv-forest-plot fig-cap="Forest plot of the effects of family ownership, foreign ownership, and network centrality metrics on bank survival in time-varying Cox proportional hazards models (only significant coefficients included)" width=115%}

![](./figures/cox_tv_forest_plot.pdf)

:::

<!-- `\end{landscape}`{=latex} -->


{{< pagebreak >}}


## Discussion 

This study provides substantial evidence regarding the role of family ownership structures in Russian bank survival, enabling us to address our two primary research hypotheses directly whilst revealing several unexpected findings regarding alternative ownership structures and network positioning.

### Hypothesis 1: Family networks as institutional substitutes

Our first hypothesis (**H1**) posited that banks embedded within family ownership networks demonstrate superior survival prospects compared to banks lacking familial connections, controlling for traditional financial performance indicators. The empirical evidence provides robust support for this proposition, though with important qualifications regarding the mechanisms through which family networks operate.

The family connection ratio emerges as the most consistent and powerful predictor of bank survival across all model specifications. In cross-sectional analyses, a one-unit increase in family network density corresponds to a 63% increase in survival odds ($\beta=0.490^{***}$, $OR \approxeq 1.63$), whilst time-varying models reveal an even more pronounced effect, with family connection ratios nearly doubling survival odds (coefficient: $0.626^{***}$, $OR \approxeq 1.87$). Critically, these effects persist when controlling for comprehensive CAMEL indicators, suggesting that family networks provide protective mechanisms that operate independently of conventional financial performance metrics.

However, our findings reveal a crucial distinction between network quality and pure family ownership stakes. Whilst dense family networks consistently enhance survival prospects, raw family ownership percentages demonstrate inconsistent effects across specifications, sometimes exhibiting negative relationships with survival probability. This pattern indicates that the mere presence of family ownership does not automatically confer advantages; rather, it is the intensity and interconnectedness of family relationships within ownership structures that drives protective effects.

### Hypothesis 2: Network density and strategic coordination

Our second hypothesis (**H2**) predicted that banks positioned within densely connected family network clusters would demonstrate enhanced survival prospects compared to banks with sparse family connections, with effects mediated through improved access to coordinated strategic decision-making. The empirical evidence strongly supports this proposition and illuminates the underlying mechanisms.

The negative coefficient on total family connections ($-0.002^{**}$) when controlling for family connection ratios provides compelling evidence for the network density hypothesis. Banks with extensive but dispersed family involvement actually face reduced survival prospects, whilst those with concentrated, dense family networks enjoy substantial protection. This finding suggests that coordinated strategic decision-making requires not merely family presence, but effective family network architecture that enables efficient information transmission and resource mobilisation.

The crisis interaction effects provide particularly strong support for the coordination mechanism proposed in Hypothesis 2. During the 2008-09 financial crisis and 2014-15 sanctions periods, the protective effects of family connection ratios intensified significantly (coefficient: $0.236^{***}$), indicating that dense family networks become increasingly valuable when external coordination mechanisms falter. This pattern aligns precisely with theoretical expectations regarding the counter-cyclical benefits of social capital and informal governance structures.

### Unexpected findings: Foreign ownership and geopolitical vulnerability

Perhaps the most striking empirical finding concerns the extraordinary protective effects of foreign ownership under normal conditions, contrasted with their dramatic reversal during crisis periods. Foreign direct ownership percentage demonstrates the most powerful protective effect encountered across all specifications, with complete foreign ownership corresponding to a 482% increase in survival odds (coefficient: $1.762^{***}$). This effect substantially exceeds any domestic relationship or structural characteristic, suggesting that foreign ownership provides access to international capital markets, sophisticated risk management practices, and potentially diplomatic protection that makes regulatory authorities more circumspect regarding intervention decisions.

However, the crisis interaction effects reveal a fundamental vulnerability in foreign ownership structures. During crisis periods, each percentage point increase in foreign direct ownership reduces survival odds by 28.1% (coefficient: $-0.330^{***}$), transforming what appears as the strongest protective factor under normal conditions into a significant liability during geopolitical tension. This reversal likely reflects both direct regulatory pressure arising from deteriorating international relations and indirect effects through constrained access to international capital markets when diplomatic relationships deteriorate.

The foreign country diversity effects provide additional nuance, with each additional foreign country represented in ownership structures increasing survival odds by approximately 5.2%. This suggests that diversified foreign ownership provides portfolio-theoretic benefits, reducing dependence on any single country's economic conditions or diplomatic relationships whilst maintaining access to multiple sources of international support.

### State ownership: Institutional form versus concentration

The state ownership findings reveal sophisticated distinctions between formal ownership mechanisms and informal influence channels. State-controlled companies demonstrate robust protective effects (coefficient: $0.308^{***}$), translating to approximately 36% higher survival odds, whilst direct state ownership percentages show more modest and inconsistent effects. This pattern suggests that connections to state-controlled intermediaries matter more than formal state ownership stakes, supporting theories regarding the importance of relationship-based governance in the Russian institutional context.

The crisis interactions with state ownership variables generally exhibit positive coefficients, with state-controlled companies showing particularly robust enhanced protection during stress periods (coefficient: $0.436^{***}$). For banks at the 75th percentile of state-controlled company connections, this translates to approximately 12 percentage points of additional survival probability during crises, reinforcing the notion that proximity to state power becomes increasingly valuable as external options diminish.

### Network centrality: The endogeneity of systemic importance

Counter to conventional network theory expectations, our findings reveal that network centrality measures predominantly correlate with increased failure probability rather than enhanced survival prospects. Closeness centrality exhibits a pronounced negative effect ($\beta = -0.291^{***}$, $OR \approxeq 0.75$), whilst betweenness centrality similarly demonstrates negative associations. These counterintuitive findings provide compelling evidence for our endogeneity hypothesis: rather than indicating competitive strength, high centrality positions appear to reflect banks' roles as 'network firefighters' in the Central Bank's cleanup operations.

This pattern suggests that apparent network centrality may result from regulatory intervention rather than market-driven competitive positioning. Banks exhibiting high centrality measures may have been compelled to absorb failing institutions or assume distressed assets as part of regulatory stabilisation efforts, thereby acquiring central network positions that reflect systemic utility to regulators rather than strategic market positioning.

The sole exception is out-degree centrality, which demonstrates positive effects (coefficient: $0.048^{***}$), indicating that banks with more extensive outward ownership connections enjoy enhanced survival prospects. This finding supports the interpretation that healthy institutions voluntarily acquire ownership stakes in other entities, whilst distressed institutions are involuntarily positioned as central nodes through regulatory intervention.

### Temporal dynamics: Crisis-dependent protective mechanisms

The crisis interaction analyses reveal fundamental shifts in the protective mechanisms afforded by different ownership structures during periods of systemic stress. The baseline crisis effect demonstrates consistently negative associations with survival ($\beta = -0.054^{***}$, $OR \approxeq 0.95$), confirming that macroeconomic turbulence substantially raised failure risks. However, the interaction terms reveal some heterogeneity in crisis responses across ownership configurations.

Family networks demonstrate remarkable resilience, with protective effects actually intensifying during crisis periods. State connections similarly provide enhanced protection during stress, whilst foreign ownership relationships transform from powerful protective factors into significant vulnerabilities. This temporal variation indicates that the relative ranking of protective mechanisms shifts fundamentally during systemic stress, with domestic political connections gaining primacy over international ones.

## Conclusion {.unnumbered}

This study provides robust empirical support for institutional substitution theory within transitional economies characterised by weak formal governance structures. Family networks function as alternative governance mechanisms that compensate for institutional deficiencies, with network architecture rather than mere presence determining organisational outcomes. 

The foreign ownership findings illuminate the contingent nature of international integration in geopolitically sensitive sectors. Whilst foreign capital provides substantial benefits under normal conditions, crisis reversals demonstrate how geopolitical tensions transform international connections into liabilities, emphasising the temporal volatility of protective mechanisms.

Both hypotheses receive strong empirical support, with the critical qualification that network effects depend upon structural quality rather than simple presence. Family networks serve as effective institutional substitutes in weak governance environments, though their effectiveness varies with geopolitical context and temporal conditions. These findings illuminate how informal governance structures operate within transitional economies and underscore the complex interplay between domestic relationship-based coordination and international integration strategies.

The analysis focuses exclusively on the Russian institutional context, potentially limiting generalisability to other economies. The family relationship identification methodology relies partially on algorithmic name-matching, introducing potential measurement error. Future research should examine protective mechanisms across different ownership networks, investigate optimal density thresholds, and explore governance structure interactions with evolving regulatory frameworks. Cross-country comparative studies would assess the broader applicability of these findings beyond Russia's distinctive institutional environment.


## Appendices {.unnumbered .appendix}

### **A** Literature review summary tables {.unnumbered}

```{=latex}
\appendix
\renewcommand{\thefigure}{A\arabic{figure}}
\renewcommand{\thetable}{A\arabic{table}}
\setcounter{figure}{0}
\setcounter{table}{0}
```

::: {.appendix-tables .smaller #tbl-survival-factors-literature  tbl-cap="Factors influencing bank survival and performance in Russia based on the current literature"}

| Factor Category | Specific Factor | Effect Direction | Effect Size/Statistical Significance | Source |
|-----------------|-----------------|------------------|-------------------------------------|---------|
| **Financial Fundamentals** | | | | |
| Bank Size | Total assets (log) | Negative on failure probability | -0.236 to -0.385*** | @barajas_SurvivalRussianBanks_2023 |
| | | Negative on failure probability | -0.24 to -0.31*** | @fungacova_PoliticsBankFailures_2022 |
| | | Negative on failure probability | -0.25*** | @fungacova_DoesCompetitionInfluence_2013a |
| Profitability | Return on Assets (ROA) | Negative on failure probability | -11.999 to -14.10*** | @barajas_SurvivalRussianBanks_2023 |
| | | Negative on failure probability | -77.5 to -82.3*** | @fungacova_PoliticsBankFailures_2022 |
| | | Negative on failure probability | -81.7*** | @fungacova_DoesCompetitionInfluence_2013a |
| Capital Adequacy | Equity-to-assets ratio | Negative on failure probability | -0.025 to -0.026*** | @barajas_SurvivalRussianBanks_2023 |
| | | Negative on failure probability | -1.62 to -1.66*** | @fungacova_PoliticsBankFailures_2022 |
| | | Negative on failure probability | -1.64*** | @fungacova_DoesCompetitionInfluence_2013a |
| Liquidity | Current liquidity ratio | Negative on failure probability | -0.001*** | @barajas_SurvivalRussianBanks_2023 |
| | Liquid assets ratio | Negative on failure probability | -1.93 to -2.39*** | @fungacova_PoliticsBankFailures_2022 |
| | | Negative on failure probability | -2.36*** | @fungacova_DoesCompetitionInfluence_2013a |
| Asset Quality | NPL ratio | Positive on failure probability | 1.49 to 1.87*** | @fungacova_PoliticsBankFailures_2022 |
| | | Positive on failure probability | 1.85*** | @fungacova_DoesCompetitionInfluence_2013a |
| **Risk Management** | | | | |
| Risk to Shareholders | Loans/guarantees to shareholders | Positive on failure probability | 0.005-0.009** | @barajas_SurvivalRussianBanks_2023 |
| Share Investments | Bank's investment in other entities | Mixed effects on failure | 0.021-0.030*** | @barajas_SurvivalRussianBanks_2023 |
| **Strategic Orientation** | | | | |
| Corporate Deposits | Proportion of firm deposits | Negative on failure probability | -0.650 to -0.698*** | @barajas_SurvivalRussianBanks_2023 |
| Corporate Loans | Proportion of firm loans | Positive on failure probability | 0.406-0.554*** | @barajas_SurvivalRussianBanks_2023 |
| Deposit Growth | Quarterly deposit growth | No significant effect | 0.049-0.066 (n.s.) | @barajas_SurvivalRussianBanks_2023 |
| Loan Growth | Quarterly loan growth | Positive on failure probability | 0.292-0.300** | @barajas_SurvivalRussianBanks_2023 |
| **Ownership Structure** | | | | |
| Foreign Control | Foreign bank control (>50%) | Negative on failure probability | -0.989 to -0.993*** | @barajas_SurvivalRussianBanks_2023 |
| Foreign Ownership | Foreign ownership dummy | Negative on lending | -0.488 to -0.504*** | @weill_HowCorruptionAffects_2011 |
| Public Ownership | State ownership dummy | Negative on lending | -0.241 to -0.339** | @weill_HowCorruptionAffects_2011 |
| **Factional Associations** | | | | |
| Media Factional Index | Intensity of faction-associated media mentions | Positive on profit | 1.27-1.46 billion RUB*** | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| | | Positive on total assets | 194.7-198.4*** (multiplier effect) | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| | | Negative on licence revocation probability | -330.4 to -385.0* | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| Factional Ownership Index | Proportion of faction-associated ownership | Negative on profitability ratio | -184.6 to -209.4*** | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| | | Positive on total assets | 343.1-367.3** | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| | | Positive on business termination risk | 403.4-404.0* | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| Siloviki Ownership | Security/intelligence faction ownership | Negative on licence revocation | -1599.0 to -1600.5** | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| Government/Presidential Ownership | State administrative faction ownership | Positive on licence revocation risk | 1691.8-1727.4** | @soldatkin_FactionalismCompetitionEfficiency_2020 |
| **Market Structure** | | | | |
| Market Competition | Lerner index (market power) | Negative (more competition increases failure) | -1.460 to -3.364*** | @fungacova_DoesCompetitionInfluence_2013a |
| Bank Concentration | Regional concentration | Mixed/no significant effect | Varied across specifications | @weill_HowCorruptionAffects_2011 |
| **Political Factors** | | | | |
| Electoral Cycles | Pre-election periods | Negative on failure probability | -0.50 to -1.21** | @fungacova_PoliticsBankFailures_2022 |
| | | | Average failure probability 2-3x lower | @fungacova_PoliticsBankFailures_2022 |
| Political Connections | Regional governor affiliation | Moderates other effects | Interaction effects significant | @fungacova_PoliticsBankFailures_2022 |
| **Institutional Environment** | | | | |
| Corruption | Regional corruption measures | Negative on lending | -0.182 to -0.340*** | @weill_HowCorruptionAffects_2011 |
| Regulatory Compliance | CBR prudential ratios | Mixed discriminatory power | 98-99% compliance rates | @barajas_SurvivalRussianBanks_2023 |
| **Regional Factors** | | | | |
| Economic Development | Per capita income | Negative on lending | -0.089 to -0.141*** | @weill_HowCorruptionAffects_2011 |
| Distance from Moscow | Geographic proximity | Positive on failure risk | -0.01** | @fungacova_PoliticsBankFailures_2022 |
| Urban Population | Regional urbanisation | Mixed effects | Varied significance | Multiple sources |

:::


::: {.appendix-tables #tbl-extended-family-business-group-studies .smaller tbl-cap="Comparative results incorporating business group and family ownership studies"}

| **Research focus** | **Study** | **Outcome variables** | **Key explanatory variables** | **Effect direction & magnitude** | **Sample context** |
|---|---|---|---|---|---|
| **Business Group Performance** | @khanna_EstimatingPerformanceEffects_2001 | ROA, within-group profit similarity | Business group affiliation, group membership across 14 countries | **Mixed**: Positive in 6 countries (India, Indonesia, Taiwan), negative in 3 (Argentina), neutral in 5; significant within-group profit clustering in 12/14 countries | 14 emerging markets (1988–1997) |
| **Family vs Professional Management** | @villalonga_HowFamilyOwnership_2006 | Tobin's Q, firm value | Founder CEO vs descendant CEO vs professional management | **Founder advantage**: Founder CEO +1.16 coefficient; Descendant CEO -0.23 coefficient relative to non-family management | Fortune 500 firms (1994–2000) |
| **Pyramidal Ownership Structures** | @almeida_TheoryPyramidalOwnership_2006 | Theoretical framework for optimal ownership structure | Security benefits, investment requirements, investor protection quality | **Theoretical prediction**: Pyramids optimal when security benefits low; poor investor protection environments favour pyramidal control | Theoretical model |
| **Intra-Family Dynamics** | @bertrand_MixingFamilyBusiness_2008 | Residual ROA, succession outcomes | Number of sons, family composition, founder status, excess control mechanisms | **Negative family size effects**: Each additional son reduces ROA by -0.34; sons' excess control -0.168 to -0.344 | Thai business groups (1996) |
| **Institutional Context Effects** | @khanna_EstimatingPerformanceEffects_2001 | Cross-country variation in group effects | Capital market development, institutional quality | **Context-dependent**: Group benefits positively correlated with capital market development (ρ = 0.70) | Cross-country |
| **Network Structure Analysis** | @vitali_CommunityStructureGlobal_2014 | Community structure, network centrality | Geographic clustering, sectoral affiliation, financial connectivity | **Geographic dominance**: 80% concentration vs 25% in random networks | Global ownership network |
| **Family Ownership and Firm Performance** | @andres_LargeShareholdersFirm_2008 | ROA | Founding-family ownership, board representation | **Positive**: Active family board members → +3.1% to +4.5% ROA | 275 German firms (1998–2004) |
| **Family Ownership During Crises** | @hiebl_FamilyOwnershipConflict_2024 | Crisis performance | Family ownership, CEO turnover, ownership concentration | **Mixed**: Lower concentration + family CEO improves outcomes | German family firms |
| **Local Embeddedness and Growth** | @bau_RootsGrowFamily_2019 | Firm growth | Local embeddedness, rural/urban | **Positive**: More impact in rural areas | 7,829 Swedish family firms |
| **Social Capital in Family Firms** | @arregle_DevelopmentOrganizationalSocial_2007 | Organisational Social Capital | Family social capital, interdependence, network closure | **Positive**: Family interdependence enhances OSC, aids survival | Theoretical/empirical model |
| **Social Networks and Turnover** | @barroso_AnalysisEvaluationLargest_2018 | Turnover | E-quality, social network presence, ownership concentration | **Positive**: Higher turnover in firms with digital presence + high family ownership | Top 500 global family firms |
| **Network Centrality and Firm Survival** | @bagley_NetworksGeographySurvival_2019 | Firm survival (hazard rate) | Network centrality (knowledge networks) | **Positive**: Higher centrality → lower hazard rate | Global firms, spinoff networks |
| **Social Networks and Crisis Recovery** | @lin_SocialNetworksListed_2022 | Recovery from distress | Executive network centrality | **Positive**: Closeness/degree centrality boosts recovery | Listed firms |
| **Family Ownership and Network Formation** | @ghinoi_FamilyFirmNetwork_2024 | Network structure | Family ownership, network formation propensity | **Positive**: Family ownership → higher propensity to form edges | Italian regional firms |

:::

::: {.appendix-tables #tbl-extended-effect-magnitudes .smaller tbl-cap="Effect magnitudes and statistical significance across governance structures"}

| **Relationship** | **Effect magnitude** | **Statistical significance** | **Study** | **Context** |
|---|---|---|---|---|
| Group-affiliated vs independent | Country-specific: +8.1% (Mexico), +9.3% (Indonesia), -2.8% (Argentina) | Significant in 9/14 | @khanna_EstimatingPerformanceEffects_2001 | 14 emerging markets |
| Within-group profit similarity | R²: 2.6%–39.5% | Significant in 12/14 | @khanna_EstimatingPerformanceEffects_2001 | Cross-country |
| Founder CEO premium | +1.16 (Tobin's Q) | p < 0.001 | @villalonga_HowFamilyOwnership_2006 | Fortune 500 |
| Family size effect (sons) | -0.34 per son | p < 0.05 | @bertrand_MixingFamilyBusiness_2008 | Thai groups |
| Excess control by sons | -0.168 to -0.344 | p < 0.001 | @bertrand_MixingFamilyBusiness_2008 | Thai groups |
| Geographic clustering (networks) | 80% vs 25% | Highly significant | @vitali_CommunityStructureGlobal_2014 | Global network |
| Capital market correlation | ρ = 0.70 | p < 0.02 | @khanna_EstimatingPerformanceEffects_2001 | 14 countries |
| Family board representation and ROA | +3.1% to +4.5% | p < 0.05 | @andres_LargeShareholdersFirm_2008 | German firms |
| Family ownership and crisis survival | Context-dependent | p < 0.05 | @hiebl_FamilyOwnershipConflict_2024 | German family firms |
| Local embeddedness on growth | Greater rural impact | p < 0.05 | @bau_RootsGrowFamily_2019 | Swedish firms |
| Network centrality and survival | Lower hazard rate | p < 0.05 | @bagley_NetworksGeographySurvival_2019 | Spinoff firms |
| Executive centrality and recovery | Faster recovery | p < 0.05 | @lin_SocialNetworksListed_2022 | Listed firms |
| Digital presence and turnover | Positive effect | p < 0.05 | @barroso_AnalysisEvaluationLargest_2018 | Global family firms |
| Family ownership on network building | Positive effect | p < 0.05 | @ghinoi_FamilyFirmNetwork_2024 | Italian regional firms | 

:::

### **B** Description of metrics {.unnumbered}

```{=latex}
\appendix
\renewcommand{\thefigure}{B\arabic{figure}}
\renewcommand{\thetable}{B\arabic{table}}
\setcounter{figure}{0}
\setcounter{table}{0}
```

::: {.appendix-tables .landscape #tbl-metrics-description tbl-cap="Descriptions of metrics employed during the analysis in addition to CAMEL financial indicators" tbl-colwidths=[15,15,50,20]}

| Metric | Symbol | Formula | Description |
|--------|--------|---------|-------------|
| **Family ownership metrics** | | | |
| Direct Family Ownership Value | $FOV_d(b)$ | $FOV_d(b) = \sum_{i \in D_b} \omega_i \cdot \mathbf{1}_{F}(i)$ | Total ownership value held by shareholders with family connections |
| Total Ownership Value | $TOV(b)$ | $TOV(b) = \sum_{i \in D_b} \omega_i$ | Sum of all direct ownership stakes in the bank |
| Family Ownership Percentage | $FOP(b)$ | $FOP(b) = \begin{cases} \frac{FOV_d(b)}{TOV(b)} \times 100\%, & \text{if } TOV(b) > 0 \\ 0, & \text{otherwise} \end{cases}$ | Proportion of total ownership held by family-connected shareholders |
| Direct Owner Count | $\|D_b\|$ | $\|D_b\|$ | Total number of direct shareholders |
| Total Family Connections | $\|F_b\|$ | $\|F_b\| = \sum_{i \in D_b} \|N_F(i)\|$ | Count of family relationships among direct owners |
| Family-Controlled Companies | $\|C_F(b)\|$ | $\|C_F(b)\| = \|\{c \in V \mid \exists f \in V, \exists p: f \xrightarrow{\text{OWNERSHIP}^*} c \xrightarrow{\text{OWNERSHIP}} b, \text{ and } \exists g: (f) \xrightarrow{\text{FAMILY}} g\}\|$ | Count of companies controlled by family members with ownership stakes |
| Family Connection Ratio | $\rho_F(b)$ | $\rho_F(b) = \begin{cases} \frac{\|F_b\|}{\|D_b\|}, & \text{if } \|D_b\| > 0 \\ 0, & \text{otherwise} \end{cases}$ | Average number of family connections per direct owner |
| **Foreign ownership metrics** | | | |
| Direct Foreign Ownership Value | $FOV_d(b)$ | $FOV_d(b) = \sum_{v \in D_b} \phi(v) \cdot \omega(v, b)$ | Total ownership value held by foreign entities |
| Foreign Direct Ownership Percentage | $FOP_d(b)$ | $FOP_d(b) = \begin{cases} \frac{FOV_d(b)}{TOV_d(b)} \times 100\%, & \text{if } TOV_d(b) > 0 \\ 0, & \text{otherwise} \end{cases}$ | Percentage of direct ownership held by foreign entities |
| Foreign Entity Direct Count | $FEC_d(b)$ | $FEC_d(b) = \sum_{v \in D_b} \phi(v)$ | Number of foreign entities with direct ownership |
| Foreign-Controlled Companies Count | $FCC(b)$ | $FCC(b) = \|\{c \in V : \exists f \in V, (f,c,b) \in P_b\}\|$ | Count of companies controlled by foreign entities |
| Indirect Foreign Ownership Value | $FOV_i(b)$ | $FOV_i(b) = \sum_{(f,c,b) \in P_b} \omega(c,b)$ | Total ownership value through foreign-controlled intermediaries |
| Total Foreign Ownership Value | $FOV_t(b)$ | $FOV_t(b) = FOV_d(b) + FOV_i(b)$ | Combined direct and indirect foreign ownership value |
| Total Foreign Ownership Percentage | $FOP_t(b)$ | $FOP_t(b) = \begin{cases} \frac{FOV_t(b)}{TOV_d(b)} \times 100\%, & \text{if } TOV_d(b) > 0 \\ 0, & \text{otherwise} \end{cases}$ | Total percentage of foreign ownership (direct + indirect) |
| **Network centrality metrics** | | | |
| In-degree Centrality | $C_{in}(v)$ | $C_{in}(v) = \|\{u \in V : (u,v) \in E\}\|$ | Number of incoming relationships to a node, indicating influence or importance |
| Out-degree Centrality | $C_{out}(v)$ | $C_{out}(v) = \|\{u \in V : (v,u) \in E\}\|$ | Number of outgoing relationships from a node, indicating activity or engagement |
| Closeness Centrality | $C_{close}(v)$ | $C_{close}(v) = \frac{1}{\sum_{u \in V} d(v,u)}$ | Measure of how close a node is to all other nodes, indicating information flow efficiency |
| Betweenness Centrality | $C_{between}(v)$ | $C_{between}(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$ | Measure of how often a node acts as a bridge between other nodes, indicating control over information flow |
| Eigenvector Centrality | $C_{eigen}(v)$ | $C_{eigen}(v) = \frac{1}{\lambda} \sum_{u \in V} A_{uv} \cdot C_{eigen}(u)$ | Measure of node influence based on number and quality of connections |
| PageRank | $PR(v)$ | $PR(v) = \frac{1-d}{N} + d \sum_{u \in M(v)} \frac{PR(u)}{L(u)}$ | Measure of node importance based on incoming relationships, similar to Google's algorithm |
| **Ownership complexity metrics** | | | |
| Unique Owners | $U_b$ | $U_b = \|\{v_0 : \exists p = (v_0, v_1, \ldots, v_k) \in P_b\}\|$ | Number of unique entities in ownership paths to the bank |
| Average Path Length | $L_b$ | $L_b = \frac{1}{\|P_b\|} \sum_{p \in P_b} \|p\|$ | Average length of ownership paths to the bank |
| Total Paths | $T_b$ | $T_b = \|P_b\|$ | Total number of ownership paths to the bank |
| Ownership Complexity Score | $C_b$ | $C_b = L_b \cdot \log_{10}(1 + U_b)$ | Combined measure of ownership structure complexity |

:::

### **C** Regression results {.unnumbered}

```{=latex}
\appendix
\renewcommand{\thefigure}{C\arabic{figure}}
\renewcommand{\thetable}{C\arabic{table}}
\setcounter{figure}{0}
\setcounter{table}{0}
```

#### Cross-sectional logistic regression models {.unnumbered}

::: {.smaller }

```{python}
#| output: asis
#| echo: false

from stargazer.stargazer import Stargazer
import pickle
import statsmodels.formula.api as smf
from IPython.display import display, HTML

# Dictionary to rename regression covariates to mathematical formula names
covariate_rename_dict = {
    # === FAMILY OWNERSHIP METRICS ===
    "family_ownership_percentage": r"$FOP(b)$",  # Family Ownership Percentage
    "family_connection_ratio": r"$\rho_F(b)$",  # Family Connection Ratio
    "total_family_connections": r"$|F_b|$",  # Total Family Connections
    "direct_family_owned": r"$FOV_d(b)$",  # Direct Family Ownership Value
    "family_controlled_companies": r"$|C_F(b)|$",  # Family-Controlled Companies
    "direct_owners": r"$|D_b|$",  # Direct Owner Count
    "direct_owner_count": r"$|D_b|$",  # Alternative name for direct owners
    # === FOREIGN OWNERSHIP METRICS ===
    "foreign_direct_ownership_percentage": r"$FOP_d(b)$",  # Foreign Direct Ownership Percentage
    "total_foreign_ownership_percentage": r"$FOP_t(b)$",  # Total Foreign Ownership Percentage
    "foreign_entity_count": r"$FEC_d(b)$",  # Foreign Entity Direct Count
    "foreign_entity_direct_count": r"$FEC_d(b)$",  # Alternative name
    "foreign_controlled_companies": r"$FCC(b)$",  # Foreign-Controlled Companies Count
    "direct_foreign_owned": r"$FOV_d^{foreign}(b)$",  # Direct Foreign Ownership Value
    "indirect_foreign_owned": r"$FOV_i(b)$",  # Indirect Foreign Ownership Value
    "total_foreign_owned": r"$FOV_t(b)$",  # Total Foreign Ownership Value
    "unique_country_count": r"$FCD(b)$",  # Foreign Country Diversity
    # === STATE OWNERSHIP METRICS ===
    "state_ownership_percentage": r"$SOP(b)$",  # State Ownership Percentage
    "state_direct_ownership_value": r"$SOV_d(b)$",  # State Direct Ownership Value
    "state_controlled_companies": r"$SCC(b)$",  # State-Controlled Companies
    "state_control_paths": r"$SCP(b)$",  # State Control Paths
    # === NETWORK CENTRALITY METRICS ===
    "in_degree_centrality": r"$C_{in}(v)$",  # In-degree Centrality
    "out_degree_centrality": r"$C_{out}(v)$",  # Out-degree Centrality
    "closeness_centrality": r"$C_{close}(v)$",  # Closeness Centrality
    "betweenness_centrality": r"$C_{between}(v)$",  # Betweenness Centrality
    "eigenvector_centrality": r"$C_{eigen}(v)$",  # Eigenvector Centrality
    "pagerank": r"$PR(v)$",  # PageRank
    # === OWNERSHIP COMPLEXITY METRICS ===
    "ownership_complexity_score": r"$C_b$",  # Ownership Complexity Score
    "unique_owners": r"$U_b$",  # Unique Owners
    "average_path_length": r"$L_b$",  # Average Path Length
    "total_paths": r"$T_b$",  # Total Paths
    # === BANK CHARACTERISTICS ===
    "lifespan_years": r"$Age(b)$",  # Bank Age
    "total_direct_owned": r"$TOV(b)$",  # Total Ownership Value
    "survived_int": r"$Survival(b)$",  # Survival Indicator
    # === ALTERNATIVE NAMING CONVENTIONS ===
    "Intercept": r"$\alpha$",  # Intercept
    "intercept": r"$\alpha$",  # Alternative intercept name
    "(Intercept)": r"$\alpha$",  # R-style intercept name
    # # === FINANCIAL METRICS (if included) ===
    "capital_adequacy": r"$CAR(b)$",  # Capital Adequacy Ratio
    "asset_quality": r"$AQ(b)$",  # Asset Quality
    "management_quality": r"$MQ(b)$",  # Management Quality
    "earnings": r"$E(b)$",  # Earnings
    "liquidity": r"$L(b)$",  # Liquidity
    # "sensitivity": r"$S(b)$",  # Sensitivity to Market Risk
    # # === EXTENDED NETWORK METRICS ===
    "in_degree": r"$C_{in}(v)$",  # In-degree Centrality (directed)
    "out_degree": r"$C_{out}(v)$",  # Out-degree Centrality (directed)
    "closeness": r"$C_{close}(v)$",  # Closeness Centrality (directed)
    "betweenness": r"$C_{between}(v)$",  # Betweenness Centrality (directed)
    "eigenvector": r"$C_{eigen}(v)$",  # Eigenvector Centrality (directed)
    "page_rank": r"$PR(v)$",  # PageRank (directed)
    # "degree_centrality": r"$C_{degree}(v)$",  # Degree Centrality (undirected)
    "clustering_coefficient": r"$CC(v)$",  # Clustering Coefficient
    # "shortest_path_length": r"$SPL(v)$",  # Average Shortest Path Length
    # # === ADDITIONAL STATE METRICS ===
    # "state_entity_count": r"$SEC(b)$",  # State Entity Count
    # "state_connection_ratio": r"$\rho_S(b)$",  # State Connection Ratio
    # # === SIZE AND PERFORMANCE METRICS ===
    # "log_assets": r"$\ln(Assets_b)$",  # Log Total Assets
    "roa": r"$$ROA(b)$$",  # Return on Assets
    "roe": r"$$ROE(b)$$",  # Return on Equity
    "net_interest_margin": r"$$NIM(b)$$",  # Net Interest Margin
    "leverage_ratio": r"$LR(b)$",  # Leverage Ratio
    "liquid_assets_to_total_assets": r'$\frac{LA}{TA}$',  # Liquid Assets to Total Assets
    "llp_to_loans_ratio": r'$\frac{LLP}{Loans}$',  # Loan Loss Provisions to Loans Ratio
    "loan_to_deposit_ratio": r'$\frac{Loans}{Deposits}$',  # Loan to Deposit Ratio
    "non_interest_expense_to_assets": r'$\frac{NIE}{Assets}$',  # Non-Interest Expense to Assets Ratio
    "npl_ratio": r'$\frac{NPL}{Loans}$',  # Non-Performing Loans Ratio
    "tier1_capital_ratio": r'$\frac{Tier1}{Assets}$',  # Tier 1 Capital Ratio
    "cost_to_income_ratio": r'$\frac{Cost}{Income}$',  # Cost to Income Ratio
    "coverage_ratio": r'$\frac{EBIT}{IE}$',   # Coverage Ratio
    "age_days": r"$Age(b)$",  # Bank Age in Days
    "asset_turnover": r"$\frac{Revenue}{Assets}$",# Asset Turnover Ratio
    "companies_loans_to_assets": r"$\frac{Loans_C}{Assets}$",  # Companies Loans to Assets Ratio
    "companies_pct_of_loans": r"$\frac{Loans_C}{Loans}$",  # Companies Loans as Percentage of Total Loans
    "companies_to_state": r"$\frac{Loans_C}{Loans_S}$",  # Companies to State Ratio
    "individuals_loans_to_assets": r"$\frac{Loans_I}{Assets}$",  # Individuals Loans to Assets Ratio
    "individuals_pct_of_loans": r"$\frac{Loans_I}{Loans}$",  # Individuals Loans as Percentage of Total Loans
    "individuals_to_companies": r"$\frac{Loans_I}{Loans_C}$",  # Individuals to Companies Ratio
    "individuals_to_state": r"$\frac{Loans_I}{Loans_S}$",  # Individuals to State Ratio
    "state_loans_to_assets": r"$\frac{Loans_S}{Assets}$",  # State Loans to Assets Ratio
    "state_pct_of_loans": r"$\frac{Loans_S}{Loans}$",  # State Loans as Percentage of Total Loans
    "tier1_capital": r'$Tier1$',  # Tier 1 Capital Ratio 

}

def format_stargazer(models, model_names, rename_covariates={}, title="Regression Results", **kwargs):
    """Formats multiple regression models using Stargazer."""
    if not models:
        return "No models to format."
    
    # compute metrics for each model
    from stargazer.stargazer import Stargazer, LineLocation
    from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, roc_auc_score
    for model, model_name in zip(models, model_names):
        # Ensure model is fitted
        if not hasattr(model, 'fittedvalues'):
            print("Model is not fitted properly, skipping metrics.")
            continue
        
        # Calculate metrics
        y_true = model.model.endog
        y_pred = model.predict()
        
        # Convert predictions to binary (0/1) based on a threshold
        y_pred_binary = (y_pred >= 0.5).astype(int)
        
        # Calculate metrics
        model.aic = model.aic
        model.bic = model.bic
        model.f1 = f1_score(y_true, y_pred_binary)
        model.precision = precision_score(y_true, y_pred_binary)
        model.recall = recall_score(y_true, y_pred_binary)
        model.accuracy = accuracy_score(y_true, y_pred_binary)
        model.roc_auc = roc_auc_score(y_true, y_pred)
        # print(f"Model '{model_name}' metrics: AIC={model.aic:.2f}, BIC={model.bic:.2f}, F1={model.f1:.2f}, Precision={model.precision:.2f}, Recall={model.recall:.2f}, Accuracy={model.accuracy:.2f}, ROC AUC={model.roc_auc:.2f}")
    stargazer = Stargazer(models, **kwargs)
    if rename_covariates:
        # Rename covariates if provided
        stargazer.rename_covariates(rename_covariates)
    
    # stargazer.title(title)
    stargazer.custom_columns(model_names, [1] * len(models)) # Assign names
    stargazer.show_degrees_of_freedom(True)
    
    # Add custom notes or settings as needed, eg add aic and bic
    stargazer.add_line("AIC", [f"{model.aic:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("BIC", [f"{model.bic:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("F1 Score", [f"{model.f1:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("Precision", [f"{model.precision:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("Recall", [f"{model.recall:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("Accuracy", [f"{model.accuracy:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    stargazer.add_line("ROC AUC", [f"{model.roc_auc:.2f}" for model in models], LineLocation.FOOTER_BOTTOM)
    return stargazer # Or render_latex(), render_ascii()

with open('regression_results/simple_fitted_models.pkl', 'rb') as f:
    fitted_models = pickle.load(f)
with open('regression_results/simple_model_names.pkl', 'rb') as f:
    model_names = pickle.load(f)

# model_names = [name.replace(' ', r'\\\\') for name in model_names]

latex = format_stargazer(
  models=fitted_models,
  model_names=model_names,
  rename_covariates=covariate_rename_dict,
  title="Logistic regression results for bank survival",
  # table_label="tbl-simple-logistic-regression-results"
).render_latex(escape=True).replace(r'\\cr', r'\\\\').replace(r'} \\', r'} \\\\').replace(r'} \\ \cline', r'} \\\\ \\cline').replace(r'\begin{table}[!htbp]', r' ').replace(r'\end{table}', r' ').replace(r'\centering', r' ').replace(r'\{', r'{').replace(r'\}', r'}')

latex = latex.replace(r'\$', r'$').replace(r'\_', r'_').replace(r'survived_int', r'survived\_int').replace(r'\textbackslash ', '\\')

latex = r'\begin{adjustbox}{max width=\textwidth}' + '\n' + latex + r'\end{adjustbox}'
latex = r'\begin{longtable}{@{}l' + 'c' * len(model_names) + r'@{}}' + '\n' + r'\caption{Results from cross-sectional logistic models}\label{tbl-simple-logistic-results}' + '\n' + latex + '\n' + r'\end{longtable}'

# the string is still escaped 
from IPython.display import display, Math, Latex
display(Latex(latex))
```

:::

#### Time-varying logistic regression models {.unnumbered}


```{python}
#| output: asis
#| echo: false

import pickle

with open('regression_results/logistic_time_series_models_and_names.pkl', 'rb') as f:
    fitted_models, model_names = pickle.load(f)

# model_names = [name.replace(' ', r'\\\\') for name in model_names]

latex = format_stargazer(
  models=fitted_models,
  model_names=model_names,
  rename_covariates=covariate_rename_dict,
  title="Logistic regression results for bank survival",
  # table_label="tbl-simple-logistic-regression-results"
).render_latex(escape=True).replace(r'\\cr', r'\\\\').replace(r'} \\', r'} \\\\').replace(r'} \\ \cline', r'} \\\\ \\cline').replace(r'\begin{table}[!htbp]', r' ').replace(r'\end{table}', r' ').replace(r'\centering', r' ').replace(r'\{', r'{').replace(r'\}', r'}')

latex = latex.replace(r'\$', r'$').replace(r'\_', r'_').replace(r'survived_int', r'survived').replace(r'\textbackslash ', '\\')

latex = r'\begin{adjustbox}{max width=\textwidth}' + '\n' + latex + r'\end{adjustbox}'

latex = r'\begin{longtable}{@{}l' + 'c' * len(model_names) + r'@{}}' + '\n' + r'\caption{Results from time-varying logistic regression models with CAMEL indicators}\label{tbl-time-variable-logistic-results}'+ latex + r'\end{longtable}'

from IPython.display import display, Math, Latex
# the string is still escaped 
display(Latex(latex))

```



#### Time-varying Cox regression models {.unnumbered}

::: {.landscape .smaller }



```{python .landscape .smaller}
#| output: asis
#| echo: false
#| label: tbl-cox-tv-regressions
#| tbl-cap: "Cox time-varying proportional hazards regression results for bank death incorporating CAMEL indicators and ownership metrics"
import pickle
import pandas as pd

with open('regression_results/cox_tv_models_and_names.pkl', 'rb') as file:
    models, model_names = pickle.load(file)

# [(display(model.summary), print(model_name)) for model in models for model_name in model_names]

def create_cox_comparison_long_df(models, model_names):
    """
    Create a comparison table for Cox models using stargazer-style output.
    
    Args:
        models (list): List of fitted Cox models
        model_names (list): List of model names
    
    Returns:
        DataFrame: Comparison table
    """
    # Create a summary DataFrame for each model
    model_summaries = []
    for model, model_name in zip(models, model_names):
        model_summary = model.summary.copy().reset_index()
        model_summary['model_name'] = model_name
        model_summary['nobs'] = model._n_unique
        model_summary['aic'] = model.AIC_partial_
        model_summary['log_likelihood'] = model.log_likelihood_
        model_summary['LLR stat'] = model.log_likelihood_ratio_test().test_statistic
        model_summary['LLR p-value'] = model.log_likelihood_ratio_test().p_value
        model_summary['aic'] = model.AIC_partial_
        model_summary['log_likelihood'] = model.log_likelihood_
        
        model_summaries.append(model_summary)

    model_summaries_df = pd.concat(model_summaries, ignore_index=True)

    def get_stars(p_value):
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return ""
    model_summaries_df['stars'] = model_summaries_df['p'].apply(get_stars)

    return model_summaries_df

# test
cox_comparison_long_df = create_cox_comparison_long_df(models, model_names)    

def create_cox_comparison_table(cox_comparison_long_df):
    """
    Create a comparison table for Cox models using stargazer-style output.
    Args:
        cox_comparison_long_df (DataFrame): DataFrame with model summaries and model names
    Returns:
        DataFrame: Comparison table
    """
    # coeff + stars (upper) + (se)
    def format_cell(row):
        coef = row["coef"]
        se = row["se(coef)"]
        stars = row["stars"]
        if type(coef) == str:
            return coef
        if pd.isna(coef):
            return ""
        if pd.isna(se):
            return ""
        return f"{coef:.3f}{stars} ({se:.3f})"
    
    cox_comparison_long_df["display_coef"] = cox_comparison_long_df.apply(
        format_cell, axis=1
    )
    cox_comparison_long_df = cox_comparison_long_df[
        ["covariate", "model_name", "display_coef", "log_likelihood", 'aic', 
         "nobs", "LLR stat", "LLR p-value"]
    ]
    # pivot to wide format, log likelihood and aic as additional rows
    cox_comparison_long_df = cox_comparison_long_df.rename(
        columns={"covariate": "covariate", "model_name": "model_name"}
    )
    cox_comparison_wide_df = cox_comparison_long_df.pivot(
        index="covariate",
        columns="model_name",
        values="display_coef"
    )
    # add a row with markdown --- for horizontal line
    # cox_comparison_wide_df.loc["\midrule"] = ["\midrule"] * len(cox_comparison_wide_df.columns)
    # add log_likelihood and aic as additional rows
    log_likelihoods = cox_comparison_long_df.groupby("model_name")["log_likelihood"].first()
    aics = cox_comparison_long_df.groupby("model_name")["aic"].first()
    nobs = cox_comparison_long_df.groupby("model_name")["nobs"].first()
    llr_stats = cox_comparison_long_df.groupby("model_name")["LLR stat"].first()
    llr_pvalues = cox_comparison_long_df.groupby("model_name")["LLR p-value"].first()
    
    # add a midrule row
    # cox_comparison_wide_df.loc["\\midrule"] = ["\\midrule"] * len(cox_comparison_wide_df.columns)
    cox_comparison_wide_df.loc["$N_{(b)}$"] = [f'{nobs:.0f}' for nobs in nobs]
    # add number of event occurrences

    cox_comparison_wide_df.loc["Log Likelihood"] = [f'{log_likelihood:.2f}' for log_likelihood in log_likelihoods]
    cox_comparison_wide_df.loc["AIC"] = [f'{aic:.2f}' for aic in aics]
    cox_comparison_wide_df.loc["LLR Stat"] = [f'{llr_stat:.2f}' for llr_stat in llr_stats]
    cox_comparison_wide_df.loc["LLR p-value"] = [f'{llr_pvalue:.3f}' for llr_pvalue in llr_pvalues]
    # add a row with markdown --- for horizontal line
    # cox_comparison_wide_df.loc["\midrule"] = ["\midrule"] * len(cox_comparison_wide_df.columns)


    cox_comparison_wide_df.fillna("", inplace=True)
    # remove model_name and covariate from index
    cox_comparison_wide_df.index.name = None
    cox_comparison_wide_df.columns.name = None
    # rename covariates to mathematical formula names
    cox_comparison_wide_df.index = cox_comparison_wide_df.index.map(
        lambda x: covariate_rename_dict.get(x, x)
    )
        
    # Create the table without styling first
    latex_table = (
        cox_comparison_wide_df
        # .to_latex(
        # column_format="l|" + "c" * len(model_names),
        # # caption="Comparison of Cox time-varying models for bank survival incorporating CAMEL indicators",
        # # title="Comparison of Cox models for bank survival",
        # label="tbl-cox-model-comparison",
        # escape=True)
    )
    # Replace with double hlines at top and bottom, and single for the header
    # latex_table = latex_table.replace("\\toprule", "\\hline\\hline")
    # latex_table = latex_table.replace("\\midrule", "\\hline")
    # latex_table = latex_table.replace("\\bottomrule", "\\hline\\hline")
    
    # # Add resizebox to make it fit page width
    # latex_table = latex_table.replace(
    #     "\\begin{table}",
    #     "\\begin{table}[H]\n\\resizebox{\\textwidth}{!}"
    # )
    # latex_table = latex_table.replace(
    #     "\\end{tabular}",
    #     "\\end{tabular}}"
    # )
    
    return latex_table
# latex = create_cox_comparison_table(cox_comparison_long_df).style.format(
#     # format the numbers in the table
#     {
#         "display_coef": lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x,
#         "log_likelihood": "{:.2f}",
#         "aic": "{:.2f}",
#         "nobs": "{:.0f}",
#         "LLR stat": "{:.2f}",
#         "LLR p-value": "{:.3f}"
#     }
# ).set_table_attributes('class="table table-striped"')

# # Create and print the comparison table
# latex = latex.to_latex(
#     column_format="l" + "c" * len(model_names),
#     environment="longtable",
#     hrules=True,
# )

latex = create_cox_comparison_table(cox_comparison_long_df).to_markdown(
    tablefmt="grid",
    index=True,
    # escape=True,
    floatfmt=".3f",
    # colalign=("left",) + ("center",) * (len(model_names) - 1),
)

# latex = latex.replace(r'\\cr', r'\\\\').replace(r'} \\', r'} \\\\').replace(r'} \\ \cline', r'} \\\\ \\cline').replace(r'\begin{table}', r' ').replace(r'\end{table}', r' ').replace(r'\centering', r' ').replace(r'\{', r'{').replace(r'\}', r'}')

latex = latex.replace(r'\$', r'$').replace(r'\_', r'_').replace(r'survived_int', r'survived\_int').replace(r'\textbackslash ', '\\')

# latex = r'\begin{landscape}' + '\n' + latex + r'\end{landscape}'

from IPython.display import display, Math, Latex, Markdown
display(Markdown(latex))
```

:::


```{python .landscape .smaller}
#| output: asis
#| echo: false

# latex = create_cox_comparison_table(cox_comparison_long_df).style.format(
#     # format the numbers in the table
#     {
#         "display_coef": lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x,
#         "log_likelihood": "{:.2f}",
#         "aic": "{:.2f}",
#         "nobs": "{:.0f}",
#         "LLR stat": "{:.2f}",
#         "LLR p-value": "{:.3f}"
#     }
# ).set_table_attributes('class="table table-striped"')

# # Create and print the comparison table
# latex = latex.to_latex(
#     column_format="l" + "c" * len(model_names),
#     environment="longtable",
#     hrules=True,
# )

# add adjustbox to make it fit page width
# latex = r'\begin{adjustbox}{max width=\textwidth}' + '\n' + latex + r'\end{adjustbox}'


# display(Latex(create_cox_comparison_table(cox_comparison_long_df)))

```

<!-- ```{=latex}
\end{adjustbox}
``` -->
  

## Code appendix {.appendix .unnumbered}

```{.sql .appendix .cypher #lst-family-heuristics include="../../../data_processing/cypher/26_1_family_heuristics.cypher" filename="../../../data_processing/cypher/26_1_family_heuristics.cypher" lst-cap="Cypher query compute the Levenshtein distance of last names and patronymics and merge the imputed family relationship"}
```

{{< pagebreak >}}



## References {.unnumbered}

::: {#refs}
:::

