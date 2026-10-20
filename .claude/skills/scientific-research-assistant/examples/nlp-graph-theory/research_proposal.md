# Is a Bag-of-Words MLP Still Competitive with Recent Text-Graph Classifiers? A Multi-Seed Replication and Extension

**Report type:** Research Proposal  
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

## Problem statement

Graph neural networks are widely used for text classification ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0); [Rizvi et al. 2025](https://doi.org/10.1145/3714456)). A 2022 study reported that a wide MLP on bag-of-words outperforms TextGCN and HeteGCN and is comparable with HyperGAT ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)). Graph-based methods published since then report gains over existing methods ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)). Whether the simple baseline still holds against them, and how stable the comparison is across random seeds, was not established by the literature retrieved for this proposal.

## Literature background

TextGCN builds one graph over words and documents and classifies documents with a GCN ([Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370)). Later work moved to other graph constructions, including graphs over language-model tokens ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)). Evaluation practice matters: for node classification, different data splits changed which GNN ranked best ([Shchur et al. 2018](https://arxiv.org/abs/1811.05868)). A closely related comparison exists whose abstract and full text could not be obtained ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)); it must be read before work starts.

| Paper | Published | Method | Datasets | Findings | Stated limitations | Read | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Graph Convolutional Networks for Text Classification (Yao et al. 2019) | 2019-07-17 | One corpus-level graph of words and documents (word co-occurrence and document-word edges); GCN on one-hot inputs (TextGCN) | Multiple benchmark datasets (not named in the abstract) | Reports outperforming the then state of the art without external embeddings; the margin grows as training data shrinks | not reported | not recorded | [link](https://doi.org/10.1609/aaai.v33i01.33017370) |
| Bag-of-Words vs. Graph vs. Sequence in Text Classification: Questioning the Necessity of Text-Graphs and the Surprising Strength of a Wide MLP (Galke & Scherp 2022) | 2022 | Wide MLP on bag-of-words; fine-tuned BERT and DistilBERT; compared with TextGCN, HeteGCN, HyperGAT | Not named in the abstract | BoW wide MLP outperforms TextGCN and HeteGCN in the inductive setting and is comparable with HyperGAT; fine-tuned BERT and DistilBERT outperform all | Abstract notes TextGCN needs an O(N^2) graph and Transformers O(L^2) attention; own limitations not stated in the abstract | not recorded | [link](https://doi.org/10.18653/v1/2022.acl-long.279) |
| Pitfalls of Graph Neural Network Evaluation (Shchur et al. 2018) | 2018-11-14 | Re-evaluation of four GNN models for node classification under varied data splits | Node-classification graphs (not text) | Different splits give dramatically different model rankings; simpler GNNs can beat complex ones under fair tuning | Concerns node classification, not text graphs | not recorded | [link](https://arxiv.org/abs/1811.05868) |
| Token-Level Graphs for Short Text Classification (Donabauer & Kruschwitz 2025) | 2025 | Text graphs built from pre-trained language model tokens and embeddings (TokenGraph) | Short-text datasets (not named in the abstract) | Reports higher or on-par scores versus existing methods with few training samples; code stated to be public | Abstract lists limits of earlier graph methods (word sense, transductive setting), not its own | not recorded | [link](https://doi.org/10.1007/978-3-031-88714-7_42) |
| Graph Neural Networks for Text Classification: A Survey (Wang et al. 2024) | 2024-07-01 | Survey of corpus-level and document-level GNNs for text classification up to 2023 | Summarises public benchmarks | Compares published performance, graph construction and evaluation practice; lists open issues | not reported | not recorded | [link](https://doi.org/10.1007/s10462-024-10808-0) |
| BoW-based neural networks vs. cutting-edge models for single-label text classification (Abdalla et al. 2023) | 2023-07-18 | Bag-of-words neural networks compared with recent models (from the title; abstract unavailable to the sources queried) | not reported | not reported | not reported | not recorded | [link](https://doi.org/10.1007/s00521-023-08754-z) |
| Text Classification Using Graph Convolutional Networks: A Comprehensive Survey (Rizvi et al. 2025) | 2025-01-21 | Survey of GCN-based text classification by architecture and supervision mode | Compares methods on benchmark datasets | Identifies strengths and limitations and future directions | not reported | not recorded | [link](https://doi.org/10.1145/3714456) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

## Research question

Under one evaluation protocol with five random seeds, does a wide MLP on bag-of-words reach the test accuracy of a text-graph classifier published after 2022 on short- and long-text benchmarks?

## Hypothesis

[S] On each benchmark, the mean test accuracy of the bag-of-words MLP is within one percentage point of the graph model, or higher.

**How the hypothesis can be supported or rejected.** Supported on a dataset if the 95% bootstrap confidence interval of the accuracy difference (graph minus MLP) lies below +1 point. Rejected if the interval lies entirely above +1 point. Inconclusive otherwise; the report then states the interval and stops there.

## Dataset

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [TextGCN benchmark data folder](https://github.com/yao8839836/text_gcn/tree/master/data) | Benchmark files used by TextGCN and reused by later work | not reported | not reported | not reported | reachable (HTTP 200) | Repository scripts (remove_words.py, build_graph.py) | Needed for O1, O2 and all reproductions; only reachability was checked | yes |
| [RottenTomatoes - MR Movie Review Data](https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes) | Sentence-level sentiment (MR) | 10662 rows | parquet | unknown | open | Tokenisation | Short texts; splits may differ from the benchmark version | yes |

The benchmark files distributed with the TextGCN repository, which the baseline study's README also points to. Only the folder's reachability was checked; file contents, sizes and licence must be confirmed on download. One verified short-text mirror is listed for a sanity check, but its splits may differ from the benchmark version, so it cannot be compared with published numbers.

## Methodology

**Project type.** Replication of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) (independent rerun with more seeds) followed by an extension (one newer graph model). No new model is proposed.

- Stage 1 (replication): run the public bag-of-words MLP code on the benchmark datasets with five seeds and compare with the numbers published in ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)).
- Stage 2 (extension): run one graph model published after 2022 with public code under the same splits, tuning budget and seeds.
- [V] TokenGraph is the planned graph model because its repository URL responds; whether the code runs was not checked. ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42))
- A logistic regression on TF-IDF features is added as the simplest reference point.

**Variables.**

Independent: model family (logistic regression, bag-of-words MLP, graph model) and random seed. Dependent: test accuracy and macro-F1, training time, peak memory. Controlled: data splits, preprocessing, vocabulary, hyperparameter search budget per model, hardware.

**Confounding factors and leakage controls.**

- Unequal tuning: give every model the same number of validation-set trials.
- Transductive graph models see test documents (without labels) during training; state for each model whether it is transductive or inductive and compare within the same setting where possible.
- Fit vocabulary and TF-IDF statistics on training data only; never tune on the test split.
- Pretrained language-model embeddings give the graph model external knowledge the bag-of-words model lacks; report this as a difference in resources, not only in architecture.

## Baselines

- Logistic regression on TF-IDF
- Wide MLP on bag-of-words (code of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)))
- Published numbers from ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)) for reference

## Evaluation metrics

- Test accuracy (confirm in the full texts that this is the measure the compared papers report)
- Macro-F1, in case classes are imbalanced
- Wall-clock training time and peak memory

## Experimental procedure

- Week 1: obtain and read ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)) and the full text of ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) and ([Donabauer & Kruschwitz 2025](https://doi.org/10.1007/978-3-031-88714-7_42)); stop and reframe if the comparison already exists.
- Week 2: set up both codebases with pinned environments; confirm the data files and their licence.
- Week 3: Stage 1 runs with five seeds; compare with published numbers.
- Weeks 4-5: Stage 2 runs under the shared protocol.
- Week 6: statistical analysis and write-up.

**Statistical analysis and uncertainty reporting.**

Report mean and standard deviation over five seeds for every model and dataset. Compare models with a paired bootstrap on test predictions (10,000 resamples) giving a 95% confidence interval for the accuracy difference. With several datasets, report every interval rather than selecting the favourable ones.

## Compute, time and feasibility

- [E] About six weeks of an eight-week budget
- [E] The MLP runs on CPU; the graph model needs a GPU for language-model embeddings and should fit in 8 GB for short texts
- [V] No hardware requirement is stated by either repository

## Expected contribution

[E] An independent, multi-seed check of a published result that questions a line of work, plus one updated comparison. Either outcome is informative.

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | verified: 7 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: not recorded: 7; claims: estimate: 4, speculative: 1, verified: 4 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | no opportunities | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## Limitations and risks

- [V] The comparison may already be published in ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z)) or elsewhere; novelty confidence is low. Fallback: report Stage 1 alone as a reproduction.
- [E] The graph model's code may not run or may exceed 8 GB. Fallback: a different post-2022 graph model with public code, or short-text datasets only.
- [V] Benchmark data licence is not stated by any API.

