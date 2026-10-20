# Brightest stars: do question clusters or upvotes better show what a lecture class needs answered?

> **DRAFT: 0 integrity error(s) and 1 warning(s) were reported by the validator.** Unverified references are marked in the reference list.

**Report type:** Research Proposal  
**Generated:** 2026-10-19

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | educational technology, HCI and NLP | stated by user |
| project | starry-sky live question app | stated by user |
| hardware | CPU or one consumer GPU with 8 GB VRAM | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| experience | undergraduate, comfortable with Python | default (not stated by user) |
| class access | unknown at time of writing; fallback included | stated by user |

## Problem statement

- [E] In large lectures, many students have the same confusion but few ask. Live question tools let students ask anonymously, and the instructor then has to decide which questions to answer first.
- [V] AskNow groups live student questions by embedding similarity and shows instructors the five most frequent groups, but its paper does not evaluate whether the groups are correct, whether the most frequent groups are the ones instructors most need, or how frequency compares with upvoting ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)). ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- [E] Widely used tools rank questions by upvotes instead. Upvotes measure visible agreement with a question someone else wrote; the number of students who independently ask the same thing measures how widely the confusion is shared. Which signal better tells an instructor what to answer has not been tested in any paper this search found.

## Literature background

- [V] AskNow: embedding-based grouping of live lecture questions (threshold K-means on text-embedding-3-small) with a top-5 topic view; one-week deployment in three CS courses with 117 students; clustering quality and threshold not reported ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)). ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- [V] Grouping of 93 student questions on one topic with six multilingual encoders, UMAP and HDBSCAN, scored against six instructors and eight students with AMI, ARI and V-measure; tuned clustering approached the lower bound of human agreement ([Gomez 2025](https://hdl.handle.net/2117/449495)). ([Gomez 2025](https://hdl.handle.net/2117/449495))
- [V] LLM-induced question similarity clusters assessment items into knowledge components ([Wei et al. 2025](https://arxiv.org/abs/2505.06469)); embedding clustering finds question topics in MOOC forums ([Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252)); unsupervised pipelines detect duplicate questions in question repositories ([Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150)). None of these used short questions typed during a live lecture. ([Wei et al. 2025](https://arxiv.org/abs/2505.06469); [Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252); [Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150))
- [V] Teacher dashboards that summarise or cluster student input were evaluated with interviews, not with measured task accuracy ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582)). Classroom backchannels and anonymous question forms are established practice ([Du et al. 2012](https://doi.org/10.1145/2379057.2379081); [Iosub et al. 2025](https://doi.org/10.1021/acs.jchemed.4c01089)). ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Du et al. 2012](https://doi.org/10.1145/2379057.2379081); [Iosub et al. 2025](https://doi.org/10.1021/acs.jchemed.4c01089))

| Paper | Published | Method | Datasets | Findings | Stated limitations | Read | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AskNow: An LLM-powered Interactive System for Real-Time Question Answering in Large-Scale Classrooms (Liu et al. 2026) | 2026 | An LLM answers live student questions using a streaming lecture transcript; the instructor view groups questions by embedding (text-embedding-3-small) with threshold-based K-means and lists the five most frequent clusters | One-week deployment in three university CS courses (117 students completed all parts; 24 students and 3 instructors interviewed) | Students' perceived time to resolve confusion fell significantly; instructors rated answers accurate. Clustering quality, the threshold value and instructor use of the topic views were not reported. | Two lectures per course; one university; self-selection; transcript-only context | full text | [link](https://doi.org/10.1145/3772318.3790328) |
| Automatic grouping of question-answer pairs expressed in natural language for teaching environments (Gomez 2025) | 2025-07-03 | Six multilingual sentence encoders, optional UMAP, HDBSCAN; agreement with human groupings by AMI, ARI and V-measure | 93 unique student questions on one topic (low-emission zones) from inquiry-based teaching; grouped by 6 instructors and 8 students | Dimensionality reduction essential; contrastive universal encoders (BGE-M3, mE5) beat masked LMs; tuned clustering approaches the lower bound of human agreement (numbers not on the landing page) | Topic-specific data; code-switching not analysed; only semantic grouping evaluated | abstract | [link](https://hdl.handle.net/2117/449495) |
| LearnLens: An AI-Enhanced Dashboard to Support Teachers in Open-Ended Classrooms (Srivastava et al. 2025) | 2025-09-11 | not reported | not reported | Teacher-facing dashboard summarising open-ended student responses (word clouds, bar charts, AI summaries); evaluated with teacher interviews | not reported | abstract | [link](https://arxiv.org/abs/2509.10582) |
| KCluster: An LLM-based Clustering Approach to Knowledge Component Discovery (Wei et al. 2025) | 2025-05-09 | not reported | not reported | An LLM-induced question-similarity metric plus clustering yields knowledge-component models that predict performance better than expert models (assessment items, not student-asked questions) | not reported | abstract | [link](https://arxiv.org/abs/2505.06469) |
| Weighted word embeddings and clustering‐based identification of question topics in MOOC discussion forum posts (Onan & Tocoglu 2020) | 2020-05-04 | not reported | not reported | Compares word-embedding weightings and clustering algorithms for question topics in MOOC forum posts | not reported | abstract | [link](https://doi.org/10.1002/cae.22252) |
| Unsupervised Question Duplicate and Related Questions Detection in e-learning platforms (Chowdhary et al. 2022) | 2022-12-20 | not reported | not reported | Unsupervised hybrid pipeline for near-duplicate and related question detection in e-learning question repositories | not reported | abstract | [link](https://arxiv.org/abs/2301.05150) |
| Communication patterns for a classroom public digital backchannel (Du et al. 2012) | 2012-10-03 | not reported | not reported | 15-week field study of a public classroom digital backchannel; analyses communication patterns and which messages draw responses | not reported | abstract | [link](https://doi.org/10.1145/2379057.2379081) |
| Ask Away! Empowering Students to Ask Anonymous In-Class Questions (Iosub et al. 2025) | 2025-06-13 | not reported | not reported | Describes an anonymous in-class question form; the abstract reports no measured outcome | not reported | abstract | [link](https://doi.org/10.1021/acs.jchemed.4c01089) |
| EduVidQA: Generating and Evaluating Long-form Answers to Student Questions based on Lecture Videos (Ray et al. 2025) | 2025-01-01 | not reported | not reported | EduVidQA: 5,252 question-answer pairs (synthetic and real-world) from 296 CS lecture videos | not reported | abstract | [link](https://doi.org/10.18653/v1/2025.emnlp-main.1760) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

## Research question

- RQ1 (Study 1). How well do lexical, sentence-embedding and LLM-based clusterings of live lecture questions agree with human groupings, and how often do they identify the same largest group (the brightest star) as humans?
- RQ2 (Study 2). When the same questions are both grouped and upvoted, does ranking groups by the number of distinct students who asked them match the instructor's priorities better than ranking by upvotes?

## Hypothesis

- [S] H1 (Study 1): sentence-embedding clustering reaches an AMI with the consensus human grouping that lies within the range of agreement between individual annotators, and exceeds TF-IDF clustering by at least 0.05 AMI on average across sessions.
- [S] H2 (Study 2): ranking question groups by the number of distinct askers gives a higher NDCG@5 against the instructor's blind priority ranking than ranking by total upvotes.

**How the hypothesis can be supported or rejected.** - Fixed before any data is analysed.
- H1 is supported if mean AMI (embedding vs consensus) is at least the lowest pairwise human AMI and the paired difference to TF-IDF has a 95% bootstrap confidence interval above 0.05; rejected if embedding AMI is below the lowest human-human AMI in most sessions or the interval for the difference includes or lies below 0; otherwise inconclusive.
- H2 is supported if the 95% bootstrap confidence interval (resampling sessions, then groups) of NDCG@5(size) minus NDCG@5(upvotes) lies above 0; rejected if it lies below 0; inconclusive if it contains 0. With few sessions an inconclusive result is likely and will be reported as such.

## Dataset

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [EduVidQA](https://huggingface.co/datasets/vqamaster/EduVidQA) | possible public source of student questions on lecture videos | 2.15 GB including transcripts (rows not reported) | json | mit | open | keep real-world questions only; drop transcripts | no vote counts; mixes synthetic and real questions | yes |

- [E] Primary data: questions collected with the app in real lectures. Target: at least 4 sessions and 300 questions in total; 8 sessions if available. Stored per question: text, session, anonymous student ID (random per session), submission time, phase, and upvotes with voter IDs.
- [E] Each session has two phases: an ask phase in which students submit questions privately (no feed visible), and a short voting phase in which all questions are shown in random order and students upvote. Both signals are then measured on the same questions, and the feed cannot suppress repeat asking.
- [E] Fallback for Study 1 if no class is available: real-world (not synthetic) questions from EduVidQA, grouped by lecture video; it has no upvotes, so Study 2 cannot use it.
- [E] Ethics: university ethics approval and informed consent before any collection; participation never affects grades; no names stored; questions released only after review for identifying content.

## Methodology

**Project type.** Original study (Study 2) built on an extension (Study 1) of published question-grouping evaluations to live lecture questions. The app is the data-collection instrument, not the contribution.

- Study 1 (RQ1). Three annotators (the instructor or TA, and two others; at least one not the project author) group each session's questions independently with a written guideline: two questions belong together if one answer from the instructor would resolve both. A consensus grouping is formed by majority co-assignment.
- Clustering methods, all with the same distance-threshold agglomerative clustering so only the representation differs: (a) TF-IDF cosine; (b) sentence embeddings from two small open models (e.g. all-MiniLM-L6-v2 and BGE-small); (c) an LLM pair judge ('would one answer resolve both questions?') turned into a similarity graph; (d) UMAP plus HDBSCAN on embeddings, as in the closest prior work.
- Thresholds are tuned by leave-one-session-out: tuned on all other sessions, evaluated on the held-out one.
- Study 2 (RQ2). After each lecture the instructor ranks the consensus question groups by how important they are to answer for the whole class, without seeing group sizes or votes (groups shown in random order). Rankings by each signal are then compared with this ranking.

**Variables.**

- Independent (Study 1): question representation and clustering method; distance threshold (swept).
- Independent (Study 2): prioritisation signal: distinct askers per group; total upvotes; upvotes from distinct students; distinct askers plus distinct upvoters; most recent first; random.
- Dependent: AMI, ARI and V-measure against each annotator and the consensus; largest-group match; NDCG@5 and precision@3 against the instructor ranking.
- Controlled: same questions, same preprocessing (lower-casing, no stemming), same clustering algorithm across representations, same tuning protocol.

**Confounding factors and leakage controls.**

- Upvote position and time bias: questions shown first or longer collect more votes. Controlled by the random order in the voting phase and a fixed voting window.
- A visible feed suppresses repeat asking (students upvote instead of re-asking), which would bias group sizes. Controlled by the private ask phase.
- Instructor knowledge of counts: the ranking is made blind to sizes and votes.
- Annotator influence: annotators group independently before any consensus; agreement is reported.
- Threshold tuned on the test session: avoided by leave-one-session-out tuning.
- Duplicate submissions by the same student count once toward distinct askers.

## Baselines

- Study 1: TF-IDF clustering (lexical baseline); a trivial baseline that puts every question in its own group; the human-human agreement range as the ceiling.
- Study 2: recency ordering and random ordering, besides the two signals being compared.

## Evaluation metrics

- AMI as the primary clustering metric (corrected for chance, comparable across sessions with different numbers of groups); ARI and V-measure as secondary, as in the closest prior work.
- Largest-group match: the largest machine group and the largest consensus group overlap with Jaccard at least 0.5.
- Threshold stability: how many of the top-3 groups stay the same across neighbouring thresholds.
- NDCG@5 (primary) and precision@3 against the instructor ranking.

## Experimental procedure

- 1. Week 1: ethics application; build the app's minimum version (two phases, anonymous IDs, logging, export).
- 2. Week 2: pilot in one session or with volunteers; write and test the annotation guideline.
- 3. Weeks 3-5: collect sessions; annotators group questions within a week of each session; instructor rankings right after each lecture.
- 4. Week 6: Study 1 analysis (all methods, thresholds, agreement).
- 5. Week 7: Study 2 analysis on the consensus groups.
- 6. Week 8: write the paper; release code and the anonymised data if consent allows.
- Minimum version if sessions fall through: Study 1 on EduVidQA real-world questions plus any collected sessions; Study 2 reported as a protocol with pilot data.

**Statistical analysis and uncertainty reporting.**

- Sessions are the unit of replication. Report per-session values and the mean with a 95% bootstrap confidence interval (10,000 resamples of sessions). Compare methods and signals with paired differences on the same sessions.
- Clustering methods with a random element (UMAP, HDBSCAN) are run with 5 seeds; report the spread.
- Two pre-specified primary comparisons (H1, H2); everything else is labelled exploratory. No significance claims beyond the confidence intervals; with 4-8 sessions the study is exploratory.
- Inter-annotator agreement (pairwise AMI) is reported before any method results.

## Compute, time and feasibility

- [E] Compute: clustering a few hundred short questions with small embedding models runs on a laptop CPU in minutes; an LLM pair judge with a small local model fits an 8 GB GPU, or can be skipped.
- [E] Main cost is people: about 4-8 lecture sessions, 3 annotators at roughly 30-60 minutes per session, and an instructor's 10-minute ranking after each lecture.
- [E] Main schedule risk: ethics approval time. Apply in week 1; the fallback keeps Study 1 possible.

## Expected contribution

- The first measured comparison, to our knowledge, of upvotes and question-group size as signals of what instructors should answer, with an interface design (private ask phase) that measures both on the same questions. Novelty confidence is very low: ACM venues still need a direct search.
- An evaluation of question grouping on live lecture questions, including how stable the top group is, which the closest deployed system did not report.
- An anonymised dataset of live lecture questions with groupings, upvotes and instructor priorities, if consent allows release.

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | url_reachable: 1, verified: 8 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: abstract: 8, full text: 1; claims: estimate: 9, speculative: 2, verified: 5 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | no opportunities | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## Limitations and risks

- Too few sessions: results stay exploratory; report per session and widen the confidence intervals honestly.
- Low annotator agreement: then the 'correct grouping' is ill-defined; report agreement as a finding and evaluate against each annotator separately.
- Few questions per session (common in small classes): pool sessions for Study 1 and treat Study 2 as a pilot.
- A paper found later that already compares upvotes and group size: reframe Study 2 as a replication in a new setting.
- Privacy: questions can reveal identity or health information; review before any release.

- The literature search had OpenAlex and Semantic Scholar unavailable and did not search the ACM Digital Library directly; the gap behind Study 2 rests on absence of evidence.
- Most cited papers were read at abstract level; only AskNow was read in full. Read the master's project (mangado2025grouping) in full before finalising Study 1.
- Effect sizes and session counts are estimates; nothing has been run.

## References

1. Maksimjeet Chowdhary, Sanyam Goyal, Venktesh V, Mukesh Mohania, Vikram Goyal (2022). *Unsupervised Question Duplicate and Related Questions Detection in e-learning platforms*. arXiv. https://arxiv.org/abs/2301.05150
2. Honglu Du, Mary Beth Rosson, John M. Carroll (2012). *Communication patterns for a classroom public digital backchannel*. ACM International Conference on Design of Communication (SIGDOC). https://doi.org/10.1145/2379057.2379081
3. Nura Mangado Gómez (2025). *Automatic grouping of question-answer pairs expressed in natural language for teaching environments*. Master's final project, Master in Artificial Intelligence (UPC, URV, UB). https://hdl.handle.net/2117/449495 **[reference url_reachable]**
4. Violeta Iosub, Emily Lovell, Shaun W. C. MacLean, J. Scott McIndoe (2025). *Ask Away! Empowering Students to Ask Anonymous In-Class Questions*. Journal of Chemical Education. https://doi.org/10.1021/acs.jchemed.4c01089
5. Ziqi Liu, Yuankun Wang, Hui-Ru Ho, Yuheng Wu, Yuhang Zhao, Bilge Mutlu (2026). *AskNow: An LLM-powered Interactive System for Real-Time Question Answering in Large-Scale Classrooms*. https://doi.org/10.1145/3772318.3790328
6. Aytuğ Onan, Mansur Alp Toçoğlu (2020). *Weighted word embeddings and clustering‐based identification of question topics in MOOC discussion forum posts*. Computer Applications in Engineering Education. https://doi.org/10.1002/cae.22252
7. Sourjyadip Ray, Shubham Sharma, Somak Aditya, Pawan Goyal (2025). *EduVidQA: Generating and Evaluating Long-form Answers to Student Questions based on Lecture Videos*. Conference on Empirical Methods in Natural Language Processing (EMNLP). https://doi.org/10.18653/v1/2025.emnlp-main.1760
8. Namrata Srivastava, Shruti Jain, Clayton Cohn, Naveeduddin Mohammed, Umesh Timalsina, Gautam Biswas (2025). *LearnLens: An AI-Enhanced Dashboard to Support Teachers in Open-Ended Classrooms*. arXiv. https://arxiv.org/abs/2509.10582
9. Yumou Wei, Paulo Carvalho, John Stamper (2025). *KCluster: An LLM-based Clustering Approach to Knowledge Component Discovery*. arXiv. https://arxiv.org/abs/2505.06469
