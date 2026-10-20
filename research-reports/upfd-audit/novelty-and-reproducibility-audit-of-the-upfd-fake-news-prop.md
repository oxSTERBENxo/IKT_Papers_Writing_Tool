# Novelty and reproducibility audit of the UPFD fake-news proposal

**Report type:** Research Opportunity Report  
**Generated:** 2026-10-18

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | Graph neural networks for fake news detection (UPFD benchmark) | stated by user |
| experience | undergraduate, comfortable with Python | default (not stated by user) |
| hardware | one consumer GPU, 8 GB VRAM (or a free cloud notebook) | default (not stated by user) |
| gpu vram gb | 8 | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| language | Python | default (not stated by user) |
| difficulty | moderate | default (not stated by user) |
| mode | any | default (not stated by user) |

## Summary

No-go for the proposal as written: the graph-vs-no-graph comparison on UPFD is already published ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)). The continuation measured on the official split files that a model-free vote over users seen in training reaches 86.0% on PolitiFact and 90.3% on GossipCop, and that repeat users carry identical feature vectors, so every per-graph model can use the shortcut. That shared users predict labels is itself already published ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)); what appears open is treating it as a confound of per-graph benchmark results. Conditional go for that narrower question, scoped to PolitiFact for controlled experiments.

## Decisions

Each shortlisted research question gets go, conditional go or no-go. A go requires full-text reading of the closest work and an explicit check for leakage, weak baselines and evaluation flaws; anything short of that is at most a conditional go.

