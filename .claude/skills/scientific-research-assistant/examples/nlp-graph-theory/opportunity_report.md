# Graph Neural Networks for Text Classification: Research Opportunities for a Student Project

**Report type:** Research Opportunity Report  
**Generated:** 2026-10-13

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | NLP and graph theory (graph neural networks for text classification) | stated by user |
| experience | undergraduate, comfortable with Python | default (not stated by user) |
| hardware | one consumer GPU, 8 GB VRAM | default (not stated by user) |
| gpu vram gb | 8 | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| language | Python | default (not stated by user) |
| difficulty | moderate | default (not stated by user) |
| mode | any | default (not stated by user) |

## Summary

Graph neural networks for text classification are well studied: the search returned two recent surveys ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456)) and hundreds of method papers. The most useful finding is a published challenge to the whole line of work ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)). Three project ideas survived an attempt to disprove them, all as replications or extensions; a fourth was rejected because it has already been done.

## Decisions

Each shortlisted research question gets go, conditional go or no-go. A go requires full-text reading of the closest work and an explicit check for leakage, weak baselines and evaluation flaws; anything short of that is at most a conditional go.

| Research question | Decision | Novelty confidence | Mode | Main conditions |
| --- | --- | --- | --- | --- |
| Does a bag-of-words wide MLP still match text-graph models published after 2022? | CONDITIONAL GO | low | extension | Read the experiment and limitation sections of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)), ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)), ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)) and confirm the comparison is absent; Obtain ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)); if it already runs this comparison, reject or reframe as a replication |
| How sensitive is TextGCN to the random seed and to the co-occurrence window used to build its graph? | CONDITIONAL GO | very_low | extension | Read the experiment and limitation sections of ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)), ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and confirm the comparison is absent |
| Do text-graph classifiers beat a bag-of-words MLP on low-resource languages? | CONDITIONAL GO | low | extension | Read the experiment and limitation sections of ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561)), ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and confirm the comparison is absent |
| Is a text graph necessary for text classification at all? | NO-GO | very_low | original | not reported |

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | verified: 9 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: abstract: 8, not accessible: 1; claims: estimate: 6, speculative: 3, verified: 11 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | Does a bag-of-words wide MLP still match text-graph models published after 2022?: low; How sensitive is TextGCN to the random seed and to the co-occurrence window used to build its graph?: very_low; Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?: low; Is a text graph necessary for text classification at all?: very_low | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## How the literature was searched

- **Sources that answered:** openalex, arxiv, crossref, huggingface
- **Sources that failed or were skipped:** semantic_scholar (rate_limited: HTTP 429 after retries)
- **Search strategies:** keyword, recent, foundational, limitations, surveys, citation exploration, novelty challenge (keyword, surveys, recent)
- **Date range:** 2018 onwards
- **Records retrieved / after deduplication:** 1113 / 397
- **Search date:** 2026-10-13
- **Queries:** `graph neural network text classification`; `graph neural network document classification`; `graph convolutional network text classification`; `graph convolutional network document classification`
- Semantic Scholar answered single-paper lookups but rejected search requests (HTTP 429, no API key).
- OpenAlex's keyless daily budget ran out late in the session; the reproduction check for ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)) could not query citing works.
- Summaries in the table come from abstracts only. No full text was read.

## What has already been done

