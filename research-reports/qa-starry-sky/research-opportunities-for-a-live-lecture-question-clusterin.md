# Research opportunities for a live-lecture question clustering app (starry sky)

> **DRAFT: 0 integrity error(s) and 1 warning(s) were reported by the validator.** Unverified references are marked in the reference list.

**Report type:** Research Opportunity Report  
**Generated:** 2026-10-19

**Evidence tags:** [V] verified against a cited source or API response; [E] reasoned estimate; [S] speculative suggestion.

| Constraint | Value | Origin |
| --- | --- | --- |
| field | educational technology, HCI and NLP | stated by user |
| project | classroom app clustering student questions | stated by user |
| hardware | CPU or one consumer GPU with 8 GB VRAM | default (not stated by user) |
| time budget weeks | 8 | default (not stated by user) |
| experience | undergraduate, comfortable with Python | default (not stated by user) |

## Summary

The app itself has largely been built before: AskNow ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) groups live student questions by embedding similarity and shows instructors the most frequent clusters, in a deployment with 117 students. Its paper, read in full, never checks whether the clusters are right, whether the most frequent clusters are the ones instructors most need, or how frequency compares with upvoting. Those omissions are where a student paper can contribute, with the app as the research instrument.

## Decisions

Each shortlisted research question gets go, conditional go or no-go. A go requires full-text reading of the closest work and an explicit check for leakage, weak baselines and evaluation flaws; anything short of that is at most a conditional go.

| Research question | Question type | Decision | Novelty confidence | Mode | Main conditions |
| --- | --- | --- | --- | --- | --- |
| Upvotes or semantic clusters: which signal tells instructors what most students need answered? | Novel research question | CONDITIONAL GO | very_low | original | Search the ACM Digital Library (CHI, L@S, SIGCSE, LAK) and Google Scholar for upvoting of live or backchannel questions; a paper that already compares the two signals turns this into a replication or extension; Confirm access to at least 4  |
| How accurately does clustering group live lecture questions, and how stable is the brightest star? | Extension of an existing experiment | CONDITIONAL GO | very_low | extension | Read the full text of the master's project; if it already used live lecture questions or analysed the largest cluster, reframe this as a replication on new data |
| Does the starry sky help instructors more than a ranked list? | Novel research question | CONDITIONAL GO | very_low | original | Check visualisation research on bubble charts versus sorted bar charts before running the study |
| Build an app that clusters live questions and shows the most frequent ones | Already answered | NO-GO | very_low | original | not reported |

## What was verified, and how

| Dimension | Status | Meaning |
| --- | --- | --- |
| Source existence (verify-refs) | url_reachable: 1, verified: 10 | The cited record exists and its title matches. Says nothing about what the paper shows. |
| Claim support | papers read: abstract: 10, full text: 1; claims: estimate: 13, verified: 10 | Verified claims were checked against their source at the read level shown. |
| Novelty confidence | Upvotes or semantic clusters: which signal tells instructors what most students need answered?: very_low (search ceiling low); How accurately does clustering group live lecture questions, and how stable is the brightest star?: very_low (search ceiling low); Does the starry sky help instructors more than a ranked list?: very_low (search ceiling low); Build an app that clusters live questions and shows the most frequent ones: very_low (search ceiling low) | How far the searches support a gap; never above medium. |
| Reproducibility | nothing executed | Whether results were re-run, not whether code exists. |

## How the literature was searched

- **Sources that answered:** crossref, huggingface
- **Sources that failed or were skipped:** openalex (keyless daily quota exhausted); semantic_scholar (rate_limited (HTTP 429)); arxiv (partly rate-limited (map and targeted search))
- **Search strategies:** keyword, surveys, negative, comparisons, critique, reproducibility, recent, design-based queries, citation expansion, ordinary web search
- **Date range:** not restricted
- **Records retrieved / after deduplication:** 544 / not recorded
- **Search date:** 2026-10-19
- **Queries:** `student questions lecture clustering`; `audience response system questions`; `classroom question aggregation`; `similar student questions grouping`; `LLM clustering student questions`; `classroom backchannel questions`; `live lecture question upvoting`; `clustering student questions`; `student question deduplication`; `large lecture anonymous questions`; `summarizing student questions LLM`; `student questions MOOC forum clustering`; `instructor question prioritization`
- The closest paper (AskNow) was found only by ordinary web search; no API search or challenge retrieved it.
- A web result gave AskNow's arXiv ID as 2511.01248, but the arXiv API returns a different paper (FocusView) for that ID, so AskNow is cited by its ACM DOI.
- Eleven ordinary web searches supplemented the API searches.

