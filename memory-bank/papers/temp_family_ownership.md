# Family Ownership and Control in Banking Networks: A Graph-Based Approach

## 1. Introduction

The analysis of ownership concentration in financial institutions represents a crucial dimension for understanding corporate governance, risk management practices, and control mechanisms within banking systems. The structure of ownership and control in banking institutions has been linked to lending practices (La Porta et al., 2003), risk-taking behavior (Laeven and Levine, 2009), and overall financial stability (Claessens and Yurtoglu, 2013). Among various ownership structures, family ownership and control deserve particular attention due to their prevalence across different markets and their distinct implications for corporate behavior (Anderson and Reeb, 2003; Villalonga and Amit, 2006).

This paper introduces a comprehensive framework for measuring family ownership concentration in banking networks through graph-based data structures. Our approach leverages the power of graph database technologies to capture multidimensional aspects of family ownership, including direct ownership stakes, family relationships, and indirect control mechanisms through complex corporate structures. By applying network science principles to the banking ownership data represented in our Neo4j database, we are able to quantify the extent and intensity of family control with greater precision than traditional ownership analysis methods.

## 2. Theoretical Framework

### 2.1 Family Ownership in Banking: Conceptual Foundations

Family ownership in banking has been the subject of extensive research in corporate governance literature. Morck et al. (2005) highlight that family control often extends beyond direct equity stakes through various mechanisms, including pyramidal structures, cross-holdings, and dual-class shares. Barontini and Caprio (2006) demonstrate that family control in European corporations often persists even when the direct ownership stake is relatively modest. In the banking sector specifically, Laeven (2013) notes that family ownership structures can significantly influence bank stability and lending practices, particularly in emerging markets.

These findings suggest that traditional measures of ownership concentration, which focus solely on direct equity stakes, may substantially underestimate the actual level of family influence within banking institutions. Our graph-based approach addresses this limitation by capturing both direct and indirect family control mechanisms through a comprehensive network analysis framework.

### 2.2 Network Science in Ownership Analysis

Network science provides powerful tools for analyzing complex ownership structures (Vitali et al., 2011; Glattfelder, 2013). In this approach, ownership relationships are represented as a directed graph $G = (V, E)$, where nodes $V$ represent entities (banks, companies, individuals) and edges $E$ represent ownership stakes. Following Battiston et al. (2012), we can define the weight of an edge $e_{ij} \in E$ as the ownership percentage that entity $i$ holds in entity $j$.

Building on this foundation, we introduce family relationships as additional edges in the graph, creating a multiplex network structure that captures both ownership and family ties. This approach aligns with recent developments in multilayer network analysis (Kivelä et al., 2014) and allows us to identify complex control patterns that emerge from the interaction between ownership and family relationships.

## 3. Data Structure and Methodology

### 3.1 Graph Database Schema

Our analysis utilizes a Neo4j graph database with a rich schema that captures various entities and relationships relevant to banking ownership structures. The primary node types include:

- **Bank**: Banking institutions, identified by properties such as `bank_regn`, `full_name`, and various financial indicators
- **Company**: Corporate entities that may own banks or be part of ownership chains
- **Person**: Individual shareholders or family members
- **Ent**: A broader category of entities that may include various organizational forms

Key relationship types in the schema include:

- **OWNERSHIP**: Represents equity stakes between entities, with properties including `FaceValue`, `Size`, and `date`
- **FAMILY**: Represents family relationships between individuals
- **CONTROL**: Represents control relationships that may exist without formal ownership
- **MANAGEMENT**: Captures management positions held by individuals in organizations

This schema allows us to construct sophisticated queries that traverse the network to identify both direct and indirect family control patterns.

### 3.2 Family Ownership Metrics

Based on this graph structure, we have developed a set of metrics to quantify family ownership and control in banking networks. Our Cypher query computes these metrics for a specific bank identified by its registration number. Each component of the query's return statement corresponds to a distinct aspect of family ownership and control:

## 4. Metric Components and Mathematical Formulation

### 4.1 Direct Family Ownership Value

The direct family ownership value, denoted as $FOV_d(b)$ for a bank $b$, represents the total ownership value held by shareholders who are part of family networks. Mathematically, it is defined as:

$$FOV_d(b) = \sum_{i \in D_b} \omega_i \cdot \mathbf{1}_{F}(i)$$

Where:
- $D_b$ is the set of direct owners of bank $b$
- $\omega_i$ is the ownership value (either `FaceValue` or `Size` properties) held by owner $i$
- $\mathbf{1}_{F}(i)$ is an indicator function that equals 1 if owner $i$ has at least one family connection and 0 otherwise

This metric, represented as `direct_family_owned` in our query, quantifies the absolute magnitude of ownership concentrated in family-connected shareholders. As noted by Maury (2006), the magnitude of family ownership is positively associated with firm valuation in contexts with moderate shareholder protection, making this an important dimension of control.

### 4.2 Total Ownership Value

