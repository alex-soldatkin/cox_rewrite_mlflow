# Quarto Document Review

## General Assessment

The documents present a highly coherent, logically structured, and well-argued analysis. The narrative arc regarding "Substitution vs. Interference" is developed consistently from the Introduction through to the Conclusion. The integration of the "Network Firefighter" concept in the Discussion adds significant depth and effectively addresses potential endogeneity concerns.

Your writing is clear, precise, and academic. The use of British English is consistent.

## Inconsistencies & Issues

### 1. **CRITICAL: "H3" Naming Collision**
There is a significant naming collision regarding the label "H3":

*   **In `04-hypotheses.qmd`**: "H3" refers to **Temporal stability (structural breaks)** (H3a: Regime-Dependent Effects, H3b: Substitution-Interference Transition).
*   **In `03-institutional-context.qmd` (lines 92-96)** and **`05-data.qmd` (line 92)**: "H3" is used to label the **Internal Capital Markets** mechanism proxies (H3 Basic, H3+ Enhanced, H3++ Deep).

**Recommendation**: Rename the mechanism proxies in `03` and `05` to avoid confusion with the main hypotheses. For example, use "M3 proxies" (Mechanism 3) or "ICM proxies" (Internal Capital Markets).

### 2. Capitalisation consistency
*   **Transaction Cost Economics**:
    *   `03-institutional-context.qmd`, line 56: `## Transaction Cost Economics mechanisms` (Title Case).
    *   `06-methods.qmd`, line 37: `### Experiment 1: Transaction cost mechanisms` (Sentence case).
    *   `09-conclusion.qmd`, line 9: "...Transaction Cost Economics mechanisms..." (Title Case).
    *   **Recommendation**: Standardise. If treating "Transaction Cost Economics" as a proper noun (the specific theory), Title Case is appropriate for the theory name, but the header in `06` should probably match `03` or be fully sentence case ("Transaction cost economics mechanisms") depending on your strict adherence to sentence case. Given `03` uses proper noun capitalization for the theory, `06` should likely align.

### 3. Punctuation with Single Quotes
British English typically places punctuation **outside** the closing quotation mark unless the quote is a complete sentence.
*   **`01-introduction.qmd`, line 17**: `'substitution' and 'interference.'` (Period is inside).
    *   **Recommendation**: Change to `'interference'.`

### 4. Heading Case
*   Headings are largely consistent in Sentence case.
*   Check `03-institutional-context.qmd`: `## Ledeneva's substitution--interference framework`. (Correct).
*   Check `05-data.qmd`: `### Central Bank of Russia (CBR) ownership disclosures`. (Correct - Proper names capitalized).

### 5. Formatting
*   **`03-institutional-context.qmd`, line 46**: `Foreign \times` in table cell.
    *   **Recommendation**: Ensure this renders correctly in your output format. Markdown tables sometimes require specific escaping or math delimiters (`$Foreign \times$`) if targeting PDF/LaTeX, or might render raw if not.

## British English Check
The text consistently uses British spellings. Verified occurrences:
*   *optimisation* (multiple)
*   *defence* (as in Ministry of Defence / defence feedback)
*   *programme* (institutional consolidation programme)
*   *centre* / *epicentre*
*   *behaviour*
*   *signalling*
*   *licence* (noun)

## Clarity of Argument
*   **Story Arc**: Strong. The distinction between "exogenous economic shocks" (2008) and "endogenous geopolitical shocks" (2014) is well-explained and crucial for the H2b hypothesis.
*   **Metaphors**: The "network firefighter" analogy in `08-discussion.qmd` is excellent for explaining high centrality of survivors.
*   **Conclusion**: Effectively summarizes the contributions without just repeating the abstract.

## Action Plan
1.  **Fix the H3 naming collision** in `03-institutional-context.qmd` and `05-data.qmd`.
2.  **Standardise capitalization** for "Transaction Cost Economics".
3.  **Move the period** outside the quote in `01-introduction.qmd`.

## Methodology Review (`06-methods.qmd`)

### General Assessment
The methodology section provides a robust and well-justified econometric framework. The choice of **Cox Proportional Hazards** models is appropriate given the right-censored nature of the data and the need to incorporate time-varying covariates (financial ratios, ownership structure).

The **stratification strategy** (Regional, Sectoral, Community) is a strong point, particularly the use of Louvain communities to address network structure confounding. The "Network Firefighter" alternative explanation is well-handled by this design.

The experimental design is broken down logically into four distinct experiments that map clearly to the research questions.

### Specific Issues
1.  **"H3" Collision (Confirmed)**:
    *   Table `tbl-model-specs-exp010` (lines 51, 54) uses "H3+" and "H3++" to refer to enhanced Internal Capital Markets mechanism proxies.
    *   **Action**: This confirms the need to rename these mechanism proxies (e.g., to "M3+" or "ICM+") to avoid confusion with Hypothesis 3 (Temporal Stability).

2.  **Capitalisation**:
    *   Line 37: `### Experiment 1: Transaction cost mechanisms` (Sentence case).
    *   Line 56: `Transaction Cost Economics` (Title Case used as proper noun modifier).
    *   **Recommendation**: Review for consistency. If "Transaction Cost Economics" is a proper noun, it should be capitalized in the header as well, or lowercase used consistently if referring to the general concept.

3.  **Typos / Phrasing**:
    *   Line 115: "...introduces additional complexity that current ERGM implementations do not handle efficiently." - Clear and valid justification for not using ERGMs.
    *   The spelling of "penalised", "penaliser", and "modelling" is correctly British.

4.  **Table Formatting**:
    *   Line 45: The table structure looks correct.

## Story Arc Improvements

While the narrative is strong, the following adjustments could enhance the impact and flow:

### 1. Foreshadowing the "Network Firefighter"
The "Network Firefighter" concept in the Discussion (that centrality is endogenous/involuntary for survivors) is a powerful insight but comes somewhat unexpectedly.
*   **Suggestion**: Hint at this ambiguity in the **Introduction** or **Institutional Context**. When introducing network centrality, mention that high centrality in a turbulent market can be a sign of *strength* (empire building) or *burden* (forced acquisition). This sets the stage for the Discussion finding.

### 2. Validating the "Evolution of Informal Governance"
The finding that family connections become *more* protective under Nabiullina (despite the cleanup) is counter-intuitive and fascinating.
*   **Suggestion**: Frame this explicitly as a story of **"Adaptation and Selection"**. The cleanup didn't kill informal governance; it selected for the most sophisticated practitioners. Explicitly framing it as "Survival of the Most Opaque" in the Discussion/Conclusion would make this paradox a core feature of the narrative rather than just a statistical result.

### 3. Visualising the Transition
The shift from Substitution (2004-2008) to Interference (2013-2020) is the central theoretical contribution.
*   **Suggestion**: A conceptual diagram or timeline figure in `03-institutional-context.qmd` or `09-conclusion.qmd` mapping the three periods to the dominant mechanism would anchor this concept visually.
*   **Example**: A timeline showing the Sodbiznesbank crisis (Start of Substitution need), the GFC (Peak Substitution), and the Nabiullina/Sanctions era (Shift to Interference).

### 4. Bookending the Narrative
*   **Suggestion**: In the **Conclusion**, explicitly reference the Sodbiznesbank vs. Otkritie cases again to "bookend" the story. "We began with the physical barricades of Sodbiznesbank (substitution of law) and ended with the complex balance sheet sanitisation of Otkritie (interference with law)." This reinforces the journey from crude to sophisticated informal governance.
