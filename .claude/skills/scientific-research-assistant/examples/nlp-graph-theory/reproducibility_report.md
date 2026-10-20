# Reproduction Candidates in Graph-Based Text Classification

**Report type:** Reproducibility Report  
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

Four papers were assessed from metadata, repositories and READMEs. One is blocked because its full text could not be located. Of the other three, the bag-of-words study ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) has the best-specified environment; the two graph-model repositories lack dependency files, seeds and licences.

## Terms used

- **Reproduction:** obtaining the reported results with the original method, code and comparable conditions.
- **Replication:** testing whether the findings hold under an independent implementation or changed conditions.
- **Extension:** adding experiments, datasets, conditions or method changes beyond the original study.

No experiment in this report has been executed unless a candidate's result status says so and gives execution evidence.

## How candidates were found

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

## Candidate papers

### 1. Bag-of-Words vs. Graph vs. Sequence in Text Classification: Questioning the Necessity of Text-Graphs and the Surprising Strength of a Wide MLP ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))
**Mode:** reproduction  
**Result status:** assessed_only (NOT executed; nothing below is a reproduction result)  
**Code:** https://github.com/lgalke/text-clf-baselines (licence MIT, 29 stars, last push 2026-04-21, 0 open issues)

| Item | Status | Evidence / note |
| --- | --- | --- |
| Full paper publicly available | verified | https://arxiv.org/abs/2109.03777 |
| Implementation available | found | https://github.com/lgalke/text-clf-baselines |
| Code licence | verified | SPDX: MIT |
| Dependencies / environment specified | found | file: pyproject.toml; file: requirements.txt |
| Dataset access and preprocessing instructions | found | README: "...on datasets with long sequences.", } ``` ## Get up and running 1. Download the data folder from the [TextGCN repository](https:/ |
| Training configuration and hyperparameters | not_found | not reported |
| Training entry point | found | file: main.py; file: run_glue.py |
| Random seeds / determinism controls | not_found | not reported |
| Hardware requirements stated | not_found | not reported |
| Evaluation script or protocol | found | file: test_textgraph.py |
| Pretrained weights or checkpoints | not_found | not reported |
| Published results to compare against | not_found | not reported |
| Model architecture fully specified | manual_review | not reported |
| Repository maintenance | verified | last push 2026-04-21; archived: False |
| Existing reproduction attempts | manual_review | Token-Level Graphs for Short Text Classification (2025) https://doi.org/10.1007/978-3-031-88714-7_42 |

**Why reproducing it is valuable.** [E] The paper reports that a simple model beats or matches graph models; confirming that independently tells a student which baseline to trust

**Hardware and time.**
- [V] No hardware requirement is stated in the README
- [E] An MLP on bag-of-words should train on CPU or any GPU

**Missing information.**
- Random seeds
- Hyperparameter configuration files
- Licence of the benchmark data

**Experimental risks.** [E] The BERT comparison may exceed 8 GB VRAM on long documents; DistilBERT is the fallback

**Suggested experiments.**
- Reproduction: rerun the wide MLP on the same benchmarks with 5 seeds and report mean and standard deviation next to the published numbers
- Replication: re-implement the MLP independently (for example with scikit-learn) and test whether the conclusion holds
- Extension: add one graph model published after 2022

### 2. Every Document Owns Its Structure: Inductive Text Classification via Graph Neural Networks ([Zhang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.31))
**Mode:** reproduction  
**Result status:** assessed_only (NOT executed; nothing below is a reproduction result)  
**Code:** https://github.com/CRIPAC-DIG/TextING (licence None, 182 stars, last push 2024-04-25, 15 open issues)

| Item | Status | Evidence / note |
| --- | --- | --- |
| Full paper publicly available | verified | https://arxiv.org/abs/2004.13826 |
| Implementation available | found | https://github.com/CRIPAC-DIG/TextING |
| Code licence | not_found | not reported |
| Dependencies / environment specified | not_found | not reported |
| Dataset access and preprocessing instructions | found | file: build_graph.py; README: "...`data/corpus/` and the label file under `data/` as other datasets do. Preprocess the text by running `remove_words.py` before bu |
| Training configuration and hyperparameters | found | README: "...raining and inference as: python train.py [--dataset DATASET] [--learning_rate LR] [--epochs EPOCHS] [--batch_size BATCHSIZE]... |
| Training entry point | found | file: train.py |
| Random seeds / determinism controls | not_found | not reported |
| Hardware requirements stated | not_found | not reported |
| Evaluation script or protocol | not_found | not reported |
| Pretrained weights or checkpoints | not_found | not reported |
| Published results to compare against | found | README: "...dden size and batch size are suggested as long as your memory allows. We report our result based on 96 hidden size with 1 batch. |
| Model architecture fully specified | manual_review | not reported |
| Repository maintenance | verified | last push 2024-04-25; archived: False |
| Existing reproduction attempts | manual_review | Token-Level Graphs for Short Text Classification (2025) https://doi.org/10.1007/978-3-031-88714-7_42; Smoothed-ModernBERT: Cross-Modal Gated Attention of Probabilistic Topic Models and ModernBERT Through Dynamic Fusion (2026) https://doi.org/ |

**Why reproducing it is valuable.** [E] Frequently used as a baseline, so a checked number is useful

**Hardware and time.** [V] README gives no memory figure and suggests larger sizes 'as long as your memory allows'

**Missing information.**
- Dependency versions
- Random seeds
- Code licence
- Hardware requirements

**Experimental risks.** [E] Without pinned dependencies the code may need porting

**Suggested experiments.** Reproduction with the README's stated configuration over 5 seeds

### 3. Graph Convolutional Networks for Text Classification ([Yao et al. 2019](https://doi.org/10.1609/aaai.v33i01.33017370))
**Mode:** reproduction  
**Result status:** assessed_only (NOT executed; nothing below is a reproduction result)  
**Code:** https://github.com/yao8839836/text_gcn (licence None, 1390 stars, last push 2021-12-29, 112 open issues)

| Item | Status | Evidence / note |
| --- | --- | --- |
| Full paper publicly available | verified | https://arxiv.org/abs/1809.05679 |
| Implementation available | found | https://github.com/yao8839836/text_gcn |
| Code licence | not_found | not reported |
| Dependencies / environment specified | not_found | not reported |
| Dataset access and preprocessing instructions | found | file: build_corpus.py; file: build_graph.py |
| Training configuration and hyperparameters | not_found | not reported |
| Training entry point | found | file: train.py |
| Random seeds / determinism controls | not_found | not reported |
| Hardware requirements stated | not_found | not reported |
| Evaluation script or protocol | found | README: "...), 7370-7377 ## Require Python 2.7 or 3.6 Tensorflow >= 1.4.0 ## Reproducing Results 1. Run `python remove_words.py 20ng` 2. Run |
| Pretrained weights or checkpoints | not_found | not reported |
| Published results to compare against | not_found | not reported |
| Model architecture fully specified | manual_review | not reported |
| Repository maintenance | verified | last push 2021-12-29; archived: False |
| Existing reproduction attempts | manual_review | Incorporating Syntactic and Semantic Information in Word Embeddings using Graph Convolutional Networks (2019) https://doi.org/10.18653/v1/p1; Detecting hate speech in memes: a review (2023) https://doi.org/10.1007/s10462-023-10459-7 |

**Why reproducing it is valuable.** [V] The reference method of the area; later claims are measured against it ([Wang et al. 2024](https://doi.org/10.1007/s10462-024-10808-0))

**Hardware and time.**
- [V] Not stated
- [V] The single corpus graph is O(N^2) in vocabulary plus corpus size ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279))

**Missing information.**
- Dependency file
- Random seeds
- Code licence
- Hardware requirements

**Experimental risks.** [E] Legacy TensorFlow 1 stack may not install on current systems; a third-party PyTorch port exists but would make this a replication

**Suggested experiments.**
- Reproduction in a container with the legacy stack
- Replication with the third-party PyTorch port (iworldtong/text_gcn.pytorch), reported as a replication

### 4. BoW-based neural networks vs. cutting-edge models for single-label text classification ([Abdalla et al. 2023](https://doi.org/10.1007/s00521-023-08754-z))
**Mode:** reproduction  
**Result status:** assessed_only (NOT executed; nothing below is a reproduction result)  
**Code:** https://github.com/aliamer/BoW-Based-Neural-Networks-for-Text-Classification (licence None, 2 stars, last push 2023-06-15, 0 open issues)

| Item | Status | Evidence / note |
| --- | --- | --- |
| Full paper publicly available | not_found | not reported |
| Implementation available | found | https://github.com/aliamer/BoW-Based-Neural-Networks-for-Text-Classification |
| Code licence | not_found | not reported |
| Dependencies / environment specified | not_found | not reported |
| Dataset access and preprocessing instructions | not_found | not reported |
| Training configuration and hyperparameters | not_found | not reported |
| Training entry point | not_found | not reported |
| Random seeds / determinism controls | not_found | not reported |
| Hardware requirements stated | not_found | not reported |
| Evaluation script or protocol | not_found | not reported |
| Pretrained weights or checkpoints | not_found | not reported |
| Published results to compare against | not_found | not reported |
| Model architecture fully specified | manual_review | not reported |
| Repository maintenance | verified | last push 2023-06-15; archived: False |
| Existing reproduction attempts | unavailable | not reported |

**Why reproducing it is valuable.** *Not provided (missing information).*

**Hardware and time.** *Not provided (missing information).*

**Missing information.**
- Open-access full text
- Abstract
- Training and evaluation scripts
- Dependencies
- Licence

**Experimental risks.** [V] Blocked unless the paper can be obtained through a library

**Suggested experiments.** *Not provided (missing information).*

## Practical ranking

Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any blocker removes a candidate from the ranking no matter how high its other scores are. Novelty is capped at 2 unless the closest prior work was read in full, and at 1 when that work already ran the experiment.

| Rank | Candidate | Status | Score % | Range | Scored weight % | Verified weight % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bag-of-Words vs. Graph vs. Sequence (Galke & Scherp) | VIABLE | 68.2 | 68.2-68.2 | 100.0 | 52.0 |
| 2 | TextING (Zhang et al.) | VIABLE | 59.8 | 52.6-64.6 | 88.0 | 49.0 |
| 3 | TextGCN (Yao et al.) | VIABLE | 59.5 | 52.4-64.4 | 88.0 | 59.0 |
| - | BoW-based neural networks vs. cutting-edge models (Abdalla et al.) | BLOCKED | 41.8 | 9.2-87.2 | 22.0 | 10.0 |

**Scores per criterion (0-5).**

| Criterion | Weight | galke2022 | zhang2020 | yao2019 | abdalla2023 |
| --- | --- | --- | --- | --- | --- |
| scientific relevance | 12 | 4 [V] | 4 [V] | 5 [V] | 3 [E] |
| novelty or replication value | 12 | 2 [E] | 2 [E] | 2 [E] | unscored |
| paper and code availability | 10 | 4 [V] | 3 [V] | 3 [V] | 1 [V] |
| dataset accessibility | 12 | 3 [V] | 3 [V] | 4 [V] | unscored |
| compute fit | 12 | 4 [E] | unscored | unscored | unscored |
| implementation simplicity | 10 | 4 [V] | 3 [E] | 2 [V] | unscored |
| time fit | 10 | 4 [E] | 3 [E] | 3 [E] | unscored |
| reproducibility | 8 | 2 [V] | 2 [V] | 1 [V] | unscored |
| evaluation clarity | 7 | 3 [E] | 4 [V] | 4 [V] | unscored |
| low failure risk | 7 | 4 [E] | 3 [E] | 2 [E] | unscored |

**Bag-of-Words vs. Graph vs. Sequence (Galke & Scherp)**
- scientific relevance: ACL 2022; 43 citations at retrieval
- novelty or replication value: The result contradicts a line of graph-based work, so independent confirmation is informative
- paper and code availability: Open access on arXiv; https://github.com/lgalke/text-clf-baselines (licence MIT, 29 stars, last push 2026-04-21, 0 open issues); requirements.txt, pyproject.toml and uv.lock are present
- dataset accessibility: README sends the user to the TextGCN repository data folder, which responds (HTTP 200)
- compute fit: The headline model is an MLP on bag-of-words; the BERT comparison is heavier and can be dropped
- implementation simplicity: Entry points exist: main.py, run_text_classification.py
- time fit: About 4 weeks
- reproducibility: No seed or determinism text and no config files were found by the automated check
- evaluation clarity: Accuracy on standard benchmarks; no results table was detected in the README
- low failure risk: Maintained repository with pinned dependencies
- Missing: dataset_accessibility: Licence of the benchmark files
- Missing: compute_fit: No hardware statement found
- Capped: novelty or replication value 4 -> 2 (closest prior work read at level 'abstract', not full text)

**TextING (Zhang et al.)**
- scientific relevance: 316 citations at retrieval
- novelty or replication value: A common baseline in later papers
- paper and code availability: Open access on arXiv; https://github.com/CRIPAC-DIG/TextING (licence None, 182 stars, last push 2024-04-25, 15 open issues); No licence and no dependency file found
- dataset accessibility: README describes where corpus and label files go; build_graph.py is present
- implementation simplicity: train.py with documented command-line options
- time fit: About 5 weeks
- reproducibility: No dependency file and no seed handling found; hyperparameters are command-line flags
- evaluation clarity: README states the configuration used for the reported results
- low failure risk: 2 issue(s) mention reproduction
- Missing: dataset_accessibility: Where to download the corpora; their licence
- Missing: compute_fit: README says to raise hidden size and batch size 'as long as your memory allows'; no figure is given
- Not scored for lack of evidence: compute_fit
- Capped: novelty or replication value 3 -> 2 (closest prior work read at level 'abstract', not full text)

**TextGCN (Yao et al.)**
- scientific relevance: 2145 citations at retrieval; the reference method of the area
- novelty or replication value: Already re-implemented several times (two third-party repositories were found)
- paper and code availability: Open access on arXiv; https://github.com/yao8839836/text_gcn (licence None, 1390 stars, last push 2021-12-29, 112 open issues); No licence
- dataset accessibility: Data folder and preparation scripts are in the repository
- implementation simplicity: README requires Python 2.7 or 3.6 and TensorFlow >= 1.4, a legacy stack
- time fit: About 6 weeks, mostly environment work
- reproducibility: No dependency file, no seed handling; 5 issues mention reproduction
- evaluation clarity: README has a 'Reproducing Results' section with the commands
- low failure risk: Unmaintained since 2021 with many open issues
- Missing: dataset_accessibility: Licence of the benchmark files
- Missing: compute_fit: No hardware statement found; graph memory on the larger benchmarks is unknown
- Not scored for lack of evidence: compute_fit
- Capped: novelty or replication value 3 -> 2 (closest prior work read at level 'abstract', not full text)

**BoW-based neural networks vs. cutting-edge models (Abdalla et al.)**
- BLOCKER (full_text): No open-access copy of the paper was located, so the method cannot be checked against the code
- scientific relevance: Directly related to the bag-of-words versus graph question
- paper and code availability: https://github.com/aliamer/BoW-Based-Neural-Networks-for-Text-Classification (licence None, 2 stars, last push 2023-06-15, 0 open issues); No training or evaluation entry point, dependency file or licence was found
- Missing: dataset_accessibility: No dataset instructions found
- Missing: compute_fit: Unknown
- Missing: time_fit: Unknown
- Not scored for lack of evidence: novelty_or_replication_value, dataset_accessibility, compute_fit, implementation_simplicity, time_fit, reproducibility, evaluation_clarity, low_failure_risk

## Datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [TextGCN benchmark data folder](https://github.com/yao8839836/text_gcn/tree/master/data) | Benchmark files used by TextGCN and reused by later work | not reported | not reported | not reported | reachable (HTTP 200) | Repository scripts (remove_words.py, build_graph.py) | Needed for O1, O2 and all reproductions; only reachability was checked | yes |
| [SetFit/20_newsgroups](https://huggingface.co/datasets/SetFit/20_newsgroups) | Topic classification (20 Newsgroups mirror) | 18846 rows | json | not reported | open | Tokenisation; bag-of-words or graph construction | Convenient mirror; confirm it matches the benchmark split before comparing with published numbers | yes |
| [RottenTomatoes - MR Movie Review Data](https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes) | Sentence-level sentiment (MR) | 10662 rows | parquet | unknown | open | Tokenisation | Short texts; splits may differ from the benchmark version | yes |
| [Ohsumed](https://huggingface.co/datasets/community-datasets/ohsumed) | Medical abstracts with subject headings | 348564 rows | parquet | cc-by-nc-4.0 | open | Subset selection and single-label filtering would be needed | Much larger than a typical benchmark subset and multi-label; not a drop-in replacement | yes |

## Recommendation

Reproduce ([Galke & Scherp 2022](https://doi.org/10.18653/v1/2022.acl-long.279)) first. Treat every status below as a pre-assessment: open each repository and the paper's experiment section before committing.

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | verified: 9 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: not recorded: 9; claims: estimate: 6, verified: 6 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | no opportunities | How far the searches support a gap; never above medium. |
| Reproducibility | 0 of 4 candidate(s) executed | Whether results were re-run, not whether code exists. |

## Limitations of this assessment

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