| Paper | Published | Method | Datasets | Findings | Stated limitations | Read | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Graph Convolutional Networks for Text Classification (Yao et al. 2019) | 2019-07-17 | One corpus-level graph of words and documents (word co-occurrence and document-word edges); GCN on one-hot inputs (TextGCN) | Multiple benchmark datasets (not named in the abstract) | Reports outperforming the then state of the art without external embeddings; the margin grows as training data shrinks | not reported | abstract | [link](https://doi.org/10.1609/aaai.v33i01.33017370) |
| Every Document Owns Its Structure: Inductive Text Classification via Graph Neural Networks (Zhang et al. 2020) | 2020 | One graph per document; GNN learns word representations inductively (TextING) | Four benchmark datasets (not named in the abstract) | Reports outperforming prior text classifiers; handles words unseen in training | Abstract criticises earlier corpus-level graphs for missing in-document context and not being inductive | abstract | [link](https://doi.org/10.18653/v1/2020.acl-main.31) |
| Bag-of-Words vs. Graph vs. Sequence in Text Classification: Questioning the Necessity of Text-Graphs and the Surprising Strength of a Wide MLP (Galke & Scherp 2022) | 2022 | Wide MLP on bag-of-words; fine-tuned BERT and DistilBERT; compared with TextGCN, HeteGCN, HyperGAT | Not named in the abstract | BoW wide MLP outperforms TextGCN and HeteGCN in the inductive setting and is comparable with HyperGAT; fine-tuned BERT and DistilBERT outperform all | Abstract notes TextGCN needs an O(N^2) graph and Transformers O(L^2) attention; own limitations not stated in the abstract | abstract | [link](https://doi.org/10.18653/v1/2022.acl-long.279) |
| Pitfalls of Graph Neural Network Evaluation (Shchur et al. 2018) | 2018-11-14 | Re-evaluation of four GNN models for node classification under varied data splits | Node-classification graphs (not text) | Different splits give dramatically different model rankings; simpler GNNs can beat complex ones under fair tuning | Concerns node classification, not text graphs | abstract | [link](https://arxiv.org/abs/1811.05868) |
| Token-Level Graphs for Short Text Classification (Donabauer & Kruschwitz 2025) | 2025 | Text graphs built from pre-trained language model tokens and embeddings (TokenGraph) | Short-text datasets (not named in the abstract) | Reports higher or on-par scores versus existing methods with few training samples; code stated to be public | Abstract lists limits of earlier graph methods (word sense, transductive setting), not its own | abstract | [link](https://doi.org/10.1007/978-3-031-88714-7_42) |
| Graph Neural Networks for Text Classification: A Survey (Wang et al. 2024) | 2024-07-01 | Survey of corpus-level and document-level GNNs for text classification up to 2023 | Summarises public benchmarks | Compares published performance, graph construction and evaluation practice; lists open issues | not reported | abstract | [link](https://doi.org/10.1007/s10462-024-10808-0) |
| BoW-based neural networks vs. cutting-edge models for single-label text classification (Abdalla et al. 2023) | 2023-07-18 | Bag-of-words neural networks compared with recent models (from the title; abstract unavailable to the sources queried) | not reported | not reported | not reported | not accessible | [link](https://doi.org/10.1007/s00521-023-08754-z) |
| Text Classification Using Graph Convolutional Networks: A Comprehensive Survey (Rizvi et al. 2025) | 2025-01-21 | Survey of GCN-based text classification by architecture and supervision mode | Compares methods on benchmark datasets | Identifies strengths and limitations and future directions | not reported | abstract | [link](https://doi.org/10.1145/3714456) |
| GNoM: Graph Neural Network Enhanced Language Models for Disaster Related Multilingual Text Classification (Ghosh et al. 2022) | 2022-06-26 | Corpus-level GNN combined with transformer language models through cross-attention (GNoM) | Nine English and non-English disaster datasets | Reports outperforming a multilingual BERT baseline in weighted F1 under limited supervision | Abstract says prior work is mostly English-only; own limitations not stated | abstract | [link](https://doi.org/10.1145/3501247.3531561) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

### Directions that are already well explored

- [V] Proposing new graph constructions and GNN architectures for text classification, catalogued in two surveys ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456))
- [V] Comparing TextGCN-era graph models with a bag-of-words MLP and fine-tuned BERT ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))
- [V] Inductive, per-document graph models ([Zhang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.31))

## Ranked research opportunities

Each opportunity below survived an explicit search for work that already addresses it. None is claimed to be novel: the novelty confidence states how far the search supports the gap, and what it could have missed.

### 1. Does a bag-of-words wide MLP still match text-graph models published after 2022?
**Type of gap:** Underexplored experimental setting  
**Recommended mode:** extension  
**Revised:** Started as 'is the text graph necessary at all?', which ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) already answers for TextGCN, HeteGCN and HyperGAT. Narrowed to graph models that appeared afterwards.

**Research question.** Under one protocol with several random seeds, does a wide MLP on bag-of-words reach the accuracy of text-graph classifiers published after 2022 on the standard benchmarks?

**Motivation.** The comparison in ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) covers three graph models. Graph-based methods have kept appearing and reporting gains over existing methods ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)), and two recent surveys catalogue many of them ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456)).

**Supporting papers.** ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279); [Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42); [Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456))