| Research question | Decision | Novelty confidence | Mode | Main conditions |
| --- | --- | --- | --- | --- |
| As proposed: multi-seed graph vs no-graph re-evaluation of UPFD | NO-GO | very_low | replication | not reported |
| Revised (twice): do per-graph UPFD results reflect recurring users rather than content or structure? | CONDITIONAL GO | low | extension | Read ([Rai & Rai 2025](https://doi.org/10.1007/978-981-96-4722-4_9)), ([Rai & Rai 2025](https://doi.org/10.1007/978-981-97-9855-1_7)) and ([A & Kasprzyk 2026](https://doi.org/10.1007/978-3-032-14163-7_21)) through the library; if any evaluates per-graph models on unseen users or reports split overlap, reframe as a replication.; Before running models, state the smallest ac |
| Fallback: independent replication of Karn and Jensen with a held-out test set | NO-GO | low | replication | not reported |

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | verified: 15 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: abstract: 5, full text: 6, not accessible: 3, title only: 1; claims: estimate: 6, speculative: 1, verified: 23 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | As proposed: multi-seed graph vs no-graph re-evaluation of UPFD: very_low (search ceiling low); Revised (twice): do per-graph UPFD results reflect recurring users rather than content or structure?: low (search ceiling low); Fallback: independent replication of Karn and Jensen with a held-out test set: low | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## How the literature was searched

- **Sources that answered:** openalex, arxiv, crossref, huggingface
- **Sources that failed or were skipped:** semantic_scholar (rate_limited / HTTP 429 during challenge searches and paper resolution)
- **Search strategies:** challenge, citations of UPFD (OpenAlex citing works), web search, full-text reading of arXiv TeX sources, code reading
- **Date range:** 2019 onwards (citing works of UPFD); challenge searches unrestricted
- **Records retrieved / after deduplication:** 626 / None
- **Search date:** 2026-10-18
- **Queries:** `UPFD fake news graph neural network content-only baseline`; `does propagation structure help fake news detection`; `propagation graph ablation fake news detection text-only baseline outperforms`; `rethinking evaluation fake news detection graph neural networks benchmark`; `user engagement graph necessary fake news detection GNN`; `FakeNewsNet propagation-based detection reproducibility`; `simple baseline fake news detection propagation graphs`; `user overlap train test leakage fake news detection social context`; `user-disjoint split fake news detection graph`; `fake news detection shortcut user identity memorization`; `spurious correlations social context fake news detection evaluation`; `unseen users generalization propagation-based fake news detection`; `FakeNewsNet data leakage evaluation bias`
- 217 and 223 records examined by the two challenge commands; 186 works citing UPFD screened by title.
- Karn and Jensen 2025 and Xu 2025 were found by web search, not by the challenge command.
- Full texts read from arXiv TeX sources: UPFD (2104.12259), Karn and Jensen (2512.06638), DAWN (2411.12775), Xu (2512.09974, partly).
- Code read: safe-graph/GNN-FakeNews gnn_model/gnn.py, utils/data_loader.py, utils/eval_helper.py, hyper_parameters.md; PyG torch_geometric/datasets/upfd.py and examples/upfd.py.
- Continuation (same day): official split files and small feature files fetched by HTTP range requests from the PyG UPFD archives (about 60 MB of 1.6 GB; no BERT features, no full GossipCop download).
- Continuation: full text read for HGFND (arXiv 2212.12621) and the Maurya et al. PDF; Springer chapters redirected to a login page and stayed unread.
- Improved challenge (eval 5) with design elements and the UPFD paper as seed: signal close_prior_work_found, 194 papers via citations, 20 flagged as possibly the same design.

## What has already been done

| Paper | Published | Method | Datasets | Findings | Stated limitations | Read | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| User Preference-aware Fake News Detection (Dou et al. 2021) | 2021-07-11 | UPFD: news root node plus user nodes (features from users' historical tweets) in a retweet tree; one GNN layer, readout, concatenation with the news embedding | PolitiFact 314 graphs, GossipCop 5,464 graphs (Table 1) | Full text (TeX source): Table 2 already includes news-only baselines (BERT+MLP 71.04 / 85.76 acc, word2vec+MLP 76.47 / 84.61 on POL / GOS) against UPFD 84.62 / 97.23. Section 3.3 ablation '-EXO' removes all edges: accuracy 85.61 vs 81.63 on PolitiFact and 95.47 vs 93.92 on the second dataset (the text labels both sentences 'Politifact'). Five runs, t-test, 20/10/70 split. | No standard deviations reported. The ablation's full model (GCNFN, word2vec, no news concatenation) reports 85.61, above the 80.54 for GCNFN with word2vec in Table 3; the difference is not explained. | full text | [link](https://doi.org/10.1145/3404835.3462990) |
| The Impact of Data Characteristics on GNN Evaluation for Detecting Fake News (Karn & Jensen 2025) | 2025-12-07 | Five GNNs (GCN, GAT, GraphSAGE, GCNFN, GNNCL) against an MLP that mean-pools all node features; feature shuffling, edge rewiring and synthetic ego-graphs | UPFD PolitiFact and GossipCop, BERT (768-d) features only | Full text (TeX source): stratified 10-fold CV, mean validation accuracy with 95% CI. Table 2: GossipCop GCNFN 96.1 +/- 1.6 vs MLP 90.8 +/- 3.0; PolitiFact GCNFN 82.7 +/- 5.5 vs MLP 74.3 +/- 7.4. Edge rewiring leaves accuracy above 90% on GossipCop; feature shuffling collapses GAT/GraphSAGE to chance while GCN and GNNCL keep about 80% on GossipCop, which the authors attribute to graph size or density. Over 75% of nodes are one hop from the root. | Preprint, no code found (author portfolio lists it as a preprint). Text and table disagree: MLP on GossipCop 93.87% in text vs 90.8% in Table 2; MLP on PolitiFact 80.93% vs 74.3%; GAT on GossipCop 95.26% vs 91.5%. Reports validation accuracy only (no held-out test). The MLP pools user nodes too, so it does not separate news content from user features. | full text | [link](https://arxiv.org/abs/2512.06638) |
| Revisiting Fake News Detection: Towards Temporality-aware Evaluation by Leveraging Engagement Earliness (Kim et al. 2025) | 2025-02-26 | Temporality-aware evaluation (70/10/20 temporal split, social context split accordingly) and DAWN edge reweighting by engagement earliness | FakeNewsNet PolitiFact (597 articles) and GossipCop (8,763 articles) built from raw FakeNewsNet, not the UPFD release | Full text (arXiv 2411.12775 TeX source): Table 2, average of 5 runs, no standard deviations: BERT content-only 84.2 / 76.4 acc vs GCN 86.4 / 87.4 and GraphSAGE 85.4 / 87.5 on PolitiFact / GossipCop. Figure caption: users tend to engage with either only fake or only real news. | Code at github.com/LeeJunmo/DAWN has no licence; automated check found no seed control. | full text | [link](https://doi.org/10.1145/3701551.3703524) |
| A New DAWN for Fake News Detection: Exploiting Engagement Earliness for Temporality-aware Evaluation (Kim et al. 2026) | 2026-05-07 | Journal version of DAWN (ACM TIST) | not reported | Abstract only: same temporality-aware evaluation claim as the WSDM paper | not reported | abstract | [link](https://doi.org/10.1145/3815193) |
| Enhancing Fake-News Detection with Node-Level Topological Features (Xu 2025) | 2025-12-10 | Appends degree centrality and local clustering coefficient to UPFD node features | UPFD PolitiFact and GossipCop, BERT features | Abstract and full text: PolitiFact macro-F1 0.7753 to 0.8344; on GossipCop the baseline has slightly better F1 (0.9551 vs 0.9451) | No split, seed or number of runs found in the TeX source | full text | [link](https://arxiv.org/abs/2512.09974) |
| DECOR: Degree-Corrected Social Graph Refinement for Fake News Detection (Wu & Hooi 2023) | 2023-08-04 | Degree-corrected social graph refinement for fake news detection | Two real-world benchmarks (abstract) | Abstract: degrees of news article nodes show distinctive patterns indicative of veracity | not reported | abstract | [link](https://doi.org/10.1145/3580305.3599298) |
| FANG: Leveraging Social Context for Fake News Detection Using Graph Representation (Nguyen et al. 2020) | 2020-10-19 | FANG: graph representation of the social context (users, sources, news) | not reported | Abstract: learned social-context representations improve fake news detection; cited here because user reuse across news is an intended signal in such social-context models | not reported | abstract | [link](https://doi.org/10.1145/3340531.3412046) |
| Beyond Reported Accuracy: A Verifiability-Focused, Multi-Axis Review of Content and Context Based Fake News Detection (Tuan et al. 2026) | 2026-09-11 | Verifiability-focused review of 45 fake news detection studies | not reported | Abstract: reported performance appears shaped as much by data and evaluation design as by architecture; near-perfect results may reflect separability, leakage or favourable evaluation | not reported | abstract | [link](https://doi.org/10.62411/jcta.17476) |
| A critical look at the evaluation of GNNs under heterophily: Are we really making progress? (Platonov et al. 2023) | 2023-02-22 | Critique of heterophily benchmarks | not reported | Abstract: duplicate nodes cause train-test leakage in standard benchmarks; precedent for a data-overlap audit | not reported | abstract | [link](https://arxiv.org/abs/2302.11640) |
| Multi-dataset Analysis of Misinformation Networks: Divergent Graph Structures and Challenges for Fake News Detection (A & Kasprzyk 2026) | 2026-01-01 | not reported | not reported | Abstract not retrievable programmatically (publisher login redirect). A web-search summary describes a structural comparison of true and false propagation graphs across platforms; not verified against the text. | not reported | not accessible | [link](https://doi.org/10.1007/978-3-032-14163-7_21) |
| Exploring the Efficacy of Attention Mechanisms in GNN-Based Fake News Detection on UPFD Dataset (Rai & Rai 2025) | 2025-01-01 | not reported | UPFD (title) | Title only; not read | not reported | not accessible | [link](https://doi.org/10.1007/978-981-97-9855-1_7) |
| Leveraging Hypergraph Neural Network for Fake News Detection on UPFD Dataset (Rai & Rai 2025) | 2025-01-01 | not reported | UPFD (title) | Title only; not read | not reported | not accessible | [link](https://doi.org/10.1007/978-981-96-4722-4_9) |
| Fake news detection: A survey of graph neural network methods (Phan et al. 2023) | 2023-03-23 | Survey of GNN methods for fake news detection | not reported | Cited as evidence the area is surveyed; abstract not read | not reported | title only | [link](https://doi.org/10.1016/j.asoc.2023.110235) |
| Nothing Stands Alone: Relational Fake News Detection with Hypergraph Neural Networks (Jeong et al. 2022) | 2022-12-24 | HGFND: hypergraph neural network over news items, with hyperedges for shared users, shared time windows and shared entities; transductive node classification | UPFD PolitiFact and GossipCop (news and user information from the UPFD release) | Full text (TeX source): user hyperedges connect news items that share a Twitter user ID (2,953 such users in PolitiFact, 15,646 in GossipCop). With user hyperedges alone the model reaches 87.23 +/- 2.32 (PolitiFact) and 97.29 +/- 0.16 (GossipCop) accuracy; all three hyperedge types give 91.13 / 97.46. Baselines trained with 10 seeds, model chosen on validation. The authors conclude that users play a key role in detecting fake news. | Treats shared users as intended signal in a transductive setting and states there is no label leakage because test labels are hidden; does not evaluate on unseen users | full text | [link](https://arxiv.org/abs/2212.12621) |
| Implementation of Weight Adjusting GNN With Differentiable Pooling for User Preference-aware Fake News Detection (Maurya et al. 2024) | 2024-02-09 | GCN and DiffPool-based GNN on UPFD PolitiFact | UPFD PolitiFact only | Full text (Research Square PDF): single reported run; test accuracy 0.82 for GCN | No seeds, no structure-free baseline, no user-overlap or user-disjoint analysis | full text | [link](https://doi.org/10.21203/rs.3.rs-3942141/v1) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

### Directions that are already well explored

- [V] GNN vs news-only or structure-agnostic baselines on UPFD, including edge removal, edge rewiring and feature shuffling ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990); [Karn & Jensen 2025](https://arxiv.org/abs/2512.06638))
- [V] Content-only vs social-graph models under temporality-aware splits on FakeNewsNet ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524))
- [V] Adding explicit topology features to UPFD node features ([Xu 2025](https://arxiv.org/abs/2512.09974))
- [E] New GNN architectures on UPFD (inferred from titles screened among 186 citing works) ([Rai & Rai 2025](https://doi.org/10.1007/978-981-97-9855-1_7); [Rai & Rai 2025](https://doi.org/10.1007/978-981-96-4722-4_9))

## Ranked research opportunities

Each opportunity below survived an explicit search for work that already addresses it. None is claimed to be novel: the novelty confidence states how far the search supports the gap, and what it could have missed.

### 1. Revised (twice): do per-graph UPFD results reflect recurring users rather than content or structure?
**Type of gap:** Unverified novelty hypothesis  
**Recommended mode:** extension  
**Revised:** First revision: the graph-vs-no-graph question is answered ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)). Second revision (this continuation): full-text reading of ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)) showed that the predictive power of users shared between news items is already published, as a deliberate transductive signal. What remains open in the sources read is the evaluation question: how much of the accuracy reported for per-graph models on the official UPFD split, and of conclusions such as 'structure adds little', comes from recurring users that the models can recognise through identical feature vectors.

**Research question.** On the official UPFD split, how much of the accuracy of per-graph GNNs and of same-feature MLPs is explained by test users seen in training, and do published conclusions about news content versus propagation structure hold when that shortcut is controlled (PolitiFact: masking seen users; GossipCop: descriptive only)?

**Motivation.** Published comparisons on UPFD attribute performance to news content, user preferences or propagation structure ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990); [Karn & Jensen 2025](https://arxiv.org/abs/2512.06638)). Every model that pools user-node features, including Karn and Jensen's MLP, can also exploit recurring users, and DAWN observes that users tend to engage with only one class ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)). A review of fake news studies argues reported accuracies are shaped by evaluation design and possible leakage ([Tuan et al. 2026](https://doi.org/10.62411/jcta.17476)).

**Supporting papers.** ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Kim et al. 2025](https://doi.org/10.1145/3701551.3703524); [Jeong et al. 2022](https://arxiv.org/abs/2212.12621); [Tuan et al. 2026](https://doi.org/10.62411/jcta.17476); [Platonov et al. 2023](https://arxiv.org/abs/2302.11640))

**Closest existing work.**
- ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)) [read: full text; overlap: partial]: Uses shared users as a feature (user hyperedges) and reports their predictive power; does not treat them as a confound of per-graph benchmark results or evaluate on unseen users.
- ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638)) [read: full text; overlap: partial]: Isolates edges and features with rewiring and shuffling; keeps user nodes and random stratified folds in every condition, so the user shortcut is present throughout.
- ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)) [read: full text; overlap: partial]: Temporal split on raw FakeNewsNet; notes users' label consistency but does not measure user overlap between splits.
- ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) [read: full text; overlap: different]: Defines the benchmark and split; no overlap analysis.
- ([A & Kasprzyk 2026](https://doi.org/10.1007/978-3-032-14163-7_21)) [read: not accessible; overlap: unknown]: Not read; title and a search summary suggest structural analysis, not split leakage.
- ([Rai & Rai 2025](https://doi.org/10.1007/978-981-96-4722-4_9)) [read: not accessible; overlap: unknown]: Not read; title suggests a hypergraph model on UPFD, possibly with user hyperedges.

**Evidence for the gap.**
- [V] Official split files (PyG/UPFD train_idx/test_idx; 62 PolitiFact and 1092 GossipCop training graphs): a vote over the training labels of a test graph's users, with no model, text or edges, reaches 86.0% on PolitiFact and 90.2% on GossipCop (majority class 48.9% and 49.9%). 79.6% and 98.8% of test graphs share a user with training. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990))
- [V] The shortcut is visible to any model through its inputs: 94.3% (spaCy history features) and 94.7% (profile features) of PolitiFact repeat users, and 86.4% of GossipCop repeat users (profile features), carry an identical feature vector in every graph they appear in. Using the feature vector itself as the identity gives the same vote accuracy (86.0% PolitiFact, 90.8% GossipCop). BERT features were not downloaded and not checked. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990))
- [V] Published accuracies on the same data: UPFD 84.62 (PolitiFact) and 97.23 (GossipCop), its news-only MLPs 71.04-76.47 and 84.61-85.76; the same-feature MLP of Karn and Jensen 74.3 and 90.8; HGFND with user hyperedges only 87.23 and 97.29. The model-free user vote is at or above several of these. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990); [Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Jeong et al. 2022](https://arxiv.org/abs/2212.12621))
- [V] That shared users predict veracity is already published: HGFND builds one hyperedge per user shared between news items (2,953 PolitiFact, 15,646 GossipCop, the same counts measured here) and reaches 87.23 / 97.29 accuracy from them alone. It treats this as a legitimate transductive signal, not as a confound of per-graph evaluations. ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621))
- [V] No source read in full (UPFD, Karn and Jensen, DAWN, HGFND, Xu, Maurya) reports train/test user overlap for per-graph models or evaluates on unseen users. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990); [Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Kim et al. 2025](https://doi.org/10.1145/3701551.3703524); [Jeong et al. 2022](https://arxiv.org/abs/2212.12621); [Xu 2025](https://arxiv.org/abs/2512.09974); [Maurya et al. 2024](https://doi.org/10.21203/rs.3.rs-3942141/v1))

**Potential contribution.** A short benchmark-validity study: the identity shortcut quantified on the official split, its availability through feature vectors, and whether per-graph models and the 'structure adds little' conclusion change when it is controlled on PolitiFact. Either outcome is reportable; the scope suits a workshop or reproducibility track.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). The observation that users predict labels is published ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)); only its use as an evaluation confound appears open in the papers read. Three UPFD-related chapters could not be read, Semantic Scholar was rate-limited, and user-disjoint evaluation is common in neighbouring areas under other names (cold-start, inductive users).
Attempts to disprove novelty: 10 search(es); signal `no_close_match_in_this_search`. Queries: `user overlap train test leakage fake news detection social context`; `user-disjoint split fake news detection graph`; `fake news detection shortcut user identity memorization`; `spurious correlations social context fake news detection evaluation`; `unseen users generalization propagation-based fake news detection`; `FakeNewsNet data leakage evaluation bias`; `propagation graph contribution fake news detection GNN ablation`; `structure-agnostic baseline graph neural network misinformation benchmark`

**Feasibility.**
- [V] A strict user-disjoint split is infeasible on both datasets: shared users link 93.0% of PolitiFact and 99.6% of GossipCop graphs into one component; even ignoring users in 3+ graphs the largest component holds 85.4% and 54.6%.
- [V] Masking test-graph users seen in training is a small change on PolitiFact (8.9% of test user nodes removed; median users per test graph 91 -> 78; 2 graphs emptied) but a large distribution shift on GossipCop (71.6% removed; median 48.0 -> 6.0; 359 graphs emptied).
- [E] PolitiFact has 221 official test graphs, so a 95% interval on accuracy is roughly +/- 5-6 points; only large differences between conditions will be detectable.
- [V] All checks ran on CPU from about 60 MB of index, label and feature files; models would also be CPU-scale.

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| train test overlap | found | [V] Official split files (PyG/UPFD train_idx/test_idx; 62 PolitiFact and 1092 GossipCop training graphs): a vote over the training labels of a test graph's users, with no model, text or edges, reaches 86.0% on PolitiFact and 90.2% on GossipCop (majority class 48.9% and 49.9%). 79.6% and 98.8% of test graphs share a user with training. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) | Mask seen users in PolitiFact test graphs; report the user vote as a baseline everywhere. |
| weak baseline | found | [V] No published UPFD comparison includes a user-identity vote or a graph-size rule; the size rule reaches 74.9% on GossipCop's official test split (fails on PolitiFact: 48.4%). | Include user vote, size rule, root-only MLP and same-feature MLP as baselines. |
| protocol mismatch | found | [V] The official GNN-FakeNews script draws a random split instead of the fixed split files used by PyG, selects no model on validation, and differs from the paper on pooling and weight decay. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) | Use the fixed split files plus repeated random splits; select on validation. |
| metric definition | found | [V] The official evaluation helper averages macro-F1 over batches. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) | Compute metrics on the whole test set. |
| insufficient runs | found | [V] 221 PolitiFact test graphs and 62 training graphs; published comparisons use 5 runs. ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) | 10+ seeds and repeated splits with paired comparisons; report intervals. |
| distribution shift | found | [V] Masking test-graph users seen in training is a small change on PolitiFact (8.9% of test user nodes removed; median users per test graph 91 -> 78; 2 graphs emptied) but a large distribution shift on GossipCop (71.6% removed; median 48.0 -> 6.0; 359 graphs emptied). | Make causal claims only for PolitiFact; GossipCop analysed descriptively. |
| label leakage | checked ok | [V] graph_labels match FakeNewsNet's fake/real lists for 313 of 314 PolitiFact and all 5,464 GossipCop graphs (one PolitiFact mismatch unexplained). | not reported |
| temporal leakage | not checked | User features come from historical tweets crawled after the news; their timing was not examined. | not reported |

**Decision: CONDITIONAL GO.** The shortcut is real, large and measured on the official split, and no source read treats it as a confound of per-graph results. But the signal itself is known ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)), the controlled experiment is only clean on PolitiFact (221 test graphs), and three related chapters are unread. Worth doing as a short, scoped benchmark-validity study, not as a full-semester flagship.

**Conditions before committing.**
- Read ([Rai & Rai 2025](https://doi.org/10.1007/978-981-96-4722-4_9)), ([Rai & Rai 2025](https://doi.org/10.1007/978-981-97-9855-1_7)) and ([A & Kasprzyk 2026](https://doi.org/10.1007/978-3-032-14163-7_21)) through the library; if any evaluates per-graph models on unseen users or reports split overlap, reframe as a replication.
- Before running models, state the smallest accuracy change on masked PolitiFact that would matter, and check it exceeds the roughly +/- 5-6 point interval from 221 test graphs; if not, keep the study descriptive.
- Frame against ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)) (users as a feature) and ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638)) (structure ablation), not as a discovery that users matter.