## What has already been done

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
| Characterizing Questioning Patterns and Student Engagement Through Contextual Analysis of Real-Time Classroom Interactions (Sharma et al. 2026) | 2026-09-30 | not reported | not reported | 47 live sessions, 604 poll questions and 340,668 responses from 2,807 learners, read against lecture transcripts | not reported | abstract | [link](https://arxiv.org/abs/2609.38907) |
| Analyzing Pedagogical Quality and Efficiency of LLM Responses with TA Feedback to Live Student Questions (Miroyan et al. 2025) | 2025-02-12 | not reported | not reported | TA evaluation of a GPT-4 RAG assistant's answers to live student questions | not reported | abstract | [link](https://doi.org/10.1145/3641554.3701965) |
| EduVidQA: Generating and Evaluating Long-form Answers to Student Questions based on Lecture Videos (Ray et al. 2025) | 2025-01-01 | not reported | not reported | EduVidQA: 5,252 question-answer pairs (synthetic and real-world) from 296 CS lecture videos | not reported | abstract | [link](https://doi.org/10.18653/v1/2025.emnlp-main.1760) |

Method, dataset, finding and limitation cells summarise the cited paper's abstract or text; 'not reported' means the information was not found there.

### Directions that are already well explored

- Audience response systems and clickers in lectures (a large literature, mostly engagement and perception studies)
- Anonymous digital backchannels in lectures ([Du et al. 2012](https://doi.org/10.1145/2379057.2379081); [Iosub et al. 2025](https://doi.org/10.1021/acs.jchemed.4c01089))
- Duplicate and related question detection in course forums and question banks ([Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150); [Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252))
- LLM answering of student questions ([Miroyan et al. 2025](https://doi.org/10.1145/3641554.3701965); [Ray et al. 2025](https://doi.org/10.18653/v1/2025.emnlp-main.1760))

## Evidence map

What the literature already establishes, where it disagrees, and what it leaves open. Every research question below is derived from these entries.

| ID | Evidence type | What the literature establishes or leaves open |
| --- | --- | --- |
| L1 | missing control | [V] AskNow groups live student questions by embedding similarity and shows instructors the five most frequent clusters, but reports no evaluation of cluster quality, no threshold value, no check that the top clusters match what instructors consider most important, and no logs of instructors using the topic views. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) |
| L2 | missing control | [V] No read paper compares peer upvote counts with the size of a semantic cluster as the signal for which questions to answer first. AskNow has no voting mechanism and ranks clusters by frequency alone. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328); [Du et al. 2012](https://doi.org/10.1145/2379057.2379081)) |
| L3 | stated limitation | [V] Sentence-embedding clustering of student questions approached the lower bound of human agreement, but on 93 questions from one topic in inquiry-based teaching; the author lists topic-specific data and semantic-grouping-only evaluation as limitations. ([Gomez 2025](https://hdl.handle.net/2117/449495)) |
| L4 | benchmark validity concern | [V] Question-similarity and clustering methods in education were evaluated on forum posts, assessment item banks and question repositories, not on the short, informal questions students type during a live lecture, so their accuracy there is unknown. ([Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252); [Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150); [Wei et al. 2025](https://arxiv.org/abs/2505.06469)) |
| L5 | missing control | [V] Teacher dashboards that cluster or summarise student input (LearnLens, AskNow) were evaluated with interviews and surveys; neither measured whether teachers identify the most widely shared questions faster or more accurately than with a plain list. ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) |
| L6 | stated limitation | [V] AskNow's instructors preferred reviewing questions after the lecture rather than during it, and the deployment lasted two lectures per course at one university; real-time use and long-term effects are open. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) |

## Ranked research opportunities

Each opportunity below survived an explicit search for work that already addresses it. None is claimed to be novel: the novelty confidence states how far the search supports the gap, and what it could have missed.

### 1. Upvotes or semantic clusters: which signal tells instructors what most students need answered?
**Question type:** Novel research question  
**Type of gap:** Unverified novelty hypothesis  
**Recommended mode:** original

**Research question.** In live lecture Q&A, does ranking question clusters by how many distinct students asked semantically similar questions identify the questions instructors judge most important better than ranking individual questions by peer upvotes?

**Derived from.**
- L1: [V] AskNow groups live student questions by embedding similarity and shows instructors the five most frequent clusters, but reports no evaluation of cluster quality, no threshold value, no check that the top clusters match what instructors consider most important, and no logs of instructors using the topic views. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- L2: [V] No read paper compares peer upvote counts with the size of a semantic cluster as the signal for which questions to answer first. AskNow has no voting mechanism and ranks clusters by frequency alone. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328); [Du et al. 2012](https://doi.org/10.1145/2379057.2379081))

**Motivation.** Live Q&A tools rank by upvotes; AskNow ranks embedding clusters by frequency ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)). The two signals measure different things (visible agreement versus independent asking), and no read paper compares them.

**Supporting papers.** ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328); [Du et al. 2012](https://doi.org/10.1145/2379057.2379081))

**Closest existing work.**
- ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) [read: full text; overlap: partial]: Uses cluster frequency only; no upvotes and no check that top clusters match instructor priorities
- ([Du et al. 2012](https://doi.org/10.1145/2379057.2379081)) [read: abstract; overlap: different]: Studies which backchannel messages draw responses, not upvote versus cluster ranking

**Evidence for the gap.**
- [V] AskNow reports no comparison with upvoting and no validation of its top-5 topic ranking ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- [E] Three web searches (2026-10-19) found no study comparing upvotes with cluster size

**Potential contribution.** An empirical answer to which prioritisation signal (upvotes, cluster size, or both combined) best matches instructor judgement, with a released, anonymised question dataset.

**Novelty confidence:** very_low (scale: very_low, low, medium; a search cannot establish more). Searched arXiv (partly rate-limited), Crossref and Hugging Face; OpenAlex was over quota and Semantic Scholar rate-limited. ACM Digital Library venues (CHI, L@S, SIGCSE, LAK) were not searched directly. The API challenge did not retrieve AskNow, a known close paper, so its coverage of HCI venues is poor.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `upvoting student questions lecture`; `question voting audience prioritization`; `popular questions upvotes versus frequency`; `crowd voting questions classroom`; `Q&A upvotes instructor answer priority`

**Feasibility.**
- [E] Needs real sessions with upvotes, which the app itself can collect: about 4 to 8 lecture sessions with 50 or more students give a few hundred questions. Ethics approval and consent are required.
- [E] Clustering runs on a CPU with a small sentence-embedding model; no GPU training is needed

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| confound | found | [E] Early questions collect more upvotes regardless of importance (position and time bias) | Log submission time and visibility; compare within time windows; randomise display order in half of the sessions |
| metric definition | found | [E] 'Most important' must be defined before data collection | Instructor ranks question groups after the lecture, blind to both signals; secondary criterion: topics missed on an end-of-lecture quiz |
| weak baseline | checked ok | Recency and random rankings are included as baselines | not reported |
| insufficient runs | found | [E] Few sessions and instructors | Report per-session results with confidence intervals; treat the study as exploratory |
| duplicate items | not checked | not reported | not reported |
| train test overlap | not applicable | not reported | not reported |

**Decision: CONDITIONAL GO.** Positive evidence of the gap (AskNow's unvalidated frequency ranking; no comparison with upvotes found) and a design a student can run, but the literature check is incomplete.

**Conditions before committing.**
- Search the ACM Digital Library (CHI, L@S, SIGCSE, LAK) and Google Scholar for upvoting of live or backchannel questions; a paper that already compares the two signals turns this into a replication or extension
- Confirm access to at least 4 class sessions and obtain ethics approval and consent

**Unresolved evidence and risks.**
- Novelty rests on searches that missed known HCI work
- Instructor judgement as ground truth may be noisy; agreement between raters must be measured

### 2. How accurately does clustering group live lecture questions, and how stable is the brightest star?
**Question type:** Extension of an existing experiment  
**Type of gap:** Underexplored experimental setting  
**Recommended mode:** extension

**Research question.** How well do TF-IDF, sentence-embedding and LLM-based clusterings of live lecture questions agree with instructor groupings, and how sensitive is the largest cluster (the brightest star) to the clustering threshold?

**Derived from.**
- L1: [V] AskNow groups live student questions by embedding similarity and shows instructors the five most frequent clusters, but reports no evaluation of cluster quality, no threshold value, no check that the top clusters match what instructors consider most important, and no logs of instructors using the topic views. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- L3: [V] Sentence-embedding clustering of student questions approached the lower bound of human agreement, but on 93 questions from one topic in inquiry-based teaching; the author lists topic-specific data and semantic-grouping-only evaluation as limitations. ([Gomez 2025](https://hdl.handle.net/2117/449495))
- L4: [V] Question-similarity and clustering methods in education were evaluated on forum posts, assessment item banks and question repositories, not on the short, informal questions students type during a live lecture, so their accuracy there is unknown. ([Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252); [Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150); [Wei et al. 2025](https://arxiv.org/abs/2505.06469))

**Motivation.** Embedding clustering approached human agreement on 93 topic-specific questions ([Gomez 2025](https://hdl.handle.net/2117/449495)); AskNow deploys threshold clustering without reporting its quality or threshold ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)); similarity methods were validated on forum posts and item banks ([Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252); [Wei et al. 2025](https://arxiv.org/abs/2505.06469)).

**Supporting papers.** ([Gomez 2025](https://hdl.handle.net/2117/449495); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328); [Onan & Tocoglu 2020](https://doi.org/10.1002/cae.22252); [Wei et al. 2025](https://arxiv.org/abs/2505.06469); [Chowdhary et al. 2022](https://arxiv.org/abs/2301.05150))

**Closest existing work.**
- ([Gomez 2025](https://hdl.handle.net/2117/449495)) [read: abstract; overlap: partial]: 93 questions on one topic from inquiry-based teaching; multilingual encoders and HDBSCAN; no live-lecture questions, no LLM-based similarity, no analysis of the largest cluster
- ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) [read: full text; overlap: partial]: Deploys the clustering but does not evaluate it
- ([Wei et al. 2025](https://arxiv.org/abs/2505.06469)) [read: abstract; overlap: partial]: LLM-induced similarity for assessment items, not student-asked questions

**Evidence for the gap.**
- [V] AskNow reports no cluster-quality evaluation or threshold ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- [V] The closest evaluation used 93 questions on a single topic, not live lecture questions ([Gomez 2025](https://hdl.handle.net/2117/449495))

**Potential contribution.** A benchmark of question-grouping methods on live lecture questions against human groupings, plus a stability analysis of the top cluster, which is what the app shows instructors.

**Novelty confidence:** very_low (scale: very_low, low, medium; a search cannot establish more). Close prior work exists (a master's project on the same question in another setting) and its full text was not read. Searched arXiv (partly rate-limited), Crossref and Hugging Face; OpenAlex was over quota and Semantic Scholar rate-limited. ACM Digital Library venues (CHI, L@S, SIGCSE, LAK) were not searched directly. The API challenge did not retrieve AskNow, a known close paper, so its coverage of HCI venues is poor.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `clustering student questions evaluation`; `student question grouping human agreement`; `short text clustering student questions embeddings`; `LLM question similarity clustering education`; `duplicate student questions detection forum`

**Feasibility.**
- [E] Fits 8 weeks on a CPU or an 8 GB GPU: a few hundred questions, 2 or 3 annotators, small embedding models
- [E] Data from the app's own sessions. EduVidQA (MIT licence) is a possible public source but is 2.15 GB with transcripts and mixes synthetic questions, so only its real-world subset would fit

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| metric definition | found | [E] Human groupings of short questions disagree; there is no single correct clustering | Measure agreement between annotators first and compare methods against that ceiling, as the closest work does |
| weak baseline | checked ok | TF-IDF and plain sentence-embedding baselines alongside LLM similarity | not reported |
| model selection on test | found | [E] Tuning thresholds on the evaluated sessions inflates agreement | Tune on held-out sessions; report results for every threshold |
| pretraining contamination | not applicable | not reported | not reported |

**Decision: CONDITIONAL GO.** A clear, measurable extension with positive evidence of the gap; the main risk is that the master's project covers more than its abstract says.

**Conditions before committing.** Read the full text of the master's project; if it already used live lecture questions or analysed the largest cluster, reframe this as a replication on new data

**Unresolved evidence and risks.**
- Annotation effort and agreement
- Small, single-course data

### 3. Does the starry sky help instructors more than a ranked list?
**Question type:** Novel research question  
**Type of gap:** Unverified novelty hypothesis  
**Recommended mode:** original

**Research question.** With the same clustered questions, do instructors identify the most widely shared questions faster and more accurately with a frequency-encoded constellation view than with a ranked list?

**Derived from.**
- L5: [V] Teacher dashboards that cluster or summarise student input (LearnLens, AskNow) were evaluated with interviews and surveys; neither measured whether teachers identify the most widely shared questions faster or more accurately than with a plain list. ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))
- L6: [V] AskNow's instructors preferred reviewing questions after the lecture rather than during it, and the deployment lasted two lectures per course at one university; real-time use and long-term effects are open. ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))

**Motivation.** Clustering dashboards were evaluated with interviews only ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)).

**Supporting papers.** ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))

**Closest existing work.**
- ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582)) [read: abstract; overlap: partial]: Middle-school open responses, word clouds and summaries; qualitative evaluation, no list baseline
- ([Liu et al. 2026](https://doi.org/10.1145/3772318.3790328)) [read: full text; overlap: partial]: Lists topics; no comparison of visualisations

**Evidence for the gap.** [V] Both dashboards were evaluated qualitatively, without a list baseline ([Srivastava et al. 2025](https://arxiv.org/abs/2509.10582); [Liu et al. 2026](https://doi.org/10.1145/3772318.3790328))

**Potential contribution.** A controlled within-subjects comparison of a constellation view and a ranked list on time, accuracy and workload.

**Novelty confidence:** very_low (scale: very_low, low, medium; a search cannot establish more). General visualisation research on size-encoded displays versus sorted lists may already predict the result; that literature was not searched. Searched arXiv (partly rate-limited), Crossref and Hugging Face; OpenAlex was over quota and Semantic Scholar rate-limited. ACM Digital Library venues (CHI, L@S, SIGCSE, LAK) were not searched directly. The API challenge did not retrieve AskNow, a known close paper, so its coverage of HCI venues is poor.
Attempts to disprove novelty: 5 search(es); signal `no_close_match_in_this_search`. Queries: `visualization student questions instructor`; `real-time classroom dashboard visualization questions`; `instructor dashboard student confusion visualization`; `question cluster visualization user study`; `teacher orchestration dashboard evaluation`

**Feasibility.** [E] 12 to 16 instructors or TAs, recorded question sets, about 30 minutes each

**Methodological risks.**

| Risk | Status | Evidence | Mitigation |
| --- | --- | --- | --- |
| confound | found | [E] A sorted list makes the largest group trivially visible; a star map may look better but be slower | Include tasks beyond finding the largest group (related questions, the second most common topic); counterbalance order |
| weak baseline | checked ok | Ranked list with counts as the baseline | not reported |
| insufficient runs | found | [E] Small participant pool | Within-subjects design; report effect sizes with intervals |

**Decision: CONDITIONAL GO.** A useful secondary study, but a list may win on pure find-the-biggest tasks.

**Conditions before committing.** Check visualisation research on bubble charts versus sorted bar charts before running the study

**Unresolved evidence and risks.** The result may be predictable from perception research

### Candidates rejected after the novelty challenge

- **Build an app that clusters live questions and shows the most frequent ones** (Already well studied): AskNow already deployed embedding-based grouping of live student questions with a view of the five most frequent topics in three courses; building it again is engineering, not a research contribution.

## Feasibility ranking

*Not provided (missing information).*

## Candidate datasets

| Dataset | Purpose | Size | Format | Licence | Access | Preprocessing | Suitability | Verified via API |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [EduVidQA](https://huggingface.co/datasets/vqamaster/EduVidQA) | possible public source of student questions on lecture videos | 2.15 GB including transcripts (rows not reported) | json | mit | open | keep real-world questions only; drop transcripts | no vote counts; mixes synthetic and real questions | yes |
| [Dataset MOOC Forum edX](https://zenodo.org/records/5115573) | forum questions from three programming MOOCs | 556 MB (one MongoDB dump) | mongo | cc-by-4.0 | open | schema not documented | forum posts, not live lecture questions; whether votes are included is not reported | yes |

## Recommendation

Make question 1 (upvotes versus cluster size) the main hypothesis, with question 2 (clustering accuracy) as the necessary first step, since a star's brightness only means something if the clusters are right. Question 3 is optional. The app collects the data for all three.

## Limitations of this report

- OpenAlex and Semantic Scholar were unavailable and arXiv was rate-limited for part of the search; ACM Digital Library venues were not searched directly
- Most papers were read at abstract level; only AskNow was read in full
- Novelty confidence is very low for every question

## References

1. Maksimjeet Chowdhary, Sanyam Goyal, Venktesh V, Mukesh Mohania, Vikram Goyal (2022). *Unsupervised Question Duplicate and Related Questions Detection in e-learning platforms*. arXiv. https://arxiv.org/abs/2301.05150
2. Honglu Du, Mary Beth Rosson, John M. Carroll (2012). *Communication patterns for a classroom public digital backchannel*. ACM International Conference on Design of Communication (SIGDOC). https://doi.org/10.1145/2379057.2379081
3. Nura Mangado Gómez (2025). *Automatic grouping of question-answer pairs expressed in natural language for teaching environments*. Master's final project, Master in Artificial Intelligence (UPC, URV, UB). https://hdl.handle.net/2117/449495 **[reference url_reachable]**
4. Violeta Iosub, Emily Lovell, Shaun W. C. MacLean, J. Scott McIndoe (2025). *Ask Away! Empowering Students to Ask Anonymous In-Class Questions*. Journal of Chemical Education. https://doi.org/10.1021/acs.jchemed.4c01089
5. Ziqi Liu, Yuankun Wang, Hui-Ru Ho, Yuheng Wu, Yuhang Zhao, Bilge Mutlu (2026). *AskNow: An LLM-powered Interactive System for Real-Time Question Answering in Large-Scale Classrooms*. https://doi.org/10.1145/3772318.3790328
6. Mihran Miroyan, Chancharik Mitra, Rishi Jain, Gireeja V. Ranade, Narges Norouzi (2025). *Analyzing Pedagogical Quality and Efficiency of LLM Responses with TA Feedback to Live Student Questions*. ACM Technical Symposium on Computer Science Education (SIGCSE). https://doi.org/10.1145/3641554.3701965
7. Aytuğ Onan, Mansur Alp Toçoğlu (2020). *Weighted word embeddings and clustering‐based identification of question topics in MOOC discussion forum posts*. Computer Applications in Engineering Education. https://doi.org/10.1002/cae.22252
8. Sourjyadip Ray, Shubham Sharma, Somak Aditya, Pawan Goyal (2025). *EduVidQA: Generating and Evaluating Long-form Answers to Student Questions based on Lecture Videos*. Conference on Empirical Methods in Natural Language Processing (EMNLP). https://doi.org/10.18653/v1/2025.emnlp-main.1760
9. Rohit Sharma, Pavani Ayinampudi, Aditya B. M. V., Jinal Gupta, Prakash Hegade, Sakshi Sharma et al. (2026). *Characterizing Questioning Patterns and Student Engagement Through Contextual Analysis of Real-Time Classroom Interactions*. arXiv. https://arxiv.org/abs/2609.38907
10. Namrata Srivastava, Shruti Jain, Clayton Cohn, Naveeduddin Mohammed, Umesh Timalsina, Gautam Biswas (2025). *LearnLens: An AI-Enhanced Dashboard to Support Teachers in Open-Ended Classrooms*. arXiv. https://arxiv.org/abs/2509.10582
11. Yumou Wei, Paulo Carvalho, John Stamper (2025). *KCluster: An LLM-based Clustering Approach to Knowledge Component Discovery*. arXiv. https://arxiv.org/abs/2505.06469