**Closest existing work.**
- ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) [read: abstract; overlap: partial]: Same question and method, but its abstract names only TextGCN, HeteGCN and HyperGAT as graph baselines.
- ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)) [read: not accessible; overlap: unknown]: Unknown. The title suggests a very similar comparison, and neither abstract nor open full text could be retrieved. It must be read before this project starts; it may already cover the gap.
- ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)) [read: abstract; overlap: partial]: Proposes a new graph model and compares it with existing methods; the abstract does not say whether a tuned bag-of-words MLP is among them.

**Evidence for the gap.**
- [V] The abstract of the baseline study lists three graph models as comparisons ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))
- [V] A later graph model reports higher or on-par scores than existing methods ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42))
- [S] Newer graph papers may not include a strong bag-of-words MLP baseline

**Potential contribution.** [E] A multi-seed replication of a published negative result plus an updated comparison; useful whichever way it comes out

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The challenge found closely worded prior work. ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)) was not readable, follow-up work by the same authors may exist, and Semantic Scholar search was unavailable (sources that answered: openalex, arxiv, crossref, huggingface).
Attempts to disprove novelty: 4 search(es); signal `close_prior_work_found`. Queries: `bag-of-words MLP versus graph neural network text classification`; `text graph necessity text classification simple baseline`; `are text graphs necessary text classification`; `TextGCN strong baseline comparison logistic regression`

**Feasibility.**
- [V] Both codebases are public; see ranking entry O1
- [E] About 6 weeks on one 8 GB GPU

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| train test overlap | not checked | Benchmark splits were not inspected for duplicate or near-duplicate documents | not reported |
| weak baseline | not checked | Whether published graph models were compared with a tuned bag-of-words MLP was read from abstracts only | not reported |
| insufficient runs | not checked | Number of runs in the closest papers not read from their experiment sections | not reported |

**Decision: CONDITIONAL GO.** The gap rests on abstracts only; the closest papers must be read in full before committing.

**Conditions before committing.**
- Read the experiment and limitation sections of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)), ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)), ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)) and confirm the comparison is absent
- Obtain ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)); if it already runs this comparison, reject or reframe as a replication

**Unresolved evidence and risks.** Leakage, baseline strength and run counts in the benchmark were not checked

### 2. How sensitive is TextGCN to the random seed and to the co-occurrence window used to build its graph?
**Type of gap:** Unverified novelty hypothesis  
**Recommended mode:** extension

**Research question.** How much does TextGCN test accuracy vary across random seeds and across sliding-window sizes for word co-occurrence edges, relative to the gaps reported between methods?

**Motivation.** For node classification, changing data splits and training procedure changed which GNN looked best ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)). TextGCN builds its graph from word co-occurrence ([Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370)), a design choice with free parameters.

**Supporting papers.** ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868); [Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370))

**Closest existing work.**
- ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)) [read: abstract; overlap: partial]: Studies evaluation sensitivity for node classification on standard graph datasets, not text graphs.
- ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) [read: abstract; overlap: partial]: Compares model families; its abstract does not mention seed or graph-construction sensitivity.

**Evidence for the gap.**
- [V] Evaluation choices changed GNN rankings in node classification ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868))
- [V] The automated check found no seed handling in the TextGCN repository (README and file names only; code was not read)
- [S] The same sensitivity may apply to text graphs

**Potential contribution.** [E] Variance estimates that tell readers whether small reported gaps between text-graph methods are meaningful

**Novelty confidence:** very_low (scale: very_low, low, medium; a search cannot establish more). The challenge search retrieved almost nothing related, so it says little either way. Ablations of window size may sit inside method papers and surveys ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0)) whose full text was not read.
Attempts to disprove novelty: 4 search(es); signal `no_close_match_in_this_search`. Queries: `TextGCN random seed variance reproducibility`; `text graph construction window size sensitivity graph convolutional network text classification`; `graph construction ablation text classification graph neural network`; `reproducibility study graph convolutional network text classification`

**Feasibility.** [E] One codebase and a parameter sweep; memory need on larger benchmarks is unknown (ranking entry O2 leaves compute unscored)

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| train test overlap | not checked | Benchmark splits were not inspected for duplicate or near-duplicate documents | not reported |
| weak baseline | not checked | Whether published graph models were compared with a tuned bag-of-words MLP was read from abstracts only | not reported |
| insufficient runs | not checked | Number of runs in the closest papers not read from their experiment sections | not reported |

