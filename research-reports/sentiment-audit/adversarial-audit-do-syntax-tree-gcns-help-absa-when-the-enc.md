# Adversarial audit: do syntax-tree GCNs help ABSA when the encoder is held fixed?

**Report type:** Research Opportunity Report  
**Generated:** 2026-10-18

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | Aspect-based sentiment analysis with dependency-graph neural networks | stated by user |
| experience | undergraduate, comfortable with Python | default (not stated by user) |
| hardware | one consumer GPU, 8 GB VRAM | default (not stated by user) |
| gpu vram gb | 8 | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| language | Python | default (not stated by user) |
| difficulty | moderate | default (not stated by user) |
| mode | any | default (not stated by user) |

## Summary

The question as posed is already answered: Dai et al. ran RoBERTa with and without ASGCN, PWCN and RGAT tree heads on the same SemEval data and found no significant gain ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)). What remains open is whether that null result, and the 2023-2026 claims of gains, survive a sound protocol: the closest codebases select models on the test set, a selection habit worth 1-2 points elsewhere in ABSA ([Mukherjee et al. 2021](https://doi.org/10.1007/978-3-030-72240-1_7)), about the size of every claimed syntax gain. A protocol-corrected replication with structure controls is a conditional go; a novel framing (frozen vs fine-tuned encoder) is plausible but unverified.

## Decisions

Each shortlisted research question gets go, conditional go or no-go. A go requires full-text reading of the closest work and an explicit check for leakage, weak baselines and evaluation flaws; anything short of that is at most a conditional go.

| Research question | Decision | Novelty confidence | Mode | Main conditions |
| --- | --- | --- | --- | --- |
| As stated: do syntax-tree GCNs help when the pretrained encoder is held fixed? | NO-GO | very_low | original | not reported |
| D1 (replication): protocol-corrected re-test of Dai et al.'s RoBERTa tree-head comparison | CONDITIONAL GO | low | replication | Read Lebmeier et al. through the library; if it already re-runs a syntax-GCN model with validation splits and uncertainty, narrow to the DeBERTa-v3 part or drop D1.; Fix the validation protocol, seeds and the smallest effect of interest (e. |
| D2 (extension): is it syntax, or just an extra graph head? Structure controls on a fixed fine-tuned encoder | CONDITIONAL GO | low | extension | Run D1 first so the baseline and protocol are trusted.; Screen ablation tables of the 5-10 most cited 2022-2026 syntax-GCN ABSA papers for random or chain-tree controls on PLMs. |
| D3 (novel investigation): frozen versus fine-tuned encoder - does syntax matter only when the encoder cannot adapt? | CONDITIONAL GO | low | original | Run a dedicated challenge and web search on frozen-encoder syntax probing (e.g. 'frozen BERT features dependency GCN') before committing. |
| D4 (extension): parser quality as the moderator of syntax gains in ABSA | NO-GO | low | extension | not reported |

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | verified: 13 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: abstract: 5, full text: 6, title only: 2; claims: estimate: 7, speculative: 2, verified: 35 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | As stated: do syntax-tree GCNs help when the pretrained encoder is held fixed?: very_low (search ceiling low); D1 (replication): protocol-corrected re-test of Dai et al.'s RoBERTa tree-head comparison: low (search ceiling low); D2 (extension): is it syntax, or just an extra graph head? Structure controls on a fixed fine-tuned encoder: low (search ceiling low); D3 (novel investigation): frozen versus fine-tuned encoder - does syntax matter only when the encoder cannot adapt?: low (search ceiling low); D4 (extension): parser quality as the moderator of syntax gains in ABSA: low (search ceiling low) | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## How the literature was searched

- **Sources that answered:** openalex, arxiv, crossref, huggingface
- **Sources that failed or were skipped:** semantic_scholar (rate_limited)
- **Search strategies:** challenge with design elements and seed (arXiv 2104.04986), citation expansion, web search, full-text reading (fulltext command), code reading, data leakage check
- **Date range:** unrestricted
- **Records retrieved / after deduplication:** 372 / None
- **Search date:** 2026-10-18
- **Queries:** `does syntax help pretrained transformers aspect-based sentiment`; `dependency tree graph neural network on top of BERT ablation sentiment`; `syntactic information unnecessary strong RoBERTa baseline aspect sentiment`; `syntax-agnostic versus syntax-aware models frozen encoder probing`; `random trees versus dependency trees graph convolution evaluation`; `web: does syntax help pretrained transformers dependency tree GNN ablation aspect-based sentiment random trees`; `web: aspect-based sentiment GCN reproducibility seeds variance same encoder syntax benefit`; `web: aspect sentiment random tree / fully connected graph replace dependency tree GCN ablation BERT`; `web: empirical study syntax ABSA pre-trained language models revisiting`; `web: ABSA evaluation model selection on test set no development set reproducibility`
- Reused from the NLP+GNN opportunity report: candidate O2, its challenge (work/challenge_absa.json), references and dataset checks.
- The challenge returned no_close_match_in_this_search and flagged an unrelated pharmacy paper on the design element 'frozen pretrained encoder'; Sachan et al., Mukherjee et al. and Lebmeier et al. were found by web search.
- Full texts read via arXiv source: 2104.04986, 2008.09084, 2101.09449, 2110.00171, 2103.04350 (targeted), 2311.04467 (targeted). Lebmeier et al. is behind a publisher login (institutional copy is a viewer link).
- Code read: RoBERTaABSA (finetune.py, ASGCN/train.py, data_utils.py, args and logs), GeneZC/ASGCN train.py, shenwzh3/RGAT-ABSA run.py and trainer.py.

## What has already been done

| Paper | Published | Method | Datasets | Findings | Stated limitations | Read | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Does syntax matter? A strong baseline for Aspect-based Sentiment Analysis with RoBERTa (Dai et al. 2021) | 2021 | Compares parser trees, PTM-induced trees, FT-PTM-induced trees and left/right-chain trees inside ASGCN, PWCN and RGAT; RoBERTa with an MLP head as baseline | Rest14, Laptop14, Twitter; three SemEval-2016 non-English sets | Full text: tree-structure comparison uses GloVe embeddings, 3 runs. SOTA table: RoBERTa-MLP 87.37/83.78 accuracy (Rest14/Laptop14) vs RoBERTa+ASGCN, PWCN, RGAT with parser or FT-RoBERTa trees between 86.87 and 87.52 (Rest14) and 81.66-84.16 (Laptop14); text: 'incorporating trees over the RoBERTa brings no significant improvement'. No variance reported for that table. | Code (README): released logs are single runs; finetune.py uses the test set as dev for model selection; released tree-model code uses GloVe only, so the RoBERTa+tree rows cannot be re-run from the repository; no licence | full text | [link](https://doi.org/10.18653/v1/2021.naacl-main.146) |
| Do Syntax Trees Help Pre-trained Transformers Extract Information? (Sachan et al. 2020) | 2020-08-20 | Syntax-GNN over BERT outputs (late fusion) and syntax inside attention (joint fusion); same encoder with and without dependency trees; gold vs in-domain vs off-the-shelf parses | CoNLL-2005/2012 SRL, OntoNotes NER, TACRED-style RE | Full text: 5 runs; gains on SRL (>2.5 F1) only with gold parses, contingent on parse quality; no gain on NER (within one standard deviation of bert-base); late-fusion gains of about 2 F1 also with RoBERTa when gold parses are used | Information extraction, not sentiment; encoder always fine-tuned | full text | [link](https://arxiv.org/abs/2008.09084) |
| Reproducibility, Replicability and Beyond: Assessing Production Readiness of Aspect Based Sentiment Analysis in the Wild (Mukherjee et al. 2021) | 2021 | Re-runs six ABSA models (memory-network and BERT-based) with test-set model selection vs a 15% held-out split from training | SemEval-2014 Laptop and Restaurant; two new e-commerce datasets | Full text: reproduced accuracy 1-2 points below reported; a further 1-2 point drop when model selection uses a held-out split instead of the test set; 5 runs | No syntax or GCN models among the six | full text | [link](https://doi.org/10.1007/978-3-030-72240-1_7) |
| On the Current State of Reproducibility and Reporting of Uncertainty for Aspect-Based Sentiment Analysis (Lebmeier et al. 2023) | 2023-01-01 | Holistic comparison of six (near) state-of-the-art transformer-based ABSA architectures with fixed preprocessing, train/validation splits, metrics and uncertainty quantification | Five public benchmark datasets | Abstract: reported results are hardly reproducible; results vary notably across data splits, so uncertainty must be reported | Full text behind publisher login; the six architectures are not named in the abstract | abstract | [link](https://doi.org/10.1007/978-3-031-26390-3_31) |
| BERT4GCN: Using BERT Intermediate Layers to Augment GCN for Aspect-based Sentiment Classification (Xiao et al. 2021) | 2021 | GCN over dependency graphs supplemented with BERT intermediate-layer features and relative positions | Twitter, Laptop14, Rest14 | Full text: ablation shows GCN over BERT sequential features without the supplemented dependency graph already reaches state-of-the-art and the graph adds 'just slightly'; its RoBERTa-MLP baseline is 81.11 on Laptop14 (Dai et al. report 83.78); averages over 10 runs ('10-fold') | Model-selection protocol not stated in the text read | full text | [link](https://doi.org/10.18653/v1/2021.emnlp-main.724) |
| Syntax-BERT: Improving Pre-trained Transformers with Syntax Trees (Bai et al. 2021) | 2021 | Syntax-tree masks inside pre-trained transformers; ablation replaces syntactic masks with random masks of equal parameter size | GLUE-style sentence classification tasks | Full text (targeted passages): a random decomposition of the network also gives moderate improvements | Not ABSA; random-mask numbers not extracted here | full text | [link](https://doi.org/10.18653/v1/2021.eacl-main.262) |
| RDGCN: Reinforced Dependency Graph Convolutional Network for Aspect-based Sentiment Analysis (Zhao et al. 2023) | 2023-11-08 | Reinforced dependency GCN with RL-tuned distance-importance function | not reported | Full text (targeted passages): 'Since the datasets do not contain the validation set, the test accuracy is used to implement the reward function' | Test labels enter training through the RL reward | full text | [link](https://arxiv.org/abs/2311.04467) |
| Selective Attention Based Graph Convolutional Networks for Aspect-Level Sentiment Classification (Hou et al. 2021) | 2021 | Selective-attention GCN over dependency trees on BERT | not reported | Web-search snippet (not verified against text): BERT baselines with 2- and 4-layer GCN, 7-run averages | arXiv source contains only the supplement; main text not read | abstract | [link](https://doi.org/10.18653/v1/2021.textgraphs-1.8) |
| Aspect-based Sentiment Classification with Aspect-specific Graph Convolutional Networks (Zhang et al. 2019) | 2019 | Aspect-specific GCN over dependency trees (GloVe/LSTM) | not reported | not reported | not reported | abstract | [link](https://doi.org/10.18653/v1/d19-1464) |
| Relational Graph Attention Network for Aspect-based Sentiment Analysis (Wang et al. 2020) | 2020 | Relational graph attention over aspect-oriented dependency trees | not reported | not reported | Official code (MIT) selects the best epoch on the test set (run.py, trainer.py) | abstract | [link](https://doi.org/10.18653/v1/2020.acl-main.295) |
| FITE-GAT: Enhancing aspect-level sentiment classification with FT-RoBERTa induced trees and graph attention network (Fan et al. 2024) | 2024-11-23 | Title: FT-RoBERTa induced trees with graph attention; abstract not retrieved | not reported | not reported | not reported | title only | [link](https://doi.org/10.1016/j.eswa.2024.125890) |
| Syntax-Enhanced Pretrained Language Models for Aspect-Level Sentiment Classification (Li et al. 2024) | 2024-12-24 | SE-BERT: syntax-enhanced transformer layers replacing BERT's final layers | not reported | Abstract states that existing methods improve aspect-level sentiment classification by adding syntactic GCN layers on BERT | not reported | abstract | [link](https://doi.org/10.1109/tcss.2024.3514901) |
| Multi-View Attention Syntactic Enhanced Graph Convolutional Network for Aspect-based Sentiment Analysis (Huang et al. 2025) | 2025-01-27 | Multi-view attention syntactic enhanced GCN for ABSA | not reported | Example of continued dependency-GCN ABSA work after 2021 | not reported | title only | [link](https://arxiv.org/abs/2501.15968) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

### Directions that are already well explored

- [E] New dependency-GCN architectures on SemEval-2014 (many 2022-2026 papers; titles screened) ([Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901); [Zhao et al. 2023](https://arxiv.org/abs/2311.04467))
- [V] On Rest14 and Laptop14, RoBERTa+tree heads lie within about +/-1.1 (Rest14) and -2.1 to +0.4 (Laptop14) accuracy points of RoBERTa-MLP, with no variance reported. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146))
- [V] Whether syntax helps fine-tuned transformers on information extraction ([Sachan et al. 2020](https://arxiv.org/abs/2008.09084))
- [V] Reproducibility of ABSA results in general ([Mukherjee et al. 2021](https://doi.org/10.1007/978-3-030-72240-1_7))

## Ranked research opportunities

Each opportunity below survived an explicit search for work that already addresses it. None is claimed to be novel: the novelty confidence states how far the search supports the gap, and what it could have missed.

### 1. D1 (replication): protocol-corrected re-test of Dai et al.'s RoBERTa tree-head comparison
**Type of gap:** Limitation reported in prior work  
**Recommended mode:** replication  
**Revised:** Narrowed from the original question after the full texts showed the comparison exists but was run with test-set model selection, without variance and without released code for the RoBERTa+tree rows.

**Research question.** On the shipped SemEval-2014 Laptop and Restaurant splits, does the reported null result (no gain from tree heads on RoBERTa) survive validation-based model selection, a tuned baseline and 10+ seeds, and does it hold for DeBERTa-v3-base?

**Motivation.** The headline null result is cited as settled but rests on test-selected, single-table numbers ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)).

**Supporting papers.** ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Mukherjee et al. 2021](https://doi.org/10.1007/978-3-030-72240-1_7); [Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31))

**Closest existing work.**
- ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) [read: full text; overlap: same experiment]: The study being replicated; the replication changes the protocol, not the question.
- ([Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31)) [read: abstract; overlap: unknown]: Re-runs six transformer ABSA architectures with validation splits and uncertainty; whether any is a syntax-GCN model is unknown.
- ([Mukherjee et al. 2021](https://doi.org/10.1007/978-3-030-72240-1_7)) [read: full text; overlap: partial]: Quantifies test-selection inflation, but for memory-network and BERT models, not tree heads.

**Evidence for the gap.**
- [V] On Rest14 and Laptop14, RoBERTa+tree heads lie within about +/-1.1 (Rest14) and -2.1 to +0.4 (Laptop14) accuracy points of RoBERTa-MLP, with no variance reported. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146))
- [V] Official code of the closest studies selects on the test set: RoBERTaABSA finetune.py passes the test split as dev_data and reloads the best model; ASGCN (original and Dai et al.'s copy) keeps max_test_acc and max_test_f1 separately, so accuracy and F1 can come from different epochs; RGAT run.py reports the best evaluation on the test set. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464); [Wang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.295))
- [V] Selecting on a 15% held-out split instead of the test set costs a further 1-2 accuracy points for six non-syntax ABSA models, about the size of the claimed syntax gains. ([Mukherjee et al. 2021](https://doi.org/10.1007/978-3-030-72240-1_7))
- [V] The same RoBERTa-MLP baseline is reported at 83.78 (Dai et al.) and 81.11 (BERT4GCN) on Laptop14, so cross-paper syntax gains can be baseline artefacts. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724))

**Potential contribution.** A checked, variance-aware answer to a question the field treats as settled; either outcome is reportable.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). Replication value, not novelty. Lebmeier et al.'s architectures are unknown; a paywalled or non-English replication could exist.
Attempts to disprove novelty: 10 search(es); signal `no_close_match_in_this_search`. Queries: `does syntax help pretrained transformers aspect-based sentiment`; `dependency tree graph neural network on top of BERT ablation sentiment`; `syntactic information unnecessary strong RoBERTa baseline aspect sentiment`; `syntax-agnostic versus syntax-aware models frozen encoder probing`; `random trees versus dependency trees graph convolution evaluation`; `web: does syntax help pretrained transformers dependency tree GNN ablation aspect-based sentiment random trees`; `web: aspect-based sentiment GCN reproducibility seeds variance same encoder syntax benefit`; `web: aspect sentiment random tree / fully connected graph replace dependency tree GCN ablation BERT`

**Feasibility.**
- [V] Shipped splits and pre-parsed dependency trees (head, deprel fields) are in the RoBERTaABSA repository; RoBERTa-base and DeBERTa-v3-base are MIT-licensed on Hugging Face.
- [E] About 3,600 training aspects; base encoders at batch 16 fit 8 GB with mixed precision; roughly 2 datasets x 2 encoders x 3 heads x 10 seeds = 120 short runs, about 15-30 GPU-hours.
- [V] Tree heads must be reimplemented on current transformers (repository pins transformers 2.11, PyTorch 1.5, fastNLP).

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| model selection on test | found | [V] Official code of the closest studies selects on the test set: RoBERTaABSA finetune.py passes the test split as dev_data and reloads the best model; ASGCN (original and Dai et al.'s copy) keeps max_test_acc and max_test_f1 separately, so accuracy and F1 can come from different epochs; RGAT run.py reports the best evaluation on the test set. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464); [Wang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.295)) | Validation split carved from training, grouped by sentence; select checkpoints and hyperparameters on it only; touch the test set once. |
| metric definition | found | [V] ASGCN reports maximum accuracy and maximum F1 from possibly different epochs. ([Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464)) | Report accuracy and macro-F1 of one selected checkpoint. |
| insufficient runs | found | [V] Dai et al.: 3 runs for the tree comparison, no variance for the RoBERTa table, released logs single-run; Lebmeier et al. report notable variance across data splits. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31)) | At least 10 seeds x repeated train/validation splits; paired comparisons; confidence intervals. |
| weak baseline | found | [V] The same RoBERTa-MLP baseline is reported at 83.78 (Dai et al.) and 81.11 (BERT4GCN) on Laptop14, so cross-paper syntax gains can be baseline artefacts. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)) | Tune the plain-encoder baseline with the same budget and search space as the tree heads. |
| protocol mismatch | found | [V] No public code for the RoBERTa+tree rows; the Hugging Face SetFit copy has 654 laptop test rows vs 638 aspects in the shipped split. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | Use the shipped split files; reimplement heads on one codebase; label the work a replication. |
| confound | not checked | Tree heads add parameters and a separate learning rate; Dai et al. note RoBERTa-based tree models are hard to optimise and need different learning rates. | Parameter-matched no-graph head with the same tuning budget. |
| duplicate items | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| train test overlap | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| pretraining contamination | not checked | SemEval-2014 reviews have been public since 2014 and may be in RoBERTa/DeBERTa pre-training data; this affects both arms of a with/without-syntax comparison alike. | not reported |

**Decision: CONDITIONAL GO.** Feasible and useful as a replication; novelty is low by design.

**Conditions before committing.**
- Read Lebmeier et al. through the library; if it already re-runs a syntax-GCN model with validation splits and uncertainty, narrow to the DeBERTa-v3 part or drop D1.
- Fix the validation protocol, seeds and the smallest effect of interest (e.g. 1 point) before any run.

**Unresolved evidence and risks.**
- Lebmeier et al. unread
- Reimplementation may not match Dai et al.'s unreleased RoBERTa+tree code

### 2. D2 (extension): is it syntax, or just an extra graph head? Structure controls on a fixed fine-tuned encoder
**Type of gap:** Underexplored experimental setting  
**Recommended mode:** extension

**Research question.** With the encoder and head parameter count fixed, do dependency trees beat left/right-chain, degree-matched random trees and a fully connected graph inside the same GCN head?

**Motivation.** Dai et al. ran chain-tree controls only with GloVe models ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)); random masks also help in Syntax-BERT ([Bai et al. 2021](https://doi.org/10.18653/v1/2021.eacl-main.262)); BERT4GCN's graph adds only slightly ([Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)).

**Supporting papers.** ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Bai et al. 2021](https://doi.org/10.18653/v1/2021.eacl-main.262); [Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724))

**Closest existing work.**
- ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) [read: full text; overlap: partial]: Chain-tree controls with GloVe embeddings only, 3 runs.
- ([Bai et al. 2021](https://doi.org/10.18653/v1/2021.eacl-main.262)) [read: full text; overlap: partial]: Random-mask control inside the transformer, GLUE tasks, not ABSA.
- ([Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)) [read: full text; overlap: partial]: Removes the dependency graph but has no random or chain-tree control.
- ([Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31)) [read: abstract; overlap: unknown]: Unknown architectures; unlikely to include structure controls.

**Evidence for the gap.**
- [V] Chain-tree controls in Dai et al. use 300-d GloVe embeddings kept fixed, not a pretrained encoder. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146))
- [V] A random decomposition of the network also gives moderate improvements (Syntax-BERT, GLUE). ([Bai et al. 2021](https://doi.org/10.18653/v1/2021.eacl-main.262))

**Potential contribution.** Separates the effect of syntax from that of adding any graph-structured head.

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). No ABSA paper with random/chain-tree controls on a pretrained encoder was found in the full texts read or by web search; ablation tables of the many 2022-2026 GCN papers were not all read and may contain such controls.
Attempts to disprove novelty: 10 search(es); signal `no_close_match_in_this_search`. Queries: `does syntax help pretrained transformers aspect-based sentiment`; `dependency tree graph neural network on top of BERT ablation sentiment`; `syntactic information unnecessary strong RoBERTa baseline aspect sentiment`; `syntax-agnostic versus syntax-aware models frozen encoder probing`; `random trees versus dependency trees graph convolution evaluation`; `web: does syntax help pretrained transformers dependency tree GNN ablation aspect-based sentiment random trees`; `web: aspect-based sentiment GCN reproducibility seeds variance same encoder syntax benefit`; `web: aspect sentiment random tree / fully connected graph replace dependency tree GCN ablation BERT`

**Feasibility.** [E] Same pipeline as D1 plus graph generators; adds about 40 runs.

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| model selection on test | found | [V] Official code of the closest studies selects on the test set: RoBERTaABSA finetune.py passes the test split as dev_data and reloads the best model; ASGCN (original and Dai et al.'s copy) keeps max_test_acc and max_test_f1 separately, so accuracy and F1 can come from different epochs; RGAT run.py reports the best evaluation on the test set. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464); [Wang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.295)) | Validation split carved from training, grouped by sentence; select checkpoints and hyperparameters on it only; touch the test set once. |
| metric definition | found | [V] ASGCN reports maximum accuracy and maximum F1 from possibly different epochs. ([Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464)) | Report accuracy and macro-F1 of one selected checkpoint. |
| insufficient runs | found | [V] Dai et al.: 3 runs for the tree comparison, no variance for the RoBERTa table, released logs single-run; Lebmeier et al. report notable variance across data splits. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31)) | At least 10 seeds x repeated train/validation splits; paired comparisons; confidence intervals. |
| weak baseline | found | [V] The same RoBERTa-MLP baseline is reported at 83.78 (Dai et al.) and 81.11 (BERT4GCN) on Laptop14, so cross-paper syntax gains can be baseline artefacts. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)) | Tune the plain-encoder baseline with the same budget and search space as the tree heads. |
| protocol mismatch | found | [V] No public code for the RoBERTa+tree rows; the Hugging Face SetFit copy has 654 laptop test rows vs 638 aspects in the shipped split. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | Use the shipped split files; reimplement heads on one codebase; label the work a replication. |
| confound | not checked | Tree heads add parameters and a separate learning rate; Dai et al. note RoBERTa-based tree models are hard to optimise and need different learning rates. | Parameter-matched no-graph head with the same tuning budget. |
| duplicate items | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| train test overlap | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| pretraining contamination | not checked | SemEval-2014 reviews have been public since 2014 and may be in RoBERTa/DeBERTa pre-training data; this affects both arms of a with/without-syntax comparison alike. | not reported |

**Decision: CONDITIONAL GO.** The most informative design: it tests the mechanism, and runs on D1's pipeline.

**Conditions before committing.**
- Run D1 first so the baseline and protocol are trusted.
- Screen ablation tables of the 5-10 most cited 2022-2026 syntax-GCN ABSA papers for random or chain-tree controls on PLMs.

**Unresolved evidence and risks.**
- Uncited ablations in recent GCN papers
- Effect sizes may be below the detectable difference on 638/1,120 test aspects

### 3. D3 (novel investigation): frozen versus fine-tuned encoder - does syntax matter only when the encoder cannot adapt?
**Type of gap:** Unverified novelty hypothesis  
**Recommended mode:** original

**Research question.** When the encoder is frozen (features only), do dependency-tree heads give larger gains over a parameter-matched no-graph head than when it is fine-tuned?

**Motivation.** Every closest study fine-tunes the encoder ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Sachan et al. 2020](https://arxiv.org/abs/2008.09084)); Dai et al. argue fine-tuning makes the encoder learn task-oriented structure implicitly.

**Supporting papers.** ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Sachan et al. 2020](https://arxiv.org/abs/2008.09084))

**Closest existing work.**
- ([Sachan et al. 2020](https://arxiv.org/abs/2008.09084)) [read: full text; overlap: partial]: Fine-tuned encoders only, information extraction tasks.
- ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) [read: full text; overlap: partial]: Fine-tuned RoBERTa only; frozen GloVe for the tree comparison.
- ([Hou et al. 2021](https://doi.org/10.18653/v1/2021.textgraphs-1.8)) [read: abstract; overlap: unknown]: BERT + GCN depth variants; encoder regime not read.

**Evidence for the gap.**
- [V] The closest full texts fine-tune the encoder in every syntax comparison. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Sachan et al. 2020](https://arxiv.org/abs/2008.09084))
- [S] If fine-tuning lets the encoder absorb task structure, a frozen encoder should leave more room for explicit syntax.

**Potential contribution.** Identifies when explicit syntax is worth adding (compute-limited, frozen-feature settings).

**Novelty confidence:** low (scale: very_low, low, medium; a search cannot establish more). Unverified hypothesis: probing and adapter literature with frozen encoders was not searched in depth.
Attempts to disprove novelty: 10 search(es); signal `no_close_match_in_this_search`. Queries: `does syntax help pretrained transformers aspect-based sentiment`; `dependency tree graph neural network on top of BERT ablation sentiment`; `syntactic information unnecessary strong RoBERTa baseline aspect sentiment`; `syntax-agnostic versus syntax-aware models frozen encoder probing`; `random trees versus dependency trees graph convolution evaluation`; `web: does syntax help pretrained transformers dependency tree GNN ablation aspect-based sentiment random trees`; `web: aspect-based sentiment GCN reproducibility seeds variance same encoder syntax benefit`; `web: aspect sentiment random tree / fully connected graph replace dependency tree GCN ablation BERT`

**Feasibility.** [E] Frozen features can be cached once; cheapest of all designs (CPU-trainable heads).

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| model selection on test | found | [V] Official code of the closest studies selects on the test set: RoBERTaABSA finetune.py passes the test split as dev_data and reloads the best model; ASGCN (original and Dai et al.'s copy) keeps max_test_acc and max_test_f1 separately, so accuracy and F1 can come from different epochs; RGAT run.py reports the best evaluation on the test set. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464); [Wang et al. 2020](https://doi.org/10.18653/v1/2020.acl-main.295)) | Validation split carved from training, grouped by sentence; select checkpoints and hyperparameters on it only; touch the test set once. |
| metric definition | found | [V] ASGCN reports maximum accuracy and maximum F1 from possibly different epochs. ([Zhang et al. 2019](https://doi.org/10.18653/v1/d19-1464)) | Report accuracy and macro-F1 of one selected checkpoint. |
| insufficient runs | found | [V] Dai et al.: 3 runs for the tree comparison, no variance for the RoBERTa table, released logs single-run; Lebmeier et al. report notable variance across data splits. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Lebmeier et al. 2023](https://doi.org/10.1007/978-3-031-26390-3_31)) | At least 10 seeds x repeated train/validation splits; paired comparisons; confidence intervals. |
| weak baseline | found | [V] The same RoBERTa-MLP baseline is reported at 83.78 (Dai et al.) and 81.11 (BERT4GCN) on Laptop14, so cross-paper syntax gains can be baseline artefacts. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146); [Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)) | Tune the plain-encoder baseline with the same budget and search space as the tree heads. |
| protocol mismatch | found | [V] No public code for the RoBERTa+tree rows; the Hugging Face SetFit copy has 654 laptop test rows vs 638 aspects in the shipped split. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | Use the shipped split files; reimplement heads on one codebase; label the work a replication. |
| confound | not checked | Tree heads add parameters and a separate learning rate; Dai et al. note RoBERTa-based tree models are hard to optimise and need different learning rates. | Parameter-matched no-graph head with the same tuning budget. |
| duplicate items | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| train test overlap | checked ok | [V] Shipped splits (Laptop 2328/638, Restaurants 3608/1120 aspects, matching Dai et al.'s statistics): one exact duplicate sentence per dataset, same label; an aspect-term vote reaches 52.5% vs majority 53.4% (Laptop) and 65.4% vs 65.0% (Restaurants), so no aspect-identity shortcut. ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)) | not reported |
| pretraining contamination | not checked | SemEval-2014 reviews have been public since 2014 and may be in RoBERTa/DeBERTa pre-training data; this affects both arms of a with/without-syntax comparison alike. | not reported |

**Decision: CONDITIONAL GO.** Plausible and cheap, but the novelty rests on absence of evidence.

**Conditions before committing.** Run a dedicated challenge and web search on frozen-encoder syntax probing (e.g. 'frozen BERT features dependency GCN') before committing.

**Unresolved evidence and risks.** Probing literature may already answer it

### Candidates rejected after the novelty challenge

- **As stated: do syntax-tree GCNs help when the pretrained encoder is held fixed?** (Already well studied): Already performed: Dai et al. compare RoBERTa-MLP with RoBERTa+ASGCN/PWCN/RGAT using parser and induced trees and conclude that trees bring no significant improvement ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146)); BERT4GCN's own ablation finds the dependency graph adds only slightly ([Xiao et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.724)); and the same comparison under identical encoders is done in information extraction ([Sachan et al. 2020](https://arxiv.org/abs/2008.09084)).
- **D4 (extension): parser quality as the moderator of syntax gains in ABSA** (Underexplored experimental setting): Sachan et al. show gains depend on gold parses ([Sachan et al. 2020](https://arxiv.org/abs/2008.09084)); SemEval reviews have no gold dependency trees, so parse quality cannot be measured against a reference and the moderator cannot be isolated.

## Feasibility ranking

Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any blocker removes a candidate from the ranking no matter how high its other scores are. Novelty is capped at 2 unless the closest prior work was read in full, and at 1 when that work already ran the experiment.

| Rank | Candidate | Status | Score % | Range | Scored weight % | Verified weight % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | D1 replication: protocol-corrected re-test | VIABLE | 71.8 | 71.8-71.8 | 100.0 | 61.0 |
| 2 | D3 novel: frozen vs fine-tuned encoder | VIABLE | 68.2 | 68.2-68.2 | 100.0 | 30.0 |
| 3 | D2 extension: structure controls | VIABLE | 64.6 | 64.6-64.6 | 100.0 | 37.0 |
| 4 | D4 parser-quality moderator | VIABLE | 53.8 | 53.8-53.8 | 100.0 | 49.0 |

**Scores per criterion (0-5).**

| Criterion | Weight | D1 | D3 | D2 | D4 |
| --- | --- | --- | --- | --- | --- |
| scientific relevance | 12 | 4 [V] | 3 [S] | 4 [E] | 2 [V] |
| novelty or replication value | 12 | 4 [V] | 3 [E] | 3 [E] | 2 [E] |
| paper and code availability | 10 | 3 [V] | 3 [V] | 3 [V] | 3 [V] |
| dataset accessibility | 12 | 3 [V] | 3 [V] | 3 [V] | 3 [V] |
| compute fit | 12 | 4 [E] | 4 [E] | 4 [E] | 4 [E] |
| implementation simplicity | 10 | 3 [E] | 4 [E] | 3 [E] | 3 [E] |
| time fit | 10 | 4 [E] | 5 [E] | 3 [E] | 4 [E] |
| reproducibility | 8 | 2 [V] | 2 [V] | 2 [V] | 2 [V] |
| evaluation clarity | 7 | 4 [V] | 3 [E] | 3 [V] | 1 [V] |
| low failure risk | 7 | 5 [E] | 4 [E] | 4 [E] | 2 [E] |

**D1 replication: protocol-corrected re-test**
- scientific relevance: Null result is cited as settled; claims of gains continue ([Li et al. 2024](https://doi.org/10.1109/tcss.2024.3514901))
- novelty or replication value: Single-table, test-selected result that many papers rely on ([Dai et al. 2021](https://doi.org/10.18653/v1/2021.naacl-main.146))
- paper and code availability: Papers open; tree-head code GloVe-only, pinned to 2020 libraries
- dataset accessibility: Shipped splits with parses; counts match the paper
- compute fit: Base encoders, ~3.6k training aspects
- implementation simplicity: Reimplement heads on current transformers
- time fit: About 4 weeks
- reproducibility: Test-set selection, few runs, missing RoBERTa+tree code
- evaluation clarity: Standard metrics, published numbers to compare
- low failure risk: Either outcome reportable
- Missing: dataset_accessibility: No licence

**D3 novel: frozen vs fine-tuned encoder**
- scientific relevance: Relevant to compute-limited practice
- novelty or replication value: Not found in the closest full texts
- paper and code availability: Papers open; tree-head code GloVe-only, pinned to 2020 libraries
- dataset accessibility: Shipped splits with parses; counts match the paper
- compute fit: Base encoders, ~3.6k training aspects
- implementation simplicity: Cached features, small heads
- time fit: About 4 weeks
- reproducibility: Test-set selection, few runs, missing RoBERTa+tree code
- evaluation clarity: No published numbers
- low failure risk: Either outcome reportable
- Missing: novelty_or_replication_value: Probing literature unsearched
- Missing: dataset_accessibility: No licence

**D2 extension: structure controls**
- scientific relevance: Tests the mechanism behind a large literature
- novelty or replication value: No PLM structure controls found in the full texts read
- paper and code availability: Papers open; tree-head code GloVe-only, pinned to 2020 libraries
- dataset accessibility: Shipped splits with parses; counts match the paper
- compute fit: Base encoders, ~3.6k training aspects
- implementation simplicity: Graph generators on D1 pipeline
- time fit: 6 weeks including D1
- reproducibility: Test-set selection, few runs, missing RoBERTa+tree code
- evaluation clarity: No published numbers for the controls
- low failure risk: Null or positive both informative
- Missing: novelty_or_replication_value: Recent ablation tables unread
- Missing: dataset_accessibility: No licence

**D4 parser-quality moderator**
- scientific relevance: Shown for IE ([Sachan et al. 2020](https://arxiv.org/abs/2008.09084))
- novelty or replication value: Moderator not isolable without gold parses
- paper and code availability: Papers open; tree-head code GloVe-only, pinned to 2020 libraries
- dataset accessibility: Shipped splits with parses; counts match the paper
- compute fit: Base encoders, ~3.6k training aspects
- implementation simplicity: Multiple parsers
- time fit: 5 weeks
- reproducibility: Test-set selection, few runs, missing RoBERTa+tree code
- evaluation clarity: No gold trees for review data
- low failure risk: Likely inconclusive
- Missing: dataset_accessibility: No licence

## Candidate datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [SemEval-2014 Laptop and Restaurant splits shipped with RoBERTaABSA](https://github.com/ROGERDJQ/RoBERTaABSA/tree/main/Dataset) | All designs (reference split) | Laptop 2,328/638 aspects; Restaurants 3,608/1,120 (counted from Train/Test.json) | JSON with tokens, POS, dependency heads and relations; original XML | not reported | reachable (HTTP 200) | Conflict polarities removed; parses precomputed | Matches Dai et al.'s statistics exactly; repository has no licence | yes |
| [SemEval-2014 restaurants (SetFit copy)](https://huggingface.co/datasets/tomaarsen/setfit-absa-semeval-restaurants) | Not recommended for comparison | 3,693 / 1,134 rows | parquet | not reported | open, not gated | not reported | Row counts differ from the published split (laptop copy: 654 test rows vs 638 aspects) | yes |
| [SemEval-2014 laptops (SetFit copy)](https://huggingface.co/datasets/tomaarsen/setfit-absa-semeval-laptops) | Not recommended for comparison | 2,358 / 654 rows | parquet | not reported | open, not gated | not reported | As above | yes |

## Recommendation

- [E] No-go for the question as stated, and for the parser-quality variant.
- [E] Conditional go for D1 followed by D2 as one 6-8 week project: replicate the RoBERTa tree-head comparison with validation-based selection and 10+ seeds, then add chain, random and fully connected graph controls with matched parameters.
- [E] First action, no compute: read Lebmeier et al. through the library and screen ablation tables of the most cited 2022-2026 syntax-GCN papers for structure controls.
- [S] D3 (frozen encoder) is the only design with a novel framing; check the probing literature first.

## Limitations of this report

- Lebmeier et al. (2023) was not read beyond its abstract; it may already contain part of D1.
- The ablation tables of most 2022-2026 syntax-GCN ABSA papers were not read; D2's controls may exist there.
- Semantic Scholar was rate-limited; the challenge command did not retrieve three of the closest papers, which were found by web search.
- Compute and time figures are estimates; no model was trained and no code was run beyond data checks.
- SemEval-2014 data licence is not stated on any copy checked.

## References

1. Jiangang Bai, Yujing Wang, Yiren Chen, Yaming Yang, Jing Bai, Jing Yu et al. (2021). *Syntax-BERT: Improving Pre-trained Transformers with Syntax Trees*. Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics: Main Volume. https://doi.org/10.18653/v1/2021.eacl-main.262
2. Junqi Dai, Hang Yan, Tianxiang Sun, Peng-Fei Liu, Xipeng Qiu (2021). *Does syntax matter? A strong baseline for Aspect-based Sentiment Analysis with RoBERTa*. Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. https://doi.org/10.18653/v1/2021.naacl-main.146
3. Mengmeng Fan, Mingming Kong, Xi Wang, Fei Hao, Chao Zhang (2024). *FITE-GAT: Enhancing aspect-level sentiment classification with FT-RoBERTa induced trees and graph attention network*. Expert Systems with Applications. https://doi.org/10.1016/j.eswa.2024.125890
4. Xiaochen Hou, Jing Huang, Guangtao Wang, Xiaodong He, Bowen Zhou (2021). *Selective Attention Based Graph Convolutional Networks for Aspect-Level Sentiment Classification*. Proceedings of the Fifteenth Workshop on Graph-Based Methods for Natural Language Processing (TextGraphs-15). https://doi.org/10.18653/v1/2021.textgraphs-1.8
5. Xiang Huang, Hao Peng, Shuo Sun, Zhifeng Hao, Hui Lin, Shuhai Wang (2025). *Multi-View Attention Syntactic Enhanced Graph Convolutional Network for Aspect-based Sentiment Analysis*. arXiv. https://arxiv.org/abs/2501.15968
6. Elisabeth Lebmeier, Matthias Aßenmacher, Christian Heumann (2023). *On the Current State of Reproducibility and Reporting of Uncertainty for Aspect-Based Sentiment Analysis*. Lecture notes in computer science. https://doi.org/10.1007/978-3-031-26390-3_31
7. Yuan Li, Jin Wang, Lung‐Hao Lee, Xuejie Zhang (2024). *Syntax-Enhanced Pretrained Language Models for Aspect-Level Sentiment Classification*. IEEE Transactions on Computational Social Systems. https://doi.org/10.1109/tcss.2024.3514901
8. Rajdeep Mukherjee, Shreyas Shetty, Subrata Chattopadhyay, Subhadeep Maji, Samik Datta, Pawan Goyal (2021). *Reproducibility, Replicability and Beyond: Assessing Production Readiness of Aspect Based Sentiment Analysis in the Wild*. Lecture Notes in Computer Science Advances in Information Retrieval. https://doi.org/10.1007/978-3-030-72240-1_7
9. Devendra Singh Sachan, Yuhao Zhang, Peng Qi, William Hamilton (2020). *Do Syntax Trees Help Pre-trained Transformers Extract Information?*. arXiv. https://arxiv.org/abs/2008.09084
10. Kai Wang, Weizhou Shen, Yunyi Yang, Xiaojun Quan, Rui Wang (2020). *Relational Graph Attention Network for Aspect-based Sentiment Analysis*. Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. https://doi.org/10.18653/v1/2020.acl-main.295
11. Zeguan Xiao, Jiarun Wu, Qingliang Chen, Congjian Deng (2021). *BERT4GCN: Using BERT Intermediate Layers to Augment GCN for Aspect-based Sentiment Classification*. Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing. https://doi.org/10.18653/v1/2021.emnlp-main.724
12. Chen Zhang, Qiuchi Li, Dawei Song (2019). *Aspect-based Sentiment Classification with Aspect-specific Graph Convolutional Networks*. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP). https://doi.org/10.18653/v1/d19-1464
13. Xusheng Zhao, Hao Peng, Qiong Dai, Xu Bai, Huailiang Peng, Yanbing Liu et al. (2023). *RDGCN: Reinforced Dependency Graph Convolutional Network for Aspect-based Sentiment Analysis*. arXiv. https://arxiv.org/abs/2311.04467