**Unresolved evidence and risks.**
- BERT user features not checked for identity (only spaCy and profile features were).
- Whether the user-feature timing leaks post-publication information is unknown.
- Reviewers may consider the result implied by HGFND.

### Candidates rejected after the novelty challenge

- **As proposed: multi-seed graph vs no-graph re-evaluation of UPFD** (Already well studied): Reading the full texts showed the experiment has been done three times: the UPFD paper itself reports news-only baselines and an edge-removal ablation ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)); Karn and Jensen benchmark five GNNs against a same-feature MLP with 10-fold CIs, edge rewiring and feature shuffling on both UPFD datasets ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638)); and DAWN compares a BERT content-only model with GNNs under temporal splits ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524)). A further multi-seed rerun would mainly confirm Karn and Jensen. The audit also found the comparison as designed cannot isolate graph structure (see the revised question).
- **Fallback: independent replication of Karn and Jensen with a held-out test set** (Limitation reported in prior work): Folded into the revised question: replicating Karn and Jensen without controlling recurring users would repeat the confound; their comparison is re-run inside the PolitiFact masking study instead.

## Feasibility ranking

Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any blocker removes a candidate from the ranking no matter how high its other scores are. Novelty is capped at 2 unless the closest prior work was read in full, and at 1 when that work already ran the experiment.