**Decision: CONDITIONAL GO.** The gap rests on abstracts only; the closest papers must be read in full before committing.

**Conditions before committing.** Read the experiment and limitation sections of ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)), ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and confirm the comparison is absent

**Unresolved evidence and risks.** Leakage, baseline strength and run counts in the benchmark were not checked

### 3. Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?
**Type of gap:** Underexplored experimental setting  
**Recommended mode:** extension

**Research question.** On news topic classification in low-resource languages, do text-graph classifiers outperform a wide MLP on bag-of-words when all are tuned under the same budget?

**Motivation.** TextGCN reported that its advantage grows with less training data ([Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370)), and ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561)) states that existing work is mostly English-only. A verified public dataset with fixed splits exists (MasakhaNEWS).

**Supporting papers.** ([Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370); [Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561); [Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))

**Closest existing work.**
- ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561)) [read: abstract; overlap: partial]: Multilingual disaster tweets with a GNN combined with transformer language models; the abstract names a multilingual BERT baseline, not a bag-of-words MLP.
- ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) [read: abstract; overlap: partial]: Same comparison of model families; the abstract does not mention low-resource or non-English data.

**Evidence for the gap.**
- [V] Prior work is described as mostly English-only ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561))
- [V] No retrieved paper compared a bag-of-words MLP with text-graph models on low-resource languages
- [S] The paper that introduced the dataset may already report classical baselines; it was not retrieved or read

**Potential contribution.** [E] Tests whether the 'graphs help with little data' claim carries over to languages with few resources

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The tool would allow 'medium' (154 papers examined, no close match), but matching was on wording, 32 records had no abstract, and the dataset paper is unread, so 'low' is used.
Attempts to disprove novelty: 4 search(es); signal `no_close_match_in_this_search`. Queries: `graph neural network text classification low-resource language`; `text graph convolutional network non-English text classification benchmark`; `bag-of-words MLP baseline low-resource language text classification`; `TextGCN multilingual text classification comparison`

**Feasibility.**
- [V] Dataset verified: afl-3.0 licence, not gated, 31088 rows
- [E] About 8 weeks, the whole budget

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| train test overlap | not checked | Benchmark splits were not inspected for duplicate or near-duplicate documents | not reported |
| weak baseline | not checked | Whether published graph models were compared with a tuned bag-of-words MLP was read from abstracts only | not reported |
| insufficient runs | not checked | Number of runs in the closest papers not read from their experiment sections | not reported |

**Decision: CONDITIONAL GO.** The gap rests on abstracts only; the closest papers must be read in full before committing.

**Conditions before committing.** Read the experiment and limitation sections of ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561)), ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and confirm the comparison is absent

**Unresolved evidence and risks.** Leakage, baseline strength and run counts in the benchmark were not checked

### Candidates rejected after the novelty challenge

- **Is a text graph necessary for text classification at all?** (Already well studied): Already answered by ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)), found by the novelty challenge although the first literature search missed it. Reframed as opportunity 1.

## Feasibility ranking

Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any blocker removes a candidate from the ranking no matter how high its other scores are. Novelty is capped at 2 unless the closest prior work was read in full, and at 1 when that work already ran the experiment.

| Rank | Candidate | Status | Score % | Range | Scored weight % | Verified weight % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | BoW wide MLP versus post-2022 text-graph models | VIABLE | 64.8 | 64.8-64.8 | 100.0 | 34.0 |
| 2 | Seed and graph-construction sensitivity of TextGCN | VIABLE | 64.3 | 56.6-68.6 | 88.0 | 30.0 |
| 3 | BoW MLP versus text graphs on low-resource languages | VIABLE | 62.8 | 62.8-62.8 | 100.0 | 22.0 |

**Scores per criterion (0-5).**

| Criterion | Weight | O1 | O2 | O3 |
| --- | --- | --- | --- | --- |
| scientific relevance | 12 | 4 [V] | 3 [E] | 4 [E] |
| novelty or replication value | 12 | 2 [E] | 2 [E] | 2 [E] |
| paper and code availability | 10 | 4 [V] | 3 [V] | 4 [V] |
| dataset accessibility | 12 | 3 [V] | 4 [V] | 4 [V] |
| compute fit | 12 | 3 [E] | unscored | 4 [E] |
| implementation simplicity | 10 | 3 [E] | 4 [E] | 2 [E] |
| time fit | 10 | 3 [E] | 4 [E] | 2 [E] |
| reproducibility | 8 | 3 [E] | 2 [V] | 3 [E] |
| evaluation clarity | 7 | 4 [E] | 4 [E] | 3 [E] |
| low failure risk | 7 | 4 [E] | 3 [E] | 3 [E] |