The total ownership value, denoted as $TOV(b)$ for a bank $b$, represents the sum of all direct ownership stakes in the bank. It is mathematically defined as:

$$TOV(b) = \sum_{i \in D_b} \omega_i$$

Where $D_b$ and $\omega_i$ are defined as above. This metric, represented as `total_direct_owned` in our query, provides the baseline against which family ownership concentration can be measured. Demsetz and Villalonga (2001) emphasize the importance of considering the total ownership structure when analyzing corporate performance and governance.

### 4.3 Family Ownership Percentage

The family ownership percentage, denoted as $FOP(b)$ for a bank $b$, represents the proportion of total ownership that is held by family-connected shareholders. It is mathematically defined as:

$$FOP(b) = \begin{cases}
\frac{FOV_d(b)}{TOV(b)} \times 100\%, & \text{if } TOV(b) > 0 \\
0, & \text{otherwise}
\end{cases}$$

This normalized metric, calculated in our query using the expression `100.0 * direct_family_owned / total_direct_owned`, allows for comparative analysis across different banks regardless of their absolute size or capitalization. Claessens et al. (2002) utilize similar percentage-based measures to analyze the separation of ownership and control in East Asian corporations, demonstrating the value of such normalized metrics in cross-sectional analyses.

### 4.4 Direct Owner Count

The direct owner count, denoted as $|D_b|$ for a bank $b$, represents the total number of direct shareholders. This structural metric provides context for understanding ownership dispersion or concentration. LaPorta et al. (1999) identify ownership concentration as a key dimension of corporate governance across different legal systems, with implications for investor protection and capital market development.

In our framework, represented as `direct_owner_count` in the query, this metric serves as a denominator for calculating relative measures of family influence. It also provides important context for interpreting other metrics, as the significance of family ownership may vary depending on whether ownership is widely dispersed or highly concentrated.

### 4.5 Total Family Connections

The total family connections, denoted as $|F_b|$ for a bank $b$, represents the count of family relationships among the direct owners of the bank. Mathematically, it is defined as:

$$|F_b| = \sum_{i \in D_b} |N_F(i)|$$

Where $N_F(i)$ represents the set of family members connected to owner $i$. This metric, represented as `total_family_connections` in our query, quantifies the density of family networks within the ownership structure.

Bertrand et al. (2008) demonstrate in their study of Thai business groups that family networks can significantly influence business decisions and resource allocation, highlighting the importance of measuring family connection intensity. Our metric builds on this insight by explicitly quantifying the extent of family relationships within the ownership structure.

### 4.6 Family-Controlled Companies

The family-controlled companies metric, denoted as $|C_F(b)|$ for a bank $b$, represents the count of companies that are controlled by family members and have ownership stakes in the bank. In network terms, these are companies that lie on paths between family members and the bank, where the paths consist of multiple OWNERSHIP relationships. Mathematically, it is defined as:

$$|C_F(b)| = |\{c \in V \mid \exists f \in V, \exists p: f \xrightarrow{\text{OWNERSHIP}^*} c \xrightarrow{\text{OWNERSHIP}} b, \text{ and } \exists g: (f) \xrightarrow{\text{FAMILY}} g\}|$$

Where $V$ is the set of all nodes in the graph, and $p$ represents a path of one or more OWNERSHIP relationships. This metric, represented as `family_controlled_companies` in our query, captures indirect family control through corporate structures.

Almeida and Wolfenzon (2006) develop a theoretical framework for analyzing pyramidal ownership structures in family business groups, demonstrating how such structures can magnify family control beyond direct ownership stakes. Our metric operationalizes this concept by explicitly identifying companies that serve as intermediaries for family control.

### 4.7 Family Connection Ratio

The family connection ratio, denoted as $\rho_F(b)$ for a bank $b$, represents the average number of family connections per direct owner. Mathematically, it is defined as:

$$\rho_F(b) = \begin{cases}
\frac{|F_b|}{|D_b|}, & \text{if } |D_b| > 0 \\
0, & \text{otherwise}
\end{cases}$$

Where $|F_b|$ and $|D_b|$ are defined as above. This normalized metric, calculated in our query using the expression `toFloat(total_family_connections) / direct_owner_count`, provides a measure of the relative intensity of family networks in the ownership structure.

Khanna and Rivkin (2001) emphasize the importance of network density in business groups, noting that denser networks facilitate information sharing and coordinated action. Our family connection ratio extends this concept to family networks specifically, providing a measure of how intensely family relationships permeate the ownership structure.

## 5. Applications and Implications

### 5.1 Regulatory Oversight and Transparency

The comprehensive measurement of family ownership and control has significant implications for regulatory oversight. As noted by Barth et al. (2013), accurate disclosure of ultimate beneficial ownership is crucial for effective banking supervision and risk assessment. Our metrics provide regulators with tools to identify complex family control patterns that might not be apparent from standard ownership disclosures.