| Rank | Candidate | Status | Score % | Range | Scored weight % | Verified weight % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Revised: recurring users as a confound of per-graph UPFD results | VIABLE | 70.6 | 70.6-70.6 | 100.0 | 54.0 |
| 2 | Fallback: replication of Karn and Jensen with held-out test | VIABLE | 62.6 | 62.6-62.6 | 100.0 | 61.0 |
| 3 | As proposed: graph vs no-graph re-evaluation (original O1) | VIABLE | 62.0 | 62.0-62.0 | 100.0 | 71.0 |

**Scores per criterion (0-5).**

| Criterion | Weight | B | C | A |
| --- | --- | --- | --- | --- |
| scientific relevance | 12 | 4 [E] | 3 [V] | 3 [V] |
| novelty or replication value | 12 | 2 [E] | 2 [V] | 1 [V] |
| paper and code availability | 10 | 4 [V] | 2 [V] | 4 [V] |
| dataset accessibility | 12 | 3 [V] | 3 [V] | 3 [V] |
| compute fit | 12 | 5 [E] | 5 [E] | 5 [E] |
| implementation simplicity | 10 | 4 [V] | 3 [E] | 4 [V] |
| time fit | 10 | 4 [E] | 5 [E] | 5 [E] |
| reproducibility | 8 | 2 [V] | 1 [V] | 1 [V] |
| evaluation clarity | 7 | 3 [V] | 3 [V] | 2 [V] |
| low failure risk | 7 | 4 [V] | 4 [E] | 2 [E] |