- Background summaries rest on abstracts; full texts were not read when this proposal was drafted.
- No code was run. Time and hardware figures are estimates.
- Semantic Scholar search was unavailable, so prior work may have been missed.

## References

1. Hassan I. Abdalla, Ali A. Amer, Sri Devi Ravana (2023). *BoW-based neural networks vs. cutting-edge models for single-label text classification*. Neural Computing and Applications. https://doi.org/10.1007/s00521-023-08754-z
2. Gregor Donabauer, Udo Kruschwitz (2025). *Token-Level Graphs for Short Text Classification*. Lecture Notes in Computer Science Advances in Information Retrieval. https://doi.org/10.1007/978-3-031-88714-7_42
3. Lukas Galke, Ansgar Scherp (2022). *Bag-of-Words vs. Graph vs. Sequence in Text Classification: Questioning the Necessity of Text-Graphs and the Surprising Strength of a Wide MLP*. Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). https://doi.org/10.18653/v1/2022.acl-long.279
4. Syed Tarif Abbas Rizvi, Ramsha Imran, Arif Mahmood (2025). *Text Classification Using Graph Convolutional Networks: A Comprehensive Survey*. ACM Computing Surveys. https://doi.org/10.1145/3714456
5. Oleksandr Shchur, Maximilian Mumme, Aleksandar Bojchevski, Stephan Günnemann (2018). *Pitfalls of Graph Neural Network Evaluation*. arXiv. https://arxiv.org/abs/1811.05868
6. Kunze Wang, Yihao Ding, Soyeon Caren Han (2024). *Graph Neural Networks for Text Classification: A Survey*. Artificial Intelligence Review. https://doi.org/10.1007/s10462-024-10808-0
7. Liang Yao, Chengsheng Mao, Yuan Luo (2019). *Graph Convolutional Networks for Text Classification*. Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v33i01.33017370