**BoW wide MLP versus post-2022 text-graph models**
- scientific relevance: Two surveys published in 2024 and 2025 show the area is active ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456)); The baseline result it builds on appeared at ACL 2022 ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))
- novelty or replication value: Novelty confidence is low, but a multi-seed replication of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) has value by itself
- paper and code availability: https://github.com/lgalke/text-clf-baselines (licence MIT, last push 2026-04-21); https://github.com/doGregor/TokenGraph responds (HTTP 200); its contents were not inspected
- dataset accessibility: Benchmark files are in the TextGCN repository data folder (URL responds, HTTP 200)
- compute fit: An MLP on bag-of-words is light; token-graph models need pre-trained language model embeddings, which should fit 8 GB for short texts
- implementation simplicity: Two existing codebases must be run under one protocol; no new model is needed
- time fit: About 6 weeks: 2 for setup, 3 for runs over 5 seeds, 1 for analysis
- reproducibility: The MLP codebase pins dependencies (requirements.txt, uv.lock); seeds must be added by the student
- evaluation clarity: Accuracy on shared benchmarks with published numbers to compare against
- low failure risk: Either outcome (MLP still competitive, or not) is reportable
- Missing: paper_and_code_availability: Licence and completeness of the TokenGraph repository
- Missing: dataset_accessibility: Licence of the benchmark files is not stated by any API
- Missing: compute_fit: No hardware statement found for either codebase
- Capped: novelty or replication value 3 -> 2 (closest prior work read at level 'abstract', not full text)

**Seed and graph-construction sensitivity of TextGCN**
- scientific relevance: Evaluation sensitivity changed GNN rankings in node classification ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)); relevance to text graphs is an inference
- novelty or replication value: The challenge search did not reach closely related work, so it supports almost nothing
- paper and code availability: https://github.com/yao8839836/text_gcn exists; no licence; 112 open issues
- dataset accessibility: Data and preparation scripts are in the same repository (build_graph.py, prepare_data.py)
- implementation simplicity: One codebase; the study is a parameter sweep
- time fit: About 5 weeks, dominated by environment setup for a 2018 codebase
- reproducibility: No dependency file and no seed handling were found by the automated check of the repository
- evaluation clarity: Accuracy mean and standard deviation over seeds and window sizes
- low failure risk: A flat result is still reportable, but the legacy TensorFlow stack may not install
- Missing: dataset_accessibility: Licence of the benchmark files
- Missing: compute_fit: No hardware statement found; [@galke2022] notes the graph is O(N^2) in vocabulary plus corpus size, so memory on the larger benchmarks is unknown
- Not scored for lack of evidence: compute_fit