**Revised: recurring users as a confound of per-graph UPFD results**
- scientific relevance: UPFD is the standard PyG fake-news benchmark; the diagnostic suggests published comparisons may misattribute performance ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Tuan et al. 2026](https://doi.org/10.62411/jcta.17476))
- novelty or replication value: Shared-user signal already published ([Jeong et al. 2022](https://arxiv.org/abs/2212.12621)); its role as an evaluation confound not found in six full texts; three chapters unread
- paper and code availability: Same code and loader as A; overlap script written in this audit
- dataset accessibility: Mappings and labels downloaded and parsed (under 60 MB)
- compute fit: Same CPU-scale models as A
- implementation simplicity: Overlap measurement already scripted; masking is a data transform on PyG graphs
- time fit: About 6 weeks including the one-week go/no-go checks
- reproducibility: Diagnostic is scripted and deterministic; upstream training code has the issues listed for A
- evaluation clarity: Official split files read; but only 221 PolitiFact test graphs
- low failure risk: Descriptive results already in hand; model runs add to them
- Missing: novelty_or_replication_value: Three UPFD chapters unread
- Missing: dataset_accessibility: Feature files not yet checked; data licence not stated

**Fallback: replication of Karn and Jensen with held-out test**
- scientific relevance: Most recent direct evidence on the question ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638))
- novelty or replication value: Unreviewed preprint with inconsistent numbers; replication value moderate, novelty low
- paper and code availability: Paper open on arXiv; no code released
- dataset accessibility: PyG loader
- compute fit: CPU-scale
- implementation simplicity: Reimplement five GNNs and perturbations from the description
- time fit: About 5 weeks
- reproducibility: No code, seeds or hyperparameters beyond batch size and weight decay
- evaluation clarity: Published table with CIs to compare against, but it conflicts with the text
- low failure risk: Confirming or failing to confirm is reportable
- Missing: dataset_accessibility: Data licence not stated

**As proposed: graph vs no-graph re-evaluation (original O1)**
- scientific relevance: Benchmark validity question raised by ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638); [Tuan et al. 2026](https://doi.org/10.62411/jcta.17476))
- novelty or replication value: Answered by ([Dou et al. 2021](https://doi.org/10.1145/3404835.3462990)) (-EXO ablation, news-only baselines), ([Karn & Jensen 2025](https://arxiv.org/abs/2512.06638)) (MLP vs 5 GNNs with CIs) and ([Kim et al. 2025](https://doi.org/10.1145/3701551.3703524))
- paper and code availability: github.com/safe-graph/GNN-FakeNews Apache-2.0; PyG loader and example
- dataset accessibility: PyG loader, docs HTTP 200
- compute fit: Graphs of 58-131 nodes on average; one-layer GNNs
- implementation simplicity: PyG example script exists
- time fit: About 4 weeks
- reproducibility: Official script ignores fixed split files, has no validation-based selection, and differs from the paper on pooling and weight decay
- evaluation clarity: Metrics standard, but published numbers come from differing protocols and a batch-averaged F1
- low failure risk: The likely outcome, structure adds little, is already published
- Missing: dataset_accessibility: Data licence not stated

## Candidate datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [UPFD (PolitiFact, GossipCop) via PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.datasets.UPFD.html) | All three options | PolitiFact 314 graphs / 41,054 nodes; GossipCop 5,464 graphs / 314,262 nodes (paper Table 1, confirmed by node counts in the id mappings); README states about 1.2 GB for the raw release | PyG InMemoryDataset; loader reads fixed train_idx/val_idx/test_idx files | not reported | reachable (HTTP 200); download via the loader from Google Drive | Choose feature type: profile, spacy, bert, content | Small; the PyG loader uses the fixed split while the original training script does not, so results from the two are not directly comparable | yes |
| [GNN-FakeNews id mappings (node id to Twitter user id, node id to timestamp)](https://github.com/safe-graph/GNN-FakeNews/tree/main/data) | User-overlap measurement (revised question) | pol_id_twitter_mapping.pkl 676 KB; gos_id_twitter_mapping.pkl 6.2 MB | Python pickle of dict[int, str] (opcodes checked: no object construction) | Repository licence Apache-2.0 (covers the repository; data terms not stated) | reachable (HTTP 200) | Graphs rebuilt by walking node ids; root order matched the released news lists exactly | Sufficient to measure overlap without downloading features | yes |
| [FakeNewsNet fake/real id lists](https://github.com/KaiDMML/FakeNewsNet/tree/master/dataset) | Labels for the overlap diagnostic | four CSV files, about 44 MB in total | CSV (id, news_url, title, tweet_ids) | not reported | reachable (HTTP 200) | Label by file name (fake/real); counts matched UPFD (157 and 2,732 fake) | Labels only | yes |

## Recommendation

- [E] Drop the original proposal (no-go) and the stand-alone replication of Karn and Jensen (no-go).
- [E] Conditional go for the recurring-user question as a 4-6 week benchmark-validity study. Its first deliverable needs no training: the overlap measurements in this report, written up with the code. Model runs on masked PolitiFact follow only if the three conditions are met.
- [S] If the unread chapters turn out to cover it, or a methods-focused project is preferred, switch to the aspect-based sentiment candidate from the opportunity report.

## Limitations of this report

- Novelty of the revised question rests on searches that missed the closest paper on the original question; treat it as unverified until the library check is done.
- Graph reconstruction assumes node ids are contiguous per graph with the news node first; this matched the released news list order and the paper's node totals, but was not checked against node_graph_id.npy.
- Accounts appearing in thousands of GossipCop graphs were not identified; removing users in 50+ graphs lowered the GossipCop vote accuracy from 91.1% to 83.9%.
- Karn and Jensen's text and table disagree; the audit quotes the table where it gives CIs and notes the conflict.
- Semantic Scholar was rate-limited throughout; citing works came from OpenAlex and were screened by title only.
- No model was trained and no published number was reproduced.
- Not read: Bryla et al. 2026, Rai et al. 2025 (two chapters); publisher pages require login.
- BERT user features (125 MB PolitiFact, 862 MB GossipCop) were not downloaded; identity was checked on spaCy and profile features (PolitiFact) and profile features (GossipCop).
- The user-vote diagnostic shows that identity carries label information; it does not show how much any trained model relies on it. No model was trained.

## References

1. Michał Bryła, Rafał Kasprzyk (2026). *Multi-dataset Analysis of Misinformation Networks: Divergent Graph Structures and Challenges for Fake News Detection*. Lecture notes in networks and systems. https://doi.org/10.1007/978-3-032-14163-7_21
2. Yingtong Dou, Kai Shu, Congyin Xia, Philip S. Yu, Li-Chao Sun (2021). *User Preference-aware Fake News Detection*. Proceedings of the 44th International ACM SIGIR Conference on Research and Development in Information Retrieval. https://doi.org/10.1145/3404835.3462990
3. Ujun Jeong, Kaize Ding, Lu Cheng, Ruocheng Guo, Kai Shu, Huan Liu (2022). *Nothing Stands Alone: Relational Fake News Detection with Hypergraph Neural Networks*. arXiv. https://arxiv.org/abs/2212.12621
4. Isha Karn, David Jensen (2025). *The Impact of Data Characteristics on GNN Evaluation for Detecting Fake News*. arXiv. https://arxiv.org/abs/2512.06638
5. Junghoon Kim, Junmo Lee, Yeonjun In, Kanghoon Yoon, Chanyoung Park (2025). *Revisiting Fake News Detection: Towards Temporality-aware Evaluation by Leveraging Engagement Earliness*. Proceedings of the Eighteenth ACM International Conference on Web Search and Data Mining. https://doi.org/10.1145/3701551.3703524
6. Junghoon Kim, Junmo Lee, Yeonjun In, Kanghoon Yoon, Chanyoung Park (2026). *A New DAWN for Fake News Detection: Exploiting Engagement Earliness for Temporality-aware Evaluation*. ACM Transactions on Intelligent Systems and Technology. https://doi.org/10.1145/3815193
7. Jay Prakash Maurya, Vivek Richhariya, Bhupesh Gour, V. K. Kumar (2024). *Implementation of Weight Adjusting GNN With Differentiable Pooling for User Preference-aware Fake News Detection*. Research Square. https://doi.org/10.21203/rs.3.rs-3942141/v1
8. Van-Hoang Nguyen, Kazunari Sugiyama, Preslav Nakov, Min-Yen Kan (2020). *FANG: Leveraging Social Context for Fake News Detection Using Graph Representation*. Proceedings of the 29th ACM International Conference on Information &amp; Knowledge Management. https://doi.org/10.1145/3340531.3412046
9. Huyen Trang Phan, Ngoc Thanh Nguyên, Dosam Hwang (2023). *Fake news detection: A survey of graph neural network methods*. Applied Soft Computing. https://doi.org/10.1016/j.asoc.2023.110235
10. Oleg Platonov, Denis Kuznedelev, Michael Diskin, Artem Babenko, Liudmila Prokhorenkova (2023). *A critical look at the evaluation of GNNs under heterophily: Are we really making progress?*. arXiv. https://arxiv.org/abs/2302.11640
11. Vandana Rai, Sakshi Rai (2025). *Exploring the Efficacy of Attention Mechanisms in GNN-Based Fake News Detection on UPFD Dataset*. Learning and analytics in intelligent systems. https://doi.org/10.1007/978-981-97-9855-1_7
12. Vandana Rai, Sakshi Rai (2025). *Leveraging Hypergraph Neural Network for Fake News Detection on UPFD Dataset*. Springer eBooks. https://doi.org/10.1007/978-981-96-4722-4_9
13. Long Dinh Tuan, Le Ngoc An, Duong Dinh Thai (2026). *Beyond Reported Accuracy: A Verifiability-Focused, Multi-Axis Review of Content and Context Based Fake News Detection*. Journal of Computing Theories and Applications. https://doi.org/10.62411/jcta.17476
14. Jiaying Wu, Bryan Hooi (2023). *DECOR: Degree-Corrected Social Graph Refinement for Fake News Detection*. ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD). https://doi.org/10.1145/3580305.3599298
15. Kaiyuan Xu (2025). *Enhancing Fake-News Detection with Node-Level Topological Features*. arXiv. https://arxiv.org/abs/2512.09974