### 5.2 Corporate Governance Analysis

From a corporate governance perspective, the metrics enable more nuanced analysis of how family control influences governance structures and decision-making processes. Villalonga and Amit (2006) find that the effect of family ownership on firm value depends on whether the founder serves as CEO or as chairman, highlighting the complex interaction between ownership and management. Our multidimensional approach allows researchers to disentangle these effects by providing a more complete picture of family influence.

### 5.3 Systemic Risk Assessment

At the system level, the identification of family-controlled networks can contribute to the assessment of interconnectedness and potential contagion pathways in the financial system. As demonstrated by Battiston et al. (2012), ownership networks can amplify financial distress through various mechanisms. By incorporating family relationships into the analysis, our approach provides a more comprehensive view of potential correlation in risk-taking behavior across seemingly independent institutions.

## 6. Conclusion

This paper has presented a comprehensive framework for measuring family ownership and control in banking networks using graph-based data structures. By leveraging the rich relationship information captured in our Neo4j database, we have developed a set of metrics that quantify different dimensions of family influence, from direct ownership stakes to complex control patterns through corporate structures.

The mathematical formulations provided for each metric establish a solid foundation for comparative analysis across different banks, markets, and time periods. The integration of network science principles with traditional corporate governance concepts enables a more nuanced understanding of how family relationships interact with formal ownership structures to shape control patterns in banking systems.

Future research can build on this framework by exploring the dynamic evolution of family ownership networks over time, the relationship between family control metrics and bank performance or risk-taking behavior, and comparative analyses across different regulatory and cultural contexts.

## References

Almeida, H., & Wolfenzon, D. (2006). A theory of pyramidal ownership and family business groups. *Journal of Finance*, 61(6), 2637-2680.

Anderson, R. C., & Reeb, D. M. (2003). Founding-family ownership and firm performance: Evidence from the S&P 500. *Journal of Finance*, 58(3), 1301-1328.

Barontini, R., & Caprio, L. (2006). The effect of family control on firm value and performance: Evidence from continental Europe. *European Financial Management*, 12(5), 689-723.

Barth, J. R., Caprio, G., & Levine, R. (2013). Bank regulation and supervision in 180 countries from 1999 to 2011. *Journal of Financial Economic Policy*, 5(2), 111-219.

Battiston, S., Puliga, M., Kaushik, R., Tasca, P., & Caldarelli, G. (2012). DebtRank: Too central to fail? Financial networks, the FED and systemic risk. *Scientific Reports*, 2(1), 1-6.

Bertrand, M., Johnson, S., Samphantharak, K., & Schoar, A. (2008). Mixing family with business: A study of Thai business groups and the families behind them. *Journal of Financial Economics*, 88(3), 466-498.

Claessens, S., Djankov, S., & Lang, L. H. (2000). The separation of ownership and control in East Asian corporations. *Journal of Financial Economics*, 58(1-2), 81-112.

Claessens, S., & Yurtoglu, B. B. (2013). Corporate governance in emerging markets: A survey. *Emerging Markets Review*, 15, 1-33.

Demsetz, H., & Villalonga, B. (2001). Ownership structure and corporate performance. *Journal of Corporate Finance*, 7(3), 209-233.

Glattfelder, J. B. (2013). *Decoding complexity: Uncovering patterns in economic networks*. Springer.

Khanna, T., & Rivkin, J. W. (2001). Estimating the performance effects of business groups in emerging markets. *Strategic Management Journal*, 22(1), 45-74.

Kivelä, M., Arenas, A., Barthelemy, M., Gleeson, J. P., Moreno, Y., & Porter, M. A. (2014). Multilayer networks. *Journal of Complex Networks*, 2(3), 203-271.

La Porta, R., Lopez-de-Silanes, F., & Shleifer, A. (1999). Corporate ownership around the world. *Journal of Finance*, 54(2), 471-517.

La Porta, R., Lopez-de-Silanes, F., & Zamarripa, G. (2003). Related lending. *The Quarterly Journal of Economics*, 118(1), 231-268.

Laeven, L. (2013). Corporate governance: What's special about banks? *Annual Review of Financial Economics*, 5(1), 63-92.

Laeven, L., & Levine, R. (2009). Bank governance, regulation and risk taking. *Journal of Financial Economics*, 93(2), 259-275.

Maury, B. (2006). Family ownership and firm performance: Empirical evidence from Western European corporations. *Journal of Corporate Finance*, 12(2), 321-341.

Morck, R., Wolfenzon, D., & Yeung, B. (2005). Corporate governance, economic entrenchment, and growth. *Journal of Economic Literature*, 43(3), 655-720.

Villalonga, B., & Amit, R. (2006). How do family ownership, control and management affect firm value? *Journal of Financial Economics*, 80(2), 385-417.

Vitali, S., Glattfelder, J. B., & Battiston, S. (2011). The network of global corporate control. *PloS one*, 6(10), e25995.
