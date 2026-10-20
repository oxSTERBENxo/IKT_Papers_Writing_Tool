# Research Opportunities at the Intersection of NLP and Graph Neural Networks (2023-2026)

**Report type:** Research Opportunity Report  
**Generated:** 2026-10-17

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | Natural Language Processing combined with Graph Neural Networks | stated by user |
| experience | undergraduate, comfortable with Python | default (not stated by user) |
| hardware | one consumer GPU with 8 GB VRAM (or a free cloud notebook) | default (not stated by user) |
| gpu vram gb | 8 | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| language | Python | default (not stated by user) |
| difficulty | moderate | default (not stated by user) |
| mode | any (reproduction, replication, extension or original) | stated by user |

## Summary

NLP combined with GNNs has become mostly a question of how large language models and graph learning work together on text-attributed graphs (TAGs), where every node carries text ([Jin et al. 2024](https://doi.org/10.1109/tkde.2024.3469578); [Wu et al. 2023](https://doi.org/10.1561/2200000096)). Benchmarks now exist for supervised and zero-shot comparison ([Li et al. 2024](https://doi.org/10.52202/079017-1340); [Wu et al. 2025](https://arxiv.org/abs/2502.00829)), and graph methods for classic NLP tasks such as aspect-based sentiment analysis (ABSA) and fake news detection already have surveys or large literatures ([Phan et al. 2023](https://doi.org/10.1016/j.asoc.2023.110235); [Gong et al. 2023](https://doi.org/10.21203/rs.3.rs-3252100/v1)). Eight candidate questions were drafted. Each was attacked with a novelty search and the closest papers were read. Three were rejected because recent work already answers them (simple baselines on TAGs, LLMs on heterophilic TAGs, robustness of LLM-enhanced GNNs). Five survived, four of them only after revision, and all five are best framed as replications or extensions. None of them can be called new with more than low confidence.

## How the literature was searched

- **Sources that answered:** openalex, arxiv, crossref, huggingface, zenodo, github
- **Sources that failed or were skipped:** semantic_scholar (rate_limited: HTTP 429 on every search call (no API key)); openalex (keyless daily budget exhausted part-way through (HTTP 429 from the UPFD challenge onward)); github (unauthenticated quota (60/h) exhausted once; repository checks resumed after the reset)
- **Search strategies:** surveys, recent, limitations, keyword, foundational, reproducibility, citation exploration, novelty challenge (keyword, surveys, recent), full-text reading (WebFetch of arXiv HTML)
- **Date range:** 2023 onwards for mapping (2021 onwards for the ABSA and fake-news challenges)
- **Records retrieved / after deduplication:** 1202 / 442
- **Search date:** 2026-10-17
- **Queries:** `graph neural networks natural language processing`; `large language models graph neural networks text`; `text-attributed graphs language models`; `benchmark text-attributed graph node classification language model embeddings GNN`; `are graph neural networks necessary text-attributed graphs simple baselines`; `LLM explanations as features node classification TAPE`; `dependency graph neural network aspect-based sentiment analysis`; `graph neural network fake news detection propagation`; `document-level relation extraction graph neural network`; `graph neural network retrieval augmented generation knowledge graph question answering`; `graph neural network text classification inductive`
- n_retrieved and n_after_dedup add up three separate searches; deduplication was per search, so some papers are counted more than once.
- Semantic Scholar answered some single-paper lookups and one citation listing but no search request.
- OpenAlex ran out of keyless budget during the session; later challenges used arXiv, Crossref and Hugging Face only, and 'existing reproduction attempts' could not be checked for any paper.
- Full text was read (via arXiv HTML) for LLMNodeBed, Chen et al. 2024 and GNN-RAG, and READMEs for TAPE, GNN-FakeNews, LLM-Structured-Data and LLMNodeBed. Everything else rests on abstracts or titles and is labelled that way in the paper notes.
- The challenge tool's wording-overlap signal said 'no close match' for the heterophily, robustness and simple-baselines ideas, but reading the retrieved papers showed close or identical prior work. Those ideas were rejected on that reading, not on the signal.

## What has already been done

| Paper | Published | Method | Datasets | Findings | Stated limitations | Link |
| --- | --- | --- | --- | --- | --- | --- |
| Graph Neural Networks for Natural Language Processing: A Survey (Wu et al. 2023) | 2023-01-25 | Survey of GNNs for NLP | not reported | Organises GNN-for-NLP work by graph construction, representation learning and encoder-decoder models (abstract not retrieved; title and venue only) | not reported | [link](https://doi.org/10.1561/2200000096) |
| Large Language Models on Graphs: A Comprehensive Survey (Jin et al. 2024) | 2024-12 | Survey: LLMs on pure, text-attributed and text-paired graphs; LLM as predictor, encoder, aligner | Summarises open-source code and benchmark datasets | States that whether LLM text reasoning generalises to graphs is underexplored (abstract) | not reported | [link](https://doi.org/10.1109/tkde.2024.3469578) |
| Fake news detection: A survey of graph neural network methods (Phan et al. 2023) | 2023-03-23 | Survey of GNN methods for fake news detection | not reported | Abstract not read; cited as evidence that the area is surveyed | not reported | [link](https://doi.org/10.1016/j.asoc.2023.110235) |
| Fake News Detection Through Graph-based Neural Networks: A Survey (Gong et al. 2023) | 2023-08-16 | Survey: knowledge-driven, propagation-based and heterogeneous social-context graph methods for fake news detection | not reported | Discusses challenges and open problems of graph-based fake news detection (abstract) | not reported | [link](https://doi.org/10.21203/rs.3.rs-3252100/v1) |
| Harnessing Explanations: LLM-to-LM Interpreter for Enhanced Text-Attributed Graph Representation Learning (He et al. 2023) | 2023-05-31 | TAPE: prompt an LLM (the repository distributes 'GPT responses'; exact model version not checked) for zero-shot predictions plus explanations; an LM interprets them into node features for a GNN | Cora, PubMed, ogbn-arxiv, tape-arxiv23 (repository calls it arxiv_2023) | State-of-the-art on these TAG datasets and 2.88x faster training than the closest baseline on ogbn-arxiv (abstract) | Repository LM example uses 4 GPUs; environment pinned to PyTorch 1.12.1 / CUDA 11.3; precomputed GPT responses are provided for download (README, read 2026-10-17) | [link](https://arxiv.org/abs/2305.19523) |
| STAGE: Simplified Text-Attributed Graph Embeddings Using Pre-trained LLMs (Lucas et al. 2024) | 2024 | STAGE: use pre-trained LLMs only as embedding generators for node text, then ensemble GNNs | Node classification benchmarks (not named in abstract) | Competitive results with a simpler pipeline than multi-stage prompting methods (abstract) | not reported | [link](https://doi.org/10.18653/v1/2024.kallm-1.10) |
| Exploring the Potential of Large Language Models (LLMs) in Learning on Graphs (Chen et al. 2024) | 2024-03-26 | Systematic study of LLMs-as-Enhancers and LLMs-as-Predictors for node classification | Cora, PubMed, ogbn-arxiv, ogbn-products and others | Section 7.1 Finding 3 (full text): a potential test data leakage problem on ogbn-arxiv; LLM-as-predictor evaluation used 200 sampled test nodes because of API cost | Section 7.2/7.3 (full text): querying LLM APIs at least N times for N nodes makes large graphs costly; test data may appear in LLM training corpora | [link](https://doi.org/10.1145/3655103.3655110) |
| Can LLMs Effectively Leverage Graph Structural Information through Prompts, and Why? (Huang et al. 2023) | 2023-09-28 | Curates a leakage-free dataset (arxiv-2023, test nodes are 2023 arXiv CS papers) and compares LLM prompting with and without structure | arxiv-2023 (33,868 nodes, 305,672 edges, per repository README), ogbn-arxiv, Cora, PubMed | No substantial evidence that LLM performance is due to data leakage; LLMs read neighbourhood prompts as context paragraphs; label-relevant phrases help most (abstract) | Repository template targets ChatGPT through the OpenAI API only; no licence stated (README) | [link](https://arxiv.org/abs/2309.16595) |
| GLBench: A Comprehensive Benchmark for Graph with Large Language Models (Li et al. 2024) | 2024 | GLBench: benchmark of GraphLLM methods vs GNN baselines with consistent splits, supervised and zero-shot | Collection of real-world TAG datasets | LLM-as-enhancer methods most robust; LLM-as-predictor less effective; no clear scaling law; a simple zero-shot baseline beats several tailored models (abstract) | not reported | [link](https://doi.org/10.52202/079017-1340) |
| When Do LLMs Help With Node Classification? A Comprehensive Analysis (Wu et al. 2025) | 2025-02-02 | LLMNodeBed: codebase and testbed, 8 LLM-based algorithms incl. TAPE, 8 classic baselines, 3 learning paradigms, >2,700 models | 10 homophilic + 4 heterophilic TAGs (Cora, Citeseer, Pubmed, arXiv, WikiCS, Instagram, Reddit, Books, Photo, Computer, Cornell, Texas, Wisconsin, Washington) | LLM methods help clearly in semi-supervised settings, marginally in supervised ones (abstract). Full text: TAPE uses Mistral-7B by default; replacing it with GPT-4o helps by up to 4% on Pubmed semi-supervised and the gap narrows with supervision; TAPE took 5.9 h on Pubmed on one H100-80G | Conclusion (full text): limited exploration of LLMs on heterophilic graphs and scarcity of text-rich heterophilic datasets. No discussion of training-data leakage found in the full text | [link](https://arxiv.org/abs/2502.00829) |
| Classic GNNs are Strong Baselines: Reassessing GNNs for Node Classification (Luo et al. 2024) | 2024 | Re-tunes GCN, GAT, GraphSAGE against graph transformers on 18 datasets | 18 node classification datasets | Classic GNNs with light tuning match or beat graph transformers on 17 of 18 datasets (abstract) | not reported | [link](https://doi.org/10.52202/079017-3098) |
| Does syntax matter? A strong baseline for Aspect-based Sentiment Analysis with RoBERTa (Dai et al. 2021) | 2021 | Compares parser trees with trees induced from fine-tuned RoBERTa inside ABSA graph models (ASGCN, PWCN, RGAT); plain RoBERTa baseline | Six ABSA datasets in four languages | FT-RoBERTa induced trees beat parser trees; a pure RoBERTa model outperforms or approximates previous SOTA (abstract) | Official repository has no licence and no seed control was found by the automated check; last push 2023-03-08 | [link](https://doi.org/10.18653/v1/2021.naacl-main.146) |
| Syntax-Enhanced Pretrained Language Models for Aspect-Level Sentiment Classification (Li et al. 2024) | 2024-12-24 | SE-BERT: syntax-enhanced transformer layers replacing BERT's final layers | not reported | Abstract states that existing methods improve aspect-level sentiment classification by adding syntactic GCN layers on BERT | not reported | [link](https://doi.org/10.1109/tcss.2024.3514901) |
| On the Robustness of Aspect-based Sentiment Analysis: Rethinking Model, Data, and Training (Fei et al. 2022) | 2022-12-21 | Universal-syntax GCN plus synthetic data and adversarial/contrastive training for ABSA robustness | not reported | Strong in-house ABSA models generalise poorly to challenging contexts (abstract) | not reported | [link](https://doi.org/10.1145/3564281) |
| User Preference-aware Fake News Detection (Dou et al. 2021) | 2021-07-11 | UPFD: joint news content and user-engagement graph modelling with GNNs | UPFD PolitiFact (314 graphs, 157 fake) and GossipCop (5,464 graphs, 2,732 fake), per repository README | Releases code and data as a benchmark for GNN-based fake news detection (abstract) | README states no run count, split or seed; repository licence Apache-2.0 | [link](https://doi.org/10.1145/3404835.3462990) |
| Revisiting Fake News Detection: Towards Temporality-aware Evaluation by Leveraging Engagement Earliness (Kim et al. 2025) | 2025-02-26 | Temporality-aware evaluation of social-graph fake news detection; DAWN edge reweighting by engagement earliness | not reported | Conventional methods lose discriminative power sharply when trained only on data available up to a point in time (abstract) | not reported | [link](https://doi.org/10.1145/3701551.3703524) |
| Less is More: Unseen Domain Fake News Detection via Causal Propagation Substructures (Gong et al. 2024) | 2024-11-14 | CSDA: causal propagation substructures for out-of-domain fake news detection | Public social media datasets | 7-16% accuracy improvement on OOD fake news (abstract) | not reported | [link](https://arxiv.org/abs/2411.09389) |
| GNN-RAG: Graph Neural Retrieval for Large Language Model Reasoning (Mavromatis & Karypis 2024) | 2024-05-30 | GNN-RAG: a GNN (ReaRev) retrieves answer candidates from a KG subgraph; shortest paths are verbalised for an LLM reader | WebQSP, CWQ | Full text: tuned LLaMA2-Chat-7B reader reaches WebQSP Hit 85.7 / F1 71.3; Table 5 shows retrieval also lifts Flan-T5-xl (WebQSP Hit 31.0 to 74.5) | Full text: assumes the KG subgraph contains the answer nodes; entity-linking errors and disconnected KG parts give empty paths. GNN runs used an RTX-3090 with 128 GB RAM; LLM runs used 4 A100 GPUs | [link](https://arxiv.org/abs/2405.20139) |
| RPO-RAG: Aligning Small LLMs with Relation-aware Preference Optimization for Knowledge Graph Question Answering (Um et al. 2026) | 2026-01-27 | RPO-RAG: relation-aware preference optimisation and answer-centred prompts for small-LLM KG RAG | not reported | States prior KG-RAG work relies on large LLMs or backbones above 7B, leaving sub-7B models underexplored (abstract) | not reported | [link](https://arxiv.org/abs/2601.19225) |
| HeTGB: A Comprehensive Benchmark for Heterophilic Text-Attributed Graphs (Li et al. 2025) | 2025-03-05 | HeTGB: benchmark of five heterophilic text-attributed graphs evaluating GNNs, PLMs and co-training | Five heterophilic TAGs | Shows utility of text in heterophilic graphs and limits of existing models (abstract) | not reported | [link](https://arxiv.org/abs/2503.04822) |
| Exploring the Potential of Large Language Models for Heterophilic Graphs (Wu et al. 2024) | 2024-08-26 | LLM-enhanced edge discriminator and edge reweighting for heterophilic graphs, with distillation to smaller models | not reported | LLMs can improve node classification on heterophilic graphs (abstract) | not reported | [link](https://arxiv.org/abs/2408.14134) |
| A critical look at the evaluation of GNNs under heterophily: Are we really making progress? (Platonov et al. 2023) | 2023-02-22 | Critique of heterophily benchmarks; new heterophilous datasets | Squirrel, Chameleon (critiqued) and new datasets | Duplicate nodes cause train-test leakage; standard GNNs usually beat specialised models on the new datasets (abstract) | not reported | [link](https://arxiv.org/abs/2302.11640) |
| Intruding with Words: Towards Understanding Graph Injection Attacks at the Text Level (Lei et al. 2024) | 2024-05-26 | Text-level graph injection attacks | not reported | Title and abstract record retrieved; studied as closest work for the robustness candidate | not reported | [link](https://arxiv.org/abs/2405.16405) |
| Are LLM-Enhanced Graph Neural Networks Robust Against Poisoning Attacks? (Ma et al. 2026) | 2026-05-18 | Poisoning attacks on LLM-enhanced GNNs (IEEE S&P 2026) | not reported | Title-level match for the robustness candidate | not reported | [link](https://doi.org/10.1109/sp63933.2026.00212) |
| Unveiling the Vulnerability of Graph-LLMs: An Interpretable Multi-Dimensional Adversarial Attack on TAGs (Fan et al. 2026) | 2026-04-12 | Interpretable multi-dimensional adversarial attack on TAGs (WWW 2026) | not reported | Title-level match for the robustness candidate | not reported | [link](https://doi.org/10.1145/3774904.3792284) |
| Robustness in Text-Attributed Graph Learning: Insights, Trade-offs, and New Defenses (Lei et al. 2025) | 2025-10-20 | Unified robustness evaluation of GNNs, robust GNNs and GraphLLMs under text, structure and hybrid perturbations; SFT-auto defence | Ten datasets from four domains | Text-structure robustness trade-offs; GNN robustness depends on the text encoder; GraphLLMs vulnerable to training-data corruption (abstract) | not reported | [link](https://arxiv.org/abs/2510.17185) |
| RDGCN: Reinforced Dependency Graph Convolutional Network for Aspect-based Sentiment Analysis (Zhao et al. 2023) | 2023-11-08 | RDGCN: reinforced dependency GCN for ABSA | not reported | Example of continued dependency-GCN ABSA work after 2021 | not reported | [link](https://arxiv.org/abs/2311.04467) |
| Multi-View Attention Syntactic Enhanced Graph Convolutional Network for Aspect-based Sentiment Analysis (Huang et al. 2025) | 2025-01-27 | Multi-view attention syntactic enhanced GCN for ABSA | not reported | Example of continued dependency-GCN ABSA work after 2021 | not reported | [link](https://arxiv.org/abs/2501.15968) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

### Directions that are already well explored

- [V] Comparing LLM-enhanced and LLM-as-predictor methods against classic GNNs under fixed protocols: two benchmarks with released code report that gains are marginal in supervised settings ([Li et al. 2024](https://doi.org/10.52202/079017-1340); [Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- [V] Re-tuning classic GNNs as strong baselines for node classification ([Luo et al. 2024](https://doi.org/10.52202/079017-3098))
- [V] Embedding node text with LLMs and training GNNs on top (TAPE, STAGE and many 2024-2026 variants) ([He et al. 2023](https://arxiv.org/abs/2305.19523); [Lucas et al. 2024](https://doi.org/10.18653/v1/2024.kallm-1.10))
- [V] LLMs on heterophilic text-attributed graphs, including a dedicated benchmark ([Li et al. 2025](https://arxiv.org/abs/2503.04822); [Wu et al. 2024](https://arxiv.org/abs/2408.14134); [Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- [V] Adversarial robustness of GNNs and GraphLLMs to text- and structure-level perturbations on TAGs ([Lei et al. 2024](https://arxiv.org/abs/2405.16405); [Lei et al. 2025](https://arxiv.org/abs/2510.17185); [Ma et al. 2026](https://doi.org/10.1109/sp63933.2026.00212); [Fan et al. 2026](https://doi.org/10.1145/3774904.3792284))
- [V] New dependency-graph GCN architectures for aspect-based sentiment analysis (dozens of 2023-2026 papers in this search alone) ([Zhao et al. 2023](https://arxiv.org/abs/2311.04467); [Huang et al. 2025](https://arxiv.org/abs/2501.15968); [Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901))
- [V] Graph-based fake news detection architectures over propagation graphs, including out-of-domain variants ([Phan et al. 2023](https://doi.org/10.1016/j.asoc.2023.110235); [Gong et al. 2023](https://doi.org/10.21203/rs.3.rs-3252100/v1); [Gong et al. 2024](https://arxiv.org/abs/2411.09389))

## Ranked research opportunities

Each opportunity below survived an explicit search for work that already addresses it. None is claimed to be novel: the novelty confidence states how far the search supports the gap, and what it could have missed.

### 1. Does the propagation graph help? Multi-seed re-evaluation of UPFD fake news detection against a no-graph baseline
**Type of gap:** Limitation reported in prior work  
**Recommended mode:** replication  
**Revised:** Originally framed as a general critique of graph-based fake news evaluation. Following the citations of UPFD found Kim et al. 2025, which already shows that conventional evaluation leaks future information and that performance drops under temporal splits ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)). The idea was narrowed to a question that paper does not address in its abstract: graph versus no-graph under seed and split variance on UPFD's own features.

**Research question.** On UPFD PolitiFact (314 graphs) and GossipCop (5,464 graphs), how much accuracy and F1 do GNNs over user-engagement graphs add beyond a classifier on the news (root-node) features alone, and do the published rankings of GNN variants survive 10+ seeds and repeated random splits?

**Motivation.** UPFD is the standard GNN fake-news benchmark and is built into PyG ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)). Its PolitiFact split is very small, which makes single-run comparisons fragile, and a 2025 study shows that the usual evaluation protocol is unrealistic ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)).

**Supporting papers.** ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990); [Phan et al. 2023](https://doi.org/10.1016/j.asoc.2023.110235); [Gong et al. 2023](https://doi.org/10.21203/rs.3.rs-3252100/v1))

**Closest existing work.**
- ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)): Changes the evaluation to temporal splits and proposes a new model; according to its abstract it does not isolate the contribution of the graph against a no-graph baseline on UPFD's features.
- ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)): Original benchmark; the README does not state run count, seeds or splits, and lists no news-content-only baseline.

**Evidence for the gap.**
- [V] PolitiFact in UPFD has 314 graphs (157 fake); GossipCop has 5,464 (repository README) ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990))
- [V] The automated reproducibility check found no seed or determinism control and no training entry point in the official repository ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990))
- [V] Conventional social-graph fake news evaluation gives models access to future information; performance drops sharply under temporality-aware evaluation (abstract) ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524))
- [E] With 314 graphs, a test split of about 60-90 graphs can move accuracy by more than one point per misclassified graph, so differences between GNN variants may be inside seed variance

**Potential contribution.** A variance-aware re-evaluation with a no-graph control, reported with confidence intervals; either outcome (graph helps or does not) is publishable as a short reproducibility paper or workshop contribution.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). Challenge searches ran without OpenAlex and Semantic Scholar. Papers citing UPFD were listed, but only titles and abstracts were screened. A reproducibility note on UPFD in a workshop or on GitHub issues could exist and would not be found by these sources.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `UPFD fake news detection reproducibility text-only baseline`; `propagation graph versus news content fake news detection ablation pretrained language model`; `do graph neural networks help fake news detection FakeNewsNet strong text baseline`; `GNN fake news detection evaluation variance small datasets PolitiFact`; `rethinking graph-based fake news detection benchmark`

**Feasibility.**
- [V] Data loads through torch_geometric.datasets.UPFD (documentation page reachable); repository licence Apache-2.0, last push 2025-12-11
- [E] Graphs average 58-131 nodes; training GCN/GAT/GraphSAGE runs on CPU or any GPU in minutes per seed
- [E] Raw news text is not in the PyG release (only BERT, spaCy, profile and content features); a modern text encoder would require re-collecting FakeNewsNet text, which depends on deleted tweets and may be impossible. The text-only baseline therefore uses the provided root-node BERT features.
- [S] Baselines: MLP or logistic regression on root-node features; GCN, GAT, GraphSAGE, UPFD-GNN with each feature type. Metrics: accuracy, macro-F1, mean and 95% CI over 10 seeds x 5 splits; paired comparison per split.

### 2. Does syntax still matter? Controlled multi-seed test of dependency-graph GCNs for ABSA with a fixed modern encoder
**Type of gap:** Unresolved contradiction between papers  
**Recommended mode:** replication

**Research question.** When the encoder (RoBERTa-base and DeBERTa-v3-base) and training budget are held fixed, do dependency-tree GCN heads (ASGCN, RGAT) give a statistically reliable gain in accuracy and macro-F1 over the plain fine-tuned encoder on SemEval-2014 laptops and restaurants, across at least 5 seeds?

**Motivation.** Dai et al. found that a pure RoBERTa model matches or beats syntax-aware models and that induced trees beat parser trees ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)), yet papers from 2023-2026 continue to propose dependency-GCN heads and report gains ([Zhao et al. 2023](https://arxiv.org/abs/2311.04467); [Huang et al. 2025](https://arxiv.org/abs/2501.15968); [Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901)).

**Supporting papers.** ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901); [Zhao et al. 2023](https://arxiv.org/abs/2311.04467); [Huang et al. 2025](https://arxiv.org/abs/2501.15968))

**Closest existing work.**
- ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)): Uses 2021-era RoBERTa and compares tree sources; its abstract does not report multi-seed significance testing, and it predates DeBERTa-v3 and the 2023-2026 GCN variants.
- ([Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901)): Proposes a new syntax-integrated model rather than testing whether syntax adds anything under a fixed encoder.
- ([Fei et al. 2022](https://doi.org/10.1145/3564281)): Studies robustness with a universal-syntax GCN and data augmentation, not the controlled syntax-versus-no-syntax question.

**Evidence for the gap.**
- [V] A pure RoBERTa model outperforms or approximates previous SOTA on six datasets in four languages (abstract) ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146))
- [V] A 2024 paper still states that existing methods improve aspect-level sentiment classification by adding a syntactic GCN layer on BERT (abstract) ([Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901))
- [V] The 2023-2026 search returned many new dependency-GCN ABSA models; none of the closest 15 challenge results is a controlled re-test ([Zhao et al. 2023](https://arxiv.org/abs/2311.04467); [Huang et al. 2025](https://arxiv.org/abs/2501.15968))
- [S] Reported gains between ABSA models are often around one point on test sets of 600-1,100 aspects, which may be within seed variance

**Potential contribution.** Evidence on whether a widely used design choice still matters for modern encoders, with a reusable multi-seed protocol. A null result (syntax does not help) is as reportable as a positive one.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The challenge tool warned that only one retrieved paper was loosely related, so the queries may have missed the literature. The 25 citing works of Dai et al. visible through Semantic Scholar were screened by title only. A replication inside a larger ABSA survey or a 2024-2026 workshop paper could exist.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `does syntax matter aspect-based sentiment analysis pretrained language model`; `dependency graph convolutional network aspect sentiment ablation without syntax RoBERTa`; `syntactic information unnecessary aspect sentiment classification strong baseline`; `reproducibility aspect-based sentiment graph neural network variance seeds`; `induced trees versus parser trees aspect sentiment DeBERTa`

**Feasibility.**
- [V] Official code (ASGCN, PWCN, RGAT folders with train and infer scripts): github.com/ROGERDJQ/RoBERTaABSA, linked by the paper; no licence; last push 2023-03-08
- [V] SemEval-2014 restaurant (3,693 train / 1,134 test rows) and laptop (2,358 / 654) data on Hugging Face, not gated, licence not stated
- [E] Base-size encoders on about 4,000 sentences fit 8 GB at batch 16 and sequence length 128; about 2 datasets x 2 encoders x 3 heads x 5 seeds = 60 short runs
- [E] The 2021 code likely needs porting to current transformers versions and a dependency parser (e.g. spaCy or Stanza)
- [S] Baselines: plain encoder + linear head; ASGCN and RGAT with parser trees; same with FT-RoBERTa induced trees. Metrics: accuracy and macro-F1; paired bootstrap or Wilcoxon over seeds.

### 3. TAPE on a student budget: explanation features from open LLMs that fit in 8 GB versus plain embeddings from the same model
**Type of gap:** Limitation reported in prior work  
**Recommended mode:** extension  
**Revised:** Originally 'TAPE with open LLMs instead of GPT'. Reading LLMNodeBed's full text showed it already runs TAPE with Mistral-7B by default and compares it with GPT-4o, recommending open models ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)). The idea was narrowed to models of about 4B parameters or fewer that run quantised on 8 GB, and to the comparison LLMNodeBed does not make: explanations versus embeddings from the same small model at matched compute.

**Research question.** On Cora and PubMed, how much of TAPE's improvement over a GNN on LM embeddings remains when explanations come from open LLMs of 4B parameters or fewer run quantised on 8 GB, and does that beat using the same LLM's embeddings directly (STAGE-style) for the same GPU time?

**Motivation.** The main barrier to LLM-enhanced graph learning for students is cost: Chen et al. name the cost of querying an LLM once per node as a limitation ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110)), and TAPE took 5.9 hours on PubMed on an H100 in LLMNodeBed ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)). STAGE suggests embeddings alone may be enough ([Lucas et al. 2024](https://doi.org/10.18653/v1/2024.kallm-1.10)).

**Supporting papers.** ([He et al. 2023](https://arxiv.org/abs/2305.19523); [Chen et al. 2024](https://doi.org/10.1145/3655103.3655110); [Lucas et al. 2024](https://doi.org/10.18653/v1/2024.kallm-1.10); [Wu et al. 2025](https://arxiv.org/abs/2502.00829))

**Closest existing work.**
- ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)): Compares Mistral-7B with GPT-4o as TAPE explainer on an H100; no models of 4B or less as explainers, and the size sweep (Qwen 3B-32B) applies to LLaGA, not TAPE (full text).
- ([Lucas et al. 2024](https://doi.org/10.18653/v1/2024.kallm-1.10)): Uses LLM embeddings only; does not compare against explanation features from the same model at matched cost (abstract).
- ([He et al. 2023](https://arxiv.org/abs/2305.19523)): Original method with API-based GPT explanations.

**Evidence for the gap.**
- [V] LLM API cost scales with the number of nodes and is a stated limitation (Sections 7.2-7.3, full text) ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110))
- [V] In LLMNodeBed TAPE took 5.9 h on PubMed on one H100-80G, against 13.4 min for a GCN on LLM embeddings (full text) ([Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- [V] GPT-4o over Mistral-7B helps TAPE by up to 4% in semi-supervised PubMed, and the gap narrows with supervision (full text) ([Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- [E] No paper testing TAPE-style explanations from models of 4B or less was found by the challenge searches

**Potential contribution.** A cost-accuracy curve for explanation features at the low end of model size, telling practitioners with small GPUs whether explanations are worth generating or whether embeddings suffice.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The challenge retrieved almost no closely related papers, so the wording probably missed some; only 22 citing works of TAPE were visible through OpenAlex. 2025-2026 efficiency papers on GraphLLMs could already include small explainers.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `TAPE explanations features open-source LLM Llama text-attributed graph`; `small language model LLM enhancer node classification cost accuracy trade-off`; `LLM-generated explanations node features smaller models text-attributed graphs`; `efficient LLM augmentation text-attributed graph without GPT`; `does LLM size matter enhancing node features graph neural network`

**Feasibility.**
- [V] TAPE code MIT licence, entry points core/trainGNN.py, trainLM.py, trainEnsemble.py, checkpoints and GPT responses downloadable; environment pinned to PyTorch 1.12.1 / CUDA 11.3; LM example uses 4 GPUs
- [V] LLMNodeBed (code: github.com/WxxShirley/LLMNodeBed, no licence found) implements TAPE, and its data is on Hugging Face (xxwu/LLMNodeBed, MIT, not gated)
- [E] A 1.5-4B model in 4-bit fits in 8 GB; generating about 100-token explanations for Cora (2,708 nodes) takes about an hour, PubMed (19,717 nodes) several hours
- [E] Fine-tuning the LM interpreter (DeBERTa-base in TAPE) on PubMed with one 8 GB GPU needs small batches or gradient accumulation; this is the main compute risk
- [S] Baselines: GCN/SAGE on shallow features, on sentence-encoder embeddings, on the small LLM's embeddings; TAPE with the provided GPT responses as the upper reference. Metric: accuracy, mean and std over 5 seeds, plus GPU-hours per method.

### 4. Has the leakage-free split expired? Re-testing LLM memorisation on citation-graph node classification with 2024-2026 open models
**Type of gap:** Unresolved contradiction between papers  
**Recommended mode:** replication  
**Revised:** Originally 'measure contamination with a post-cutoff split'. Following a citation from Chen et al. showed Huang et al. 2023 already built a leakage-free arxiv-2023 dataset and found no substantial evidence of leakage with ChatGPT ([Huang et al. 2023](https://arxiv.org/abs/2309.16595)). The idea became a replication with newer open models, whose training data now includes 2023 papers, plus a fresh post-cutoff split.

**Research question.** For open LLMs released in 2024-2026, is zero-shot node classification accuracy on papers published before the model's training cutoff higher than on matched papers published after it, once arXiv category distribution is controlled for?

**Motivation.** Chen et al. report a potential test-data leakage problem on ogbn-arxiv as a key finding ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110)), while Huang et al. find no substantial evidence of leakage ([Huang et al. 2023](https://arxiv.org/abs/2309.16595)). LLMNodeBed, the largest recent benchmark, does not discuss leakage ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)).

**Supporting papers.** ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110); [Huang et al. 2023](https://arxiv.org/abs/2309.16595); [Wu et al. 2025](https://arxiv.org/abs/2502.00829))

**Closest existing work.**
- ([Huang et al. 2023](https://arxiv.org/abs/2309.16595)): Tests ChatGPT (2023) only; its 2023 test papers predate the training cutoff of most 2024-2026 models, so its leakage-free property no longer holds for them (reasoned from dates).
- ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110)): Raises the concern and remarks on post-2023 papers, but reports no dedicated dataset or numbers (full text).

**Evidence for the gap.**
- [V] Chen et al., Section 7.1 Finding 3: 'a potential test data leakage problem on Ogbn-arxiv' (full text) ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110))
- [V] Huang et al.: 'no substantial evidence that the performance of LLMs is significantly attributed to data leakage' (abstract) ([Huang et al. 2023](https://arxiv.org/abs/2309.16595))
- [V] No discussion of training-data overlap or memorisation was found in LLMNodeBed's full text ([Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- [E] arxiv-2023 test papers (2023) are inside the training window of models released from 2024 on, so the original control is no longer leakage-free for them

**Potential contribution.** An updated, open-model answer to a disputed question, plus a refreshed post-cutoff split that others can reuse.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The challenge found only two loosely related papers, so the wording may have missed relevant work; general LLM contamination literature (outside graphs) was not searched in depth. Topic drift between years is a confound that may make any accuracy gap hard to attribute to memorisation.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `data leakage large language models node classification Cora arxiv memorization`; `test set contamination LLM graph benchmark text-attributed`; `temporal split papers after training cutoff LLM zero-shot classification citation graph`; `LLM memorization benchmark inflation graph learning evaluation`; `LLM-as-predictor node classification label leakage`

**Feasibility.**
- [V] arxiv-2023 (33,868 nodes, 305,672 edges) with raw text is in github.com/TRAIS-Lab/LLM-Structured-Data; no licence stated; template targets the OpenAI API only
- [E] A new post-cutoff split can be built from the arXiv API (which responded throughout this session) by sampling 2026 CS papers per category
- [E] Inference only: a 4-8B model in 4-bit on a few thousand nodes fits 8 GB in a few GPU-hours
- [V] Repository check found no environment file, no entry point and no seeds

### 5. When the subgraph has no answer: coverage failure analysis of GNN-RAG with a frozen small LLM reader
**Type of gap:** Limitation reported in prior work  
**Recommended mode:** extension  
**Revised:** Originally 'GNN-RAG with a small LLM'. The GNN-RAG full text already reports Flan-T5-xl as a reader (Table 5), and RPO-RAG targets sub-7B readers with training ([Um et al. 2026](https://arxiv.org/abs/2601.19225)). The idea was narrowed to the limitation GNN-RAG states itself: questions whose retrieved subgraph lacks the answer.

**Research question.** On WebQSP, what fraction of test questions have no answer entity in the GNN-retrieved subgraph, how does a frozen instruction-tuned LLM of 4B parameters or fewer perform on covered versus uncovered questions, and does falling back to no-retrieval answering when GNN confidence is low reduce errors?

**Motivation.** GNN-RAG states that it assumes the KG subgraph contains the answer nodes and that entity-linking errors break this ([Mavromatis & Karypis 2024](https://arxiv.org/abs/2405.20139)); RPO-RAG notes that sub-7B readers are underexplored in KG RAG ([Um et al. 2026](https://arxiv.org/abs/2601.19225)).

**Supporting papers.** ([Mavromatis & Karypis 2024](https://arxiv.org/abs/2405.20139); [Um et al. 2026](https://arxiv.org/abs/2601.19225))

**Closest existing work.**
- ([Mavromatis & Karypis 2024](https://arxiv.org/abs/2405.20139)): Reports aggregate Hit/F1 per reader; per the full text read, it gives no breakdown by subgraph answer coverage.
- ([Um et al. 2026](https://arxiv.org/abs/2601.19225)): Trains small readers with preference optimisation; does not analyse coverage failures (abstract).

**Evidence for the gap.**
- [V] GNN-RAG limitation: assumes the KG subgraph contains answer nodes; entity-linking errors and disconnected KG parts give empty paths (full text) ([Mavromatis & Karypis 2024](https://arxiv.org/abs/2405.20139))
- [V] Prior KG-RAG work relies on large LLMs or backbones above 7B (abstract) ([Um et al. 2026](https://arxiv.org/abs/2601.19225))

**Potential contribution.** A quantified error decomposition (retrieval miss vs reader error) and a cheap confidence-based fallback, useful for anyone deploying KG RAG with small models.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The challenge found only one loosely related paper; KGQA error analyses often appear inside method papers and would not be found by title or abstract wording.
Attempts to disprove novelty: 4 search(es); signal `no_close_match_in_this_search`. Queries: `GNN-RAG answer coverage retrieved subgraph missing answer knowledge graph question answering`; `knowledge graph question answering retrieval failure analysis subgraph recall WebQSP`; `error analysis entity linking subgraph retrieval KGQA large language model`; `graph neural network retriever small language model knowledge base question answering`

**Feasibility.**
- [V] Code: github.com/cmavro/GNN-RAG, no licence, last push 2024-06-12, 15 open issues, no seeds found; GNN entry point gnn/main.py and evaluation scripts present
- [V] WebQSP on Hugging Face (rmanluo/RoG-webqsp: 2,826 train / 246 validation / 1,628 test, not gated, licence not stated)
- [V] The paper's GNN experiments used an RTX-3090 with 128 GB RAM (full text); memory needs on a student machine are unknown and may block the project
- [E] Without a licence the code cannot safely be redistributed; using it for private research is a grey area to check with a supervisor

### Candidates rejected after the novelty challenge

- **Simple baselines versus LLM-enhanced methods on text-attributed graphs** (Already well studied): GLBench ([Li et al. 2024](https://doi.org/10.52202/079017-1340)) and LLMNodeBed ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)) compare GraphLLM methods with classic baselines under consistent protocols and report marginal gains in supervised settings; Luo et al. re-tune classic GNNs as strong baselines ([Luo et al. 2024](https://doi.org/10.52202/079017-3098)). The challenge signal said 'no close match', but reading these papers shows the question is answered.
- **LLM-derived features for GNNs on heterophilic text-attributed graphs** (Already well studied): Reading the challenge results found a dedicated benchmark of heterophilic TAGs ([Li et al. 2025](https://arxiv.org/abs/2503.04822)), an LLM-based method for heterophilic graphs ([Wu et al. 2024](https://arxiv.org/abs/2408.14134)), and LLMNodeBed's four heterophilic datasets ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)). The challenge tool's 'medium' ceiling rested on wording only.
- **Robustness of LLM-enhanced GNNs to text-level perturbations** (Already well studied): At least four close papers were retrieved and read at abstract or title level: text-level graph injection attacks ([Lei et al. 2024](https://arxiv.org/abs/2405.16405)), a unified robustness framework across ten datasets ([Lei et al. 2025](https://arxiv.org/abs/2510.17185)), poisoning attacks on LLM-enhanced GNNs ([Ma et al. 2026](https://doi.org/10.1109/sp63933.2026.00212)) and multi-dimensional attacks on TAGs ([Fan et al. 2026](https://doi.org/10.1145/3774904.3792284)).

## Feasibility ranking

Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any blocker removes a candidate from the ranking no matter how high its other scores are.

| Rank | Candidate | Status | Score % | Range | Scored weight % | Verified weight % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | UPFD fake news: multi-seed graph vs no-graph re-evaluation | VIABLE | 75.4 | 75.4-75.4 | 100.0 | 49.0 |
| 2 | ABSA: do dependency-graph GCNs help with a fixed modern encoder? | VIABLE | 73.2 | 73.2-73.2 | 100.0 | 42.0 |
| 3 | TAPE with explanation features from LLMs that fit in 8 GB | VIABLE | 71.0 | 71.0-71.0 | 100.0 | 49.0 |
| 4 | LLM memorisation on citation graphs: re-test with 2024-2026 open models | VIABLE | 59.6 | 59.6-59.6 | 100.0 | 30.0 |
| 5 | GNN-RAG answer-coverage failure analysis with a small frozen reader | VIABLE | 54.1 | 47.6-59.6 | 88.0 | 49.0 |

**Scores per criterion (0-5).**

| Criterion | Weight | O1 | O2 | O3 | O4 | O5 |
| --- | --- | --- | --- | --- | --- | --- |
| scientific relevance | 12 | 3 [V] | 4 [V] | 4 [V] | 4 [V] | 4 [V] |
| novelty or replication value | 12 | 3 [E] | 4 [E] | 3 [E] | 3 [E] | 3 [E] |
| paper and code availability | 10 | 4 [V] | 3 [V] | 4 [V] | 2 [V] | 2 [V] |
| dataset accessibility | 12 | 3 [V] | 3 [V] | 5 [V] | 3 [E] | 3 [V] |
| compute fit | 12 | 5 [E] | 4 [E] | 2 [E] | 4 [E] | unscored |
| implementation simplicity | 10 | 4 [E] | 3 [E] | 3 [E] | 3 [E] | 2 [E] |
| time fit | 10 | 5 [E] | 4 [E] | 3 [E] | 3 [E] | 2 [E] |
| reproducibility | 8 | 2 [V] | 2 [V] | 3 [V] | 1 [V] | 2 [V] |
| evaluation clarity | 7 | 4 [V] | 5 [E] | 5 [V] | 3 [E] | 4 [V] |
| low failure risk | 7 | 5 [E] | 5 [E] | 4 [E] | 3 [E] | 2 [E] |

**UPFD fake news: multi-seed graph vs no-graph re-evaluation**
- scientific relevance: Two surveys cover GNN fake news detection ([Phan et al. 2023](https://doi.org/10.1016/j.asoc.2023.110235); [Gong et al. 2023](https://doi.org/10.21203/rs.3.rs-3252100/v1)); A WSDM 2025 paper questions the standard evaluation protocol ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524))
- novelty or replication value: UPFD is widely used (cited 360 per Crossref/OpenAlex) and no seed control was found in its repository ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)); Temporal evaluation is already covered by ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)), so the remaining value is the graph vs no-graph control
- paper and code availability: github.com/safe-graph/GNN-FakeNews: Apache-2.0, last push 2025-12-11, requirements.txt, utils/eval_helper.py
- dataset accessibility: Loader in PyTorch Geometric (documentation page HTTP 200); sizes in README
- compute fit: Graphs average 58-131 nodes; GNNs this size train on CPU
- implementation simplicity: PyG ships an UPFD example; the project is mostly re-running with more seeds and a no-graph baseline
- time fit: About 4 weeks including write-up, leaving room for reruns
- reproducibility: Repository check: environment file found, seeds and hardware not found
- evaluation clarity: Accuracy and F1 are the standard metrics; evaluation helper in the repository
- low failure risk: Both outcomes (graph helps / does not) are reportable
- Missing: paper_and_code_availability: No training entry point detected by the automated check
- Missing: dataset_accessibility: Data licence not stated
- Missing: dataset_accessibility: Raw news text not included
- Missing: evaluation_clarity: Split protocol not stated in README

**ABSA: do dependency-graph GCNs help with a fixed modern encoder?**
- scientific relevance: Published claims conflict: ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) vs continued syntax-GCN papers ([Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901); [Zhao et al. 2023](https://arxiv.org/abs/2311.04467); [Huang et al. 2025](https://arxiv.org/abs/2501.15968)); Dai et al. cited 197 times
- novelty or replication value: Replication of a contested result; no controlled re-test found (novelty confidence low)
- paper and code availability: github.com/ROGERDJQ/RoBERTaABSA linked by the paper; ASGCN/PWCN/RGAT train and infer scripts; no licence; last push 2023-03-08
- dataset accessibility: SemEval-2014 restaurants and laptops on Hugging Face, not gated, under 200 KB each
- compute fit: Base-size encoders on about 4,000 sentences fit 8 GB
- implementation simplicity: Existing code, but 2021-era environment and a parser to set up; DeBERTa needs porting
- time fit: About 60 short fine-tuning runs plus porting fits 6 weeks
- reproducibility: Repository check: dependencies and configs found, seeds and hardware not found
- evaluation clarity: Accuracy and macro-F1 on SemEval-2014 with many published numbers to compare
- low failure risk: A null result answers the question as well as a positive one
- Missing: paper_and_code_availability: Licence
- Missing: dataset_accessibility: Licence on the dataset card
- Missing: dataset_accessibility: Equivalence with the split used by Dai et al.

**TAPE with explanation features from LLMs that fit in 8 GB**
- scientific relevance: LLM-on-graphs survey cited 154 times ([Jin et al. 2024](https://doi.org/10.1109/tkde.2024.3469578)); LLM query cost named as a limitation ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110))
- novelty or replication value: Partly covered by LLMNodeBed's Mistral-7B vs GPT-4o comparison ([Wu et al. 2025](https://arxiv.org/abs/2502.00829)); the 4B-and-under regime and the embedding comparison remain
- paper and code availability: github.com/XiaoxinHe/TAPE: MIT, entry points, checkpoints and GPT responses downloadable; LLMNodeBed code implements TAPE (no licence found)
- dataset accessibility: huggingface.co/datasets/xxwu/LLMNodeBed: MIT, not gated, includes Cora and PubMed text
- compute fit: Explanation generation with a 4-bit model under 4B fits; LM interpreter fine-tuning on PubMed is tight on 8 GB; TAPE took 5.9 h on PubMed on an H100 ([Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- implementation simplicity: Code exists; swapping the explainer and adding an embedding baseline is moderate adaptation; old PyTorch 1.12 environment
- time fit: Fits about 7 weeks with little slack if PubMed generation is slow
- reproducibility: Environment, entry points and checkpoints found; seeds and hardware not found
- evaluation clarity: Accuracy on Cora/PubMed with published TAPE and LLMNodeBed numbers
- low failure risk: A cost-accuracy curve is reportable whichever way it falls; the risk is not finishing PubMed
- Missing: compute_fit: Measured memory use of the interpreter step on 8 GB

**LLM memorisation on citation graphs: re-test with 2024-2026 open models**
- scientific relevance: Leakage raised as a key finding ([Chen et al. 2024](https://doi.org/10.1145/3655103.3655110)) and disputed ([Huang et al. 2023](https://arxiv.org/abs/2309.16595)); not discussed by the largest recent benchmark ([Wu et al. 2025](https://arxiv.org/abs/2502.00829))
- novelty or replication value: Replication of ([Huang et al. 2023](https://arxiv.org/abs/2309.16595)) with new models; topic drift is a confound
- paper and code availability: github.com/TRAIS-Lab/LLM-Structured-Data: data and an OpenAI-only template; no licence, no entry point, no environment file
- dataset accessibility: arxiv-2023 in the repository; ogbn-arxiv text via LLMNodeBed (MIT); New post-cutoff split must be built from the arXiv API
- compute fit: Inference only with a quantised 4-8B model
- implementation simplicity: Data collection, prompt pipeline and matched sampling must be written
- time fit: Building and checking a new split takes time; fits 7 weeks with little slack
- reproducibility: Repository check found no environment, seeds or entry point
- evaluation clarity: Accuracy is clear, but separating memorisation from topic drift needs a careful protocol
- low failure risk: A null result is reportable but may be hard to interpret because of confounds
- Missing: dataset_accessibility: Licence of arxiv-2023

**GNN-RAG answer-coverage failure analysis with a small frozen reader**
- scientific relevance: Limitation stated in GNN-RAG itself ([Mavromatis & Karypis 2024](https://arxiv.org/abs/2405.20139)); small readers named as underexplored ([Um et al. 2026](https://arxiv.org/abs/2601.19225))
- novelty or replication value: Error decomposition not found in abstracts; novelty confidence low
- paper and code availability: github.com/cmavro/GNN-RAG: no licence, last push 2024-06-12, 15 open issues
- dataset accessibility: rmanluo/RoG-webqsp and RoG-cwq on Hugging Face, not gated
- implementation simplicity: Two-stage pipeline (GNN + LLM) with separate requirements files; adding coverage logging and a fallback
- time fit: Setup risk of the pipeline uses most of 8 weeks
- reproducibility: Requirements and evaluation scripts found; seeds, hardware and checkpoints not found
- evaluation clarity: Hit, H@1 and F1 on WebQSP with published numbers (Hit 85.7 for the 7B reader)
- low failure risk: If the pipeline cannot be run, there is nothing to report
- Missing: dataset_accessibility: Licence
- Missing: dataset_accessibility: Size of the KG subgraph files
- Missing: compute_fit: Paper's GNN runs used 128 GB RAM; minimum RAM and VRAM for the GNN step are not stated
- Not scored for lack of evidence: compute_fit

## Candidate datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [UPFD (PolitiFact, GossipCop) via PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.datasets.UPFD.html) | O1 | PolitiFact 314 graphs / 41,054 nodes; GossipCop 5,464 graphs / 314,262 nodes (README); raw files about 1.2 GB | PyG InMemoryDataset | not reported | open (documentation page reachable; download through the PyG loader) | Choose a feature type (bert, spacy, profile, content) | Small and CPU-friendly; licence of the data is not stated, only of the code (Apache-2.0) | yes |
| [SemEval-2014 ABSA restaurants (SetFit copy)](https://huggingface.co/datasets/tomaarsen/setfit-absa-semeval-restaurants) | O2 | 3,693 train / 1,134 test rows | parquet | not reported | open, not gated | Check against the split shipped with the RoBERTaABSA repository before comparing with published numbers; this copy may be restructured for SetFit | Small, fast to fine-tune; licence must be read from the card | yes |
| [SemEval-2014 ABSA laptops (SetFit copy)](https://huggingface.co/datasets/tomaarsen/setfit-absa-semeval-laptops) | O2 | 2,358 train / 654 test rows | parquet | not reported | open, not gated | As above; the RoBERTaABSA repository also ships its own preprocessing | Small; licence must be read from the card | yes |
| [LLMNodeBed datasets (Cora, PubMed, arXiv and 11 more TAGs)](https://huggingface.co/datasets/xxwu/LLMNodeBed) | O3 (and O4 for ogbn-arxiv text) | 857,129 rows in total | json | mit | open, not gated | Use LLMNodeBed loaders; download only the needed datasets | Raw node text with a clear licence | yes |
| [arxiv-2023 leakage-control dataset](https://github.com/TRAIS-Lab/LLM-Structured-Data) | O4 | 33,868 nodes, 305,672 edges (README) | PyG data with raw text in the repository | not reported | open (repository reachable) | load_data('arxiv_2023', use_text=True) per README | Reference control; no longer post-cutoff for 2024+ models | yes |
| [WebQSP (RoG release)](https://huggingface.co/datasets/rmanluo/RoG-webqsp) | O5 | 2,826 train / 246 validation / 1,628 test | parquet | not reported | open, not gated | Subgraphs as used by GNN-RAG; check against the repository's preprocessing scripts | Standard KGQA set; licence not stated | yes |
| [CWQ (RoG release)](https://huggingface.co/datasets/rmanluo/RoG-cwq) | O5 (optional second dataset) | 16,894 train / 3,519 validation / 3,531 test | parquet | not reported | open, not gated | not reported | Larger, harder multi-hop set | yes |

## Recommendation

For a student with one 8 GB GPU and about 8 weeks, the three most suitable opportunities are: (1) a multi-seed re-evaluation of GNN fake news detection on UPFD against a no-graph baseline (cheapest, lowest risk, but modest publication potential); (2) a controlled test of whether dependency-graph GCNs still help ABSA once a modern encoder is held fixed (clearest scientific question, because published results disagree); (3) TAPE-style explanation features from small open LLMs that fit in 8 GB, compared with plain embeddings from the same model (closest to current TAG research, highest publication potential of the three, but tightest on compute and time). The score ranges of these three overlap, so the order is not decisive: pick by interest. Before committing to any of them, read the full text of the closest paper listed for it, because every novelty judgement here rests on a lexical search and mostly on abstracts. Opportunity 4 (LLM memorisation on citation graphs) is a good alternative if no GPU is available beyond inference. Opportunity 5 (GNN-RAG answer coverage) is not recommended under these constraints: the paper's GNN runs used 128 GB of RAM, and the code has no licence.

## Limitations of this report

- Novelty judgements rest on lexical searches of arXiv, Crossref, Hugging Face and (until it ran out) OpenAlex. Semantic Scholar search failed throughout. 'Not found' means not found in these sources with these queries.
- Most paper summaries come from abstracts. Full text was read only for LLMNodeBed, Chen et al. 2024 and GNN-RAG, and READMEs for four repositories.
- No code was executed and no dataset was downloaded. Every compute and time figure marked as an estimate is a projection, not a measurement.
- Existing reproduction attempts could not be checked for any paper because OpenAlex was rate-limited.
- Dataset licences are missing for five of the seven datasets; read each dataset card before use.
- Scores are assigned by the assistant from the evidence above; the tool only enforces that each score has evidence and that blockers are respected.

## References

1. Zhikai Chen, Haitao Mao, Hang Li, Wei Jin, Hongzhi Wen, Xiaochi Wei et al. (2024). *Exploring the Potential of Large Language Models (LLMs) in Learning on Graphs*. ACM SIGKDD Explorations Newsletter. https://doi.org/10.1145/3655103.3655110
2. Junqi Dai, Hang Yan, Tianxiang Sun, Peng-Fei Liu, Xipeng Qiu (2021). *Does syntax matter? A strong baseline for Aspect-based Sentiment Analysis with RoBERTa*. Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. https://doi.org/10.18653/v1/2021.naacl-main.146
3. Yingtong Dou, Kai Shu, Congyin Xia, Philip S. Yu, Li-Chao Sun (2021). *User Preference-aware Fake News Detection*. Proceedings of the 44th International ACM SIGIR Conference on Research and Development in Information Retrieval. https://doi.org/10.1145/3404835.3462990
4. Bo-Wen Fan, Zhilin Guo, Xun-Kai Li, Yihan Zhou, Bing Zhou, Zhenjun Li et al. (2026). *Unveiling the Vulnerability of Graph-LLMs: An Interpretable Multi-Dimensional Adversarial Attack on TAGs*. Proceedings of the ACM Web Conference 2026. https://doi.org/10.1145/3774904.3792284
5. Hao Fei, Tat-Seng Chua, Chenliang Li, Donghong Ji, Meishan Zhang, Yafeng Ren (2022). *On the Robustness of Aspect-based Sentiment Analysis: Rethinking Model, Data, and Training*. ACM Transactions on Information Systems. https://doi.org/10.1145/3564281
6. Shuzhi Gong, Richard O. Sinnott, Jianzhong Qi, Cecile Paris (2023). *Fake News Detection Through Graph-based Neural Networks: A Survey*. Research Square. https://doi.org/10.21203/rs.3.rs-3252100/v1
7. Shuzhi Gong, Richard O. Sinnott, Jianzhong Qi, Cecile Paris (2024). *Less is More: Unseen Domain Fake News Detection via Causal Propagation Substructures*. arXiv. https://arxiv.org/abs/2411.09389
8. Xiaoxin He, Xavier Bresson, Thomas Laurent, Adam Perold, Yann LeCun, Bryan Hooi (2023). *Harnessing Explanations: LLM-to-LM Interpreter for Enhanced Text-Attributed Graph Representation Learning*. arXiv. https://arxiv.org/abs/2305.19523
9. Jin Huang, Xingjian Zhang, Qiaozhu Mei, Jiaqi Ma (2023). *Can LLMs Effectively Leverage Graph Structural Information through Prompts, and Why?*. arXiv. https://arxiv.org/abs/2309.16595
10. Xiang Huang, Hao Peng, Shuo Sun, Zhifeng Hao, Hui Lin, Shuhai Wang (2025). *Multi-View Attention Syntactic Enhanced Graph Convolutional Network for Aspect-based Sentiment Analysis*. arXiv. https://arxiv.org/abs/2501.15968
11. Bowen Jin, Gang Liu, Chi Han, Meng Jiang, Heng Ji, Jiawei Han (2024). *Large Language Models on Graphs: A Comprehensive Survey*. IEEE Transactions on Knowledge and Data Engineering. https://doi.org/10.1109/tkde.2024.3469578
12. Junghoon Kim, Junmo Lee, Yeonjun In, Kanghoon Yoon, Chanyoung Park (2025). *Revisiting Fake News Detection: Towards Temporality-aware Evaluation by Leveraging Engagement Earliness*. Proceedings of the Eighteenth ACM International Conference on Web Search and Data Mining. https://doi.org/10.1145/3701551.3703524
13. Runlin Lei, Yuwei Hu, Yuchen Ren, Zhewei Wei (2024). *Intruding with Words: Towards Understanding Graph Injection Attacks at the Text Level*. arXiv. https://arxiv.org/abs/2405.16405
14. Runlin Lei, Lu Yi, Mingguo He, Pengyu Qiu, Zhewei Wei, Yongchao Liu et al. (2025). *Robustness in Text-Attributed Graph Learning: Insights, Trade-offs, and New Defenses*. arXiv. https://arxiv.org/abs/2510.17185
15. Yuhan Li, Peisong Wang, Xiao Zhu, Aochuan Chen, Haiyun Jiang, Deng Cai et al. (2024). *GLBench: A Comprehensive Benchmark for Graph with Large Language Models*. Advances in Neural Information Processing Systems 37. https://doi.org/10.52202/079017-1340
16. Yuan Li, Jin Wang, Lung‐Hao Lee, Xuejie Zhang (2024). *Syntax-Enhanced Pretrained Language Models for Aspect-Level Sentiment Classification*. IEEE Transactions on Computational Social Systems. https://doi.org/10.1109/tcss.2024.3514901
17. Shujie Li, Yuxia Wu, Yuan Fang, Chuan Shi (2025). *HeTGB: A Comprehensive Benchmark for Heterophilic Text-Attributed Graphs*. arXiv. https://arxiv.org/abs/2503.04822
18. Aaron Zolnai-Lucas, Jack Boylan, Chris Hokamp, Parsa Ghaffari (2024). *STAGE: Simplified Text-Attributed Graph Embeddings Using Pre-trained LLMs*. Proceedings of the 1st Workshop on Knowledge Graphs and Large Language Models (KaLLM 2024). https://doi.org/10.18653/v1/2024.kallm-1.10
19. Yuankai Luo, Lei Shi, Xiao-Ming Wu (2024). *Classic GNNs are Strong Baselines: Reassessing GNNs for Node Classification*. Advances in Neural Information Processing Systems 37. https://doi.org/10.52202/079017-3098
20. Yuhan Ma, Jie Wang, Zheng Yan (2026). *Are LLM-Enhanced Graph Neural Networks Robust Against Poisoning Attacks?*. 2026 IEEE Symposium on Security and Privacy (SP). https://doi.org/10.1109/sp63933.2026.00212
21. Costas Mavromatis, George Karypis (2024). *GNN-RAG: Graph Neural Retrieval for Large Language Model Reasoning*. arXiv. https://arxiv.org/abs/2405.20139
22. Huyen Trang Phan, Ngoc Thanh Nguyên, Dosam Hwang (2023). *Fake news detection: A survey of graph neural network methods*. Applied Soft Computing. https://doi.org/10.1016/j.asoc.2023.110235
23. Oleg Platonov, Denis Kuznedelev, Michael Diskin, Artem Babenko, Liudmila Prokhorenkova (2023). *A critical look at the evaluation of GNNs under heterophily: Are we really making progress?*. arXiv. https://arxiv.org/abs/2302.11640
24. Kaehyun Um, KyuHwan Yeom, Haerim Yang, Minyoung Choi, Hyeongjun Yang, Kyong-Ho Lee (2026). *RPO-RAG: Aligning Small LLMs with Relation-aware Preference Optimization for Knowledge Graph Question Answering*. arXiv. https://arxiv.org/abs/2601.19225
25. Lingfei Wu, Yu Chen, Kai Shen, Xiaojie Guo, Hanning Gao, Shucheng Li et al. (2023). *Graph Neural Networks for Natural Language Processing: A Survey*. Foundations and Trends® in Machine Learning. https://doi.org/10.1561/2200000096
26. Yuxia Wu, Shujie Li, Yuan Fang, Chuan Shi (2024). *Exploring the Potential of Large Language Models for Heterophilic Graphs*. arXiv. https://arxiv.org/abs/2408.14134
27. Xixi Wu, Yifei Shen, Fangzhou Ge, Caihua Shan, Yizhu Jiao, Xiangguo Sun et al. (2025). *When Do LLMs Help With Node Classification? A Comprehensive Analysis*. arXiv. https://arxiv.org/abs/2502.00829
28. Xusheng Zhao, Hao Peng, Qiong Dai, Xu Bai, Huailiang Peng, Yanbing Liu et al. (2023). *RDGCN: Reinforced Dependency Graph Convolutional Network for Aspect-based Sentiment Analysis*. arXiv. https://arxiv.org/abs/2311.04467