**BoW MLP versus text graphs on low-resource languages**
- scientific relevance: ([Ghosh et al. 2022](https://doi.org/10.1145/3501247.3531561)) states that existing work is mostly English-only
- novelty or replication value: No close match was retrieved, but the dataset's own paper was not read and may report similar baselines
- paper and code availability: https://github.com/lgalke/text-clf-baselines (licence MIT)
- dataset accessibility: https://huggingface.co/datasets/masakhane/masakhanews: licence afl-3.0, not gated, 31088 rows, about 96.3 MB to download, 96.4 MB in memory (dataset viewer figures)
- compute fit: Small corpora (a few thousand documents per language)
- implementation simplicity: Graph models need tokenisation and graph construction for each new language; nothing is pre-built
- time fit: About 8 weeks, which leaves no slack in an 8-week budget
- reproducibility: Public data with fixed train/validation/test splits per language
- evaluation clarity: Splits exist
- low failure risk: Per-language preprocessing is the main risk
- Missing: compute_fit: No measured run time
- Missing: evaluation_clarity: Which baselines the dataset paper already reports
- Capped: novelty or replication value 3 -> 2 (closest prior work read at level 'abstract', not full text)

## Candidate datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [TextGCN benchmark data folder](https://github.com/yao8839836/text_gcn/tree/master/data) | Benchmark files used by TextGCN and reused by later work | not reported | not reported | not reported | reachable (HTTP 200) | Repository scripts (remove_words.py, build_graph.py) | Needed for O1, O2 and all reproductions; only reachability was checked | yes |
| [SetFit/20_newsgroups](https://huggingface.co/datasets/SetFit/20_newsgroups) | Topic classification (20 Newsgroups mirror) | 18846 rows | json | not reported | open | Tokenisation; bag-of-words or graph construction | Convenient mirror; confirm it matches the benchmark split before comparing with published numbers | yes |
| [RottenTomatoes - MR Movie Review Data](https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes) | Sentence-level sentiment (MR) | 10662 rows | parquet | unknown | open | Tokenisation | Short texts; splits may differ from the benchmark version | yes |
| [Ohsumed](https://huggingface.co/datasets/community-datasets/ohsumed) | Medical abstracts with subject headings | 348564 rows | parquet | cc-by-nc-4.0 | open | Subset selection and single-label filtering would be needed | Much larger than a typical benchmark subset and multi-label; not a drop-in replacement | yes |
| [masakhanews](https://huggingface.co/datasets/masakhane/masakhanews) | News topic classification in African languages | 31088 rows | csv | afl-3.0 | open | Per-language tokenisation; graph construction | Core dataset for O3; fixed splits per language | yes |

## Recommendation

Start with opportunity 1, and begin by obtaining and reading ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)): if it already compares newer graph models with a bag-of-words MLP, fall back to a plain multi-seed reproduction of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)), which is the most practical reproduction candidate found. Opportunity 3 is the more original direction but uses the whole 8-week budget.

## Limitations of this report

- Paper summaries rest on abstracts; no full text was read, so limitations stated only in the body of a paper are missing.
- Semantic Scholar search and, late in the session, OpenAlex were unavailable without API keys; coverage is narrower than it could be.
- Novelty checks match wording, not meaning. Every novelty statement here is an unverified hypothesis.
- No code was run and no dataset was downloaded. Time and hardware figures are estimates.

## References

1. Hassan I. Abdalla, Ali A. Amer, Sri Devi Ravana (2023). *BoW-based neural networks vs. cutting-edge models for single-label text classification*. Neural Computing and Applications. https://doi.org/10.1007/s00521-023-08754-z
2. Gregor Donabauer, Udo Kruschwitz (2025). *Token-Level Graphs for Short Text Classification*. Lecture Notes in Computer Science Advances in Information Retrieval. https://doi.org/10.1007/978-3-031-88714-7_42
3. Lukas Galke, Ansgar Scherp (2022). *Bag-of-Words vs. Graph vs. Sequence in Text Classification: Questioning the Necessity of Text-Graphs and the Surprising Strength of a Wide MLP*. Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). https://doi.org/10.18653/v1/2022.acl-long.279
4. Samujjwal Ghosh, Subhadeep Maji, Maunendra Sankar Desarkar (2022). *GNoM: Graph Neural Network Enhanced Language Models for Disaster Related Multilingual Text Classification*. 14th ACM Web Science Conference 2022. https://doi.org/10.1145/3501247.3531561
5. Syed Tarif Abbas Rizvi, Ramsha Imran, Arif Mahmood (2025). *Text Classification Using Graph Convolutional Networks: A Comprehensive Survey*. ACM Computing Surveys. https://doi.org/10.1145/3714456
6. Oleksandr Shchur, Maximilian Mumme, Aleksandar Bojchevski, Stephan Günnemann (2018). *Pitfalls of Graph Neural Network Evaluation*. arXiv. https://arxiv.org/abs/1811.05868
7. Kunze Wang, Yihao Ding, Soyeon Caren Han (2024). *Graph Neural Networks for Text Classification: A Survey*. Artificial Intelligence Review. https://doi.org/10.1007/s10462-024-10808-0
8. Liang Yao, Chengsheng Mao, Yuan Luo (2019). *Graph Convolutional Networks for Text Classification*. Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v33i01.33017370
9. Yufeng Zhang, Xueli Yu, Zeyu Cui, Shu Wu, Zhongzhen Wen, Liang Wang (2020). *Every Document Owns Its Structure: Inductive Text Classification via Graph Neural Networks*. Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.acl-main.31
