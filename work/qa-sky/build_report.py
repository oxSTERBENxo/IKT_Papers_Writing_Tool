"""Assemble the opportunity report JSON from retrieved metadata (abstracts.json, learnlens.json) and reading notes."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
a = json.loads((HERE / "abstracts.json").read_text(encoding="utf-8"))
ll = json.loads((HERE / "learnlens.json").read_text(encoding="utf-8"))["paper"]


def rec(key, d, role, read="abstract", findings=None, doi=None):
    d_doi = d.get("doi")
    if d_doi and "zenodo" in d_doi:
        d_doi = None
    return {"key": key, "title": d["title"], "authors": d.get("authors") or [], "year": d.get("year"),
            "date": d.get("date"), "venue": d.get("venue"), "doi": doi or d_doi, "arxiv_id": d.get("arxiv_id"),
            "pmid": None, "url": d.get("url"), "method": None, "datasets": None, "findings": findings,
            "limitations": None, "role": role, "read_level": read}


papers = [
    {"key": "liu2026asknow",
     "title": "AskNow: An LLM-powered Interactive System for Real-Time Question Answering in Large-Scale Classrooms",
     "authors": ["Ziqi Liu", "Yuankun Wang", "Hui-Ru Ho", "Yuheng Wu", "Yuhang Zhao", "Bilge Mutlu"], "year": 2026,
     "date": None, "venue": None, "doi": "10.1145/3772318.3790328", "arxiv_id": None, "pmid": None,
     "url": "https://arxiv.org/html/2511.01248v1",
     "method": "An LLM answers live student questions using a streaming lecture transcript; the instructor view groups "
               "questions by embedding (text-embedding-3-small) with threshold-based K-means and lists the five most "
               "frequent clusters",
     "datasets": "One-week deployment in three university CS courses (117 students completed all parts; 24 students "
                 "and 3 instructors interviewed)",
     "findings": "Students' perceived time to resolve confusion fell significantly; instructors rated answers accurate. "
                 "Clustering quality, the threshold value and instructor use of the topic views were not reported.",
     "limitations": "Two lectures per course; one university; self-selection; transcript-only context",
     "role": "closest", "read_level": "full_text"},
    {"key": "mangado2025grouping",
     "title": "Automatic grouping of question-answer pairs expressed in natural language for teaching environments",
     "authors": ["Nura Mangado Gómez"], "year": 2025, "date": "2025-07-03",
     "venue": "Master's final project, Master in Artificial Intelligence (UPC, URV, UB)",
     "doi": None, "arxiv_id": None, "pmid": None, "url": "https://hdl.handle.net/2117/449495",
     "method": "Six multilingual sentence encoders, optional UMAP, HDBSCAN; agreement with human groupings by AMI, "
               "ARI and V-measure",
     "datasets": "93 unique student questions on one topic (low-emission zones) from inquiry-based teaching; grouped by "
                 "6 instructors and 8 students",
     "findings": "Dimensionality reduction essential; contrastive universal encoders (BGE-M3, mE5) beat masked LMs; "
                 "tuned clustering approaches the lower bound of human agreement (numbers not on the landing page)",
     "limitations": "Topic-specific data; code-switching not analysed; only semantic grouping evaluated",
     "role": "closest", "read_level": "abstract"},
    rec("srivastava2025learnlens", ll, "closest",
        findings="Teacher-facing dashboard summarising open-ended student responses (word clouds, bar charts, AI "
                 "summaries); evaluated with teacher interviews"),
    rec("wei2025kcluster", a["2505.06469"], "supporting",
        findings="An LLM-induced question-similarity metric plus clustering yields knowledge-component models that "
                 "predict performance better than expert models (assessment items, not student-asked questions)"),
    rec("onan2020moocclustering", a["10.1002/cae.22252"], "supporting", doi="10.1002/cae.22252",
        findings="Compares word-embedding weightings and clustering algorithms for question topics in MOOC forum posts"),
    rec("chowdhary2022qdup", a["2301.05150"], "supporting",
        findings="Unsupervised hybrid pipeline for near-duplicate and related question detection in e-learning "
                 "question repositories"),
    rec("du2012classcommons", a["10.1145/2379057.2379081"], "supporting",
        findings="15-week field study of a public classroom digital backchannel; analyses communication patterns and "
                 "which messages draw responses"),
    rec("iosub2025askaway", a["10.26434/chemrxiv-2024-gwxrs"], "supporting",
        findings="Describes an anonymous in-class question form; the abstract reports no measured outcome"),
    rec("sharma2026polls", a["2609.38907"], "background",
        findings="47 live sessions, 604 poll questions and 340,668 responses from 2,807 learners, read against lecture "
                 "transcripts"),
    rec("miroyan2025edison", a["10.1145/3641554.3701965"], "background",
        findings="TA evaluation of a GPT-4 RAG assistant's answers to live student questions"),
    rec("ray2025eduvidqa", a["10.18653/v1/2025.emnlp-main.1760"], "background",
        findings="EduVidQA: 5,252 question-answer pairs (synthetic and real-world) from 296 CS lecture videos"),
]

ledger = [
    {"id": "L1", "type": "missing_control", "level": "verified", "sources": ["liu2026asknow"],
     "text": "AskNow groups live student questions by embedding similarity and shows instructors the five most frequent "
             "clusters, but reports no evaluation of cluster quality, no threshold value, no check that the top "
             "clusters match what instructors consider most important, and no logs of instructors using the topic views."},
    {"id": "L2", "type": "missing_control", "level": "verified", "sources": ["liu2026asknow", "du2012classcommons"],
     "text": "No read paper compares peer upvote counts with the size of a semantic cluster as the signal for which "
             "questions to answer first. AskNow has no voting mechanism and ranks clusters by frequency alone."},
    {"id": "L3", "type": "stated_limitation", "level": "verified", "sources": ["mangado2025grouping"],
     "text": "Sentence-embedding clustering of student questions approached the lower bound of human agreement, but on "
             "93 questions from one topic in inquiry-based teaching; the author lists topic-specific data and "
             "semantic-grouping-only evaluation as limitations."},
    {"id": "L4", "type": "benchmark_validity_concern", "level": "verified",
     "sources": ["onan2020moocclustering", "chowdhary2022qdup", "wei2025kcluster"],
     "text": "Question-similarity and clustering methods in education were evaluated on forum posts, assessment item "
             "banks and question repositories, not on the short, informal questions students type during a live "
             "lecture, so their accuracy there is unknown."},
    {"id": "L5", "type": "missing_control", "level": "verified", "sources": ["srivastava2025learnlens", "liu2026asknow"],
     "text": "Teacher dashboards that cluster or summarise student input (LearnLens, AskNow) were evaluated with "
             "interviews and surveys; neither measured whether teachers identify the most widely shared questions "
             "faster or more accurately than with a plain list."},
    {"id": "L6", "type": "stated_limitation", "level": "verified", "sources": ["liu2026asknow"],
     "text": "AskNow's instructors preferred reviewing questions after the lecture rather than during it, and the "
             "deployment lasted two lectures per course at one university; real-time use and long-term effects are open."},
]

LIMITED = ("Searched arXiv (partly rate-limited), Crossref and Hugging Face; OpenAlex was over quota and Semantic "
           "Scholar rate-limited. ACM Digital Library venues (CHI, L@S, SIGCSE, LAK) were not searched directly. "
           "The API challenge did not retrieve AskNow, a known close paper, so its coverage of HCI venues is poor.")

opps = [
    {"title": "Upvotes or semantic clusters: which signal tells instructors what most students need answered?",
     "question_type": "novel", "derived_from": ["L1", "L2"], "category": "unverified_novelty_hypothesis",
     "mode": "original", "status": "kept",
     "research_question": "In live lecture Q&A, does ranking question clusters by how many distinct students asked "
                          "semantically similar questions identify the questions instructors judge most important "
                          "better than ranking individual questions by peer upvotes?",
     "motivation": "Live Q&A tools rank by upvotes; AskNow ranks embedding clusters by frequency [@liu2026asknow]. The "
                   "two signals measure different things (visible agreement versus independent asking), and no read "
                   "paper compares them.",
     "supporting_papers": ["liu2026asknow", "du2012classcommons"],
     "closest_existing_work": [
         {"key": "liu2026asknow", "how_it_differs": "Uses cluster frequency only; no upvotes and no check that top "
          "clusters match instructor priorities", "read_level": "full_text", "overlap": "partial"},
         {"key": "du2012classcommons", "how_it_differs": "Studies which backchannel messages draw responses, not "
          "upvote versus cluster ranking", "read_level": "abstract", "overlap": "different"}],
     "gap_evidence": [
         {"text": "AskNow reports no comparison with upvoting and no validation of its top-5 topic ranking",
          "level": "verified", "sources": ["liu2026asknow"]},
         {"text": "Three web searches (2026-10-19) found no study comparing upvotes with cluster size", "level": "estimate"}],
     "contribution": "An empirical answer to which prioritisation signal (upvotes, cluster size, or both combined) "
                     "best matches instructor judgement, with a released, anonymised question dataset.",
     "novelty": {"confidence": "very_low", "uncertainty": LIMITED, "signal": "no_close_match_in_this_search",
                 "ceiling": "low",
                 "challenge_searches": ["upvoting student questions lecture", "question voting audience prioritization",
                                        "popular questions upvotes versus frequency", "crowd voting questions classroom",
                                        "Q&A upvotes instructor answer priority"]},
     "feasibility": [
         {"text": "Needs real sessions with upvotes, which the app itself can collect: about 4 to 8 lecture sessions "
                  "with 50 or more students give a few hundred questions. Ethics approval and consent are required.",
          "level": "estimate"},
         {"text": "Clustering runs on a CPU with a small sentence-embedding model; no GPU training is needed",
          "level": "estimate"}],
     "methodological_risks": [
         {"type": "confound", "status": "found",
          "evidence": {"text": "Early questions collect more upvotes regardless of importance (position and time bias)",
                       "level": "estimate"},
          "mitigation": "Log submission time and visibility; compare within time windows; randomise display order in "
                        "half of the sessions"},
         {"type": "metric_definition", "status": "found",
          "evidence": {"text": "'Most important' must be defined before data collection", "level": "estimate"},
          "mitigation": "Instructor ranks question groups after the lecture, blind to both signals; secondary "
                        "criterion: topics missed on an end-of-lecture quiz"},
         {"type": "weak_baseline", "status": "checked_ok",
          "evidence": "Recency and random rankings are included as baselines"},
         {"type": "insufficient_runs", "status": "found",
          "evidence": {"text": "Few sessions and instructors", "level": "estimate"},
          "mitigation": "Report per-session results with confidence intervals; treat the study as exploratory"},
         {"type": "duplicate_items", "status": "not_checked"},
         {"type": "train_test_overlap", "status": "not_applicable"}],
     "decision": {"verdict": "conditional_go",
                  "rationale": "Positive evidence of the gap (AskNow's unvalidated frequency ranking; no comparison "
                               "with upvotes found) and a design a student can run, but the literature check is "
                               "incomplete.",
                  "conditions": ["Search the ACM Digital Library (CHI, L@S, SIGCSE, LAK) and Google Scholar for "
                                 "upvoting of live or backchannel questions; a paper that already compares the two "
                                 "signals turns this into a replication or extension",
                                 "Confirm access to at least 4 class sessions and obtain ethics approval and consent"],
                  "unresolved_risks": ["Novelty rests on searches that missed known HCI work",
                                       "Instructor judgement as ground truth may be noisy; agreement between raters "
                                       "must be measured"]}},
    {"title": "How accurately does clustering group live lecture questions, and how stable is the brightest star?",
     "question_type": "extension", "derived_from": ["L1", "L3", "L4"], "category": "underexplored_setting",
     "mode": "extension", "status": "kept",
     "research_question": "How well do TF-IDF, sentence-embedding and LLM-based clusterings of live lecture questions "
                          "agree with instructor groupings, and how sensitive is the largest cluster (the brightest "
                          "star) to the clustering threshold?",
     "motivation": "Embedding clustering approached human agreement on 93 topic-specific questions "
                   "[@mangado2025grouping]; AskNow deploys threshold clustering without reporting its quality or "
                   "threshold [@liu2026asknow]; similarity methods were validated on forum posts and item banks "
                   "[@onan2020moocclustering; @wei2025kcluster].",
     "supporting_papers": ["mangado2025grouping", "liu2026asknow", "onan2020moocclustering", "wei2025kcluster",
                           "chowdhary2022qdup"],
     "closest_existing_work": [
         {"key": "mangado2025grouping", "how_it_differs": "93 questions on one topic from inquiry-based teaching; "
          "multilingual encoders and HDBSCAN; no live-lecture questions, no LLM-based similarity, no analysis of the "
          "largest cluster", "read_level": "abstract", "overlap": "partial"},
         {"key": "liu2026asknow", "how_it_differs": "Deploys the clustering but does not evaluate it",
          "read_level": "full_text", "overlap": "partial"},
         {"key": "wei2025kcluster", "how_it_differs": "LLM-induced similarity for assessment items, not "
          "student-asked questions", "read_level": "abstract", "overlap": "partial"}],
     "gap_evidence": [
         {"text": "AskNow reports no cluster-quality evaluation or threshold", "level": "verified",
          "sources": ["liu2026asknow"]},
         {"text": "The closest evaluation used 93 questions on a single topic, not live lecture questions",
          "level": "verified", "sources": ["mangado2025grouping"]}],
     "contribution": "A benchmark of question-grouping methods on live lecture questions against human groupings, "
                     "plus a stability analysis of the top cluster, which is what the app shows instructors.",
     "novelty": {"confidence": "very_low",
                 "uncertainty": "Close prior work exists (a master's project on the same question in another "
                                "setting) and its full text was not read. " + LIMITED,
                 "signal": "no_close_match_in_this_search", "ceiling": "low",
                 "challenge_searches": ["clustering student questions evaluation",
                                        "student question grouping human agreement",
                                        "short text clustering student questions embeddings",
                                        "LLM question similarity clustering education",
                                        "duplicate student questions detection forum"]},
     "feasibility": [
         {"text": "Fits 8 weeks on a CPU or an 8 GB GPU: a few hundred questions, 2 or 3 annotators, small embedding "
                  "models", "level": "estimate"},
         {"text": "Data from the app's own sessions. EduVidQA (MIT licence) is a possible public source but is 2.15 GB "
                  "with transcripts and mixes synthetic questions, so only its real-world subset would fit",
          "level": "estimate"}],
     "methodological_risks": [
         {"type": "metric_definition", "status": "found",
          "evidence": {"text": "Human groupings of short questions disagree; there is no single correct clustering",
                       "level": "estimate"},
          "mitigation": "Measure agreement between annotators first and compare methods against that ceiling, as the "
                        "closest work does"},
         {"type": "weak_baseline", "status": "checked_ok",
          "evidence": "TF-IDF and plain sentence-embedding baselines alongside LLM similarity"},
         {"type": "model_selection_on_test", "status": "found",
          "evidence": {"text": "Tuning thresholds on the evaluated sessions inflates agreement", "level": "estimate"},
          "mitigation": "Tune on held-out sessions; report results for every threshold"},
         {"type": "pretraining_contamination", "status": "not_applicable"}],
     "decision": {"verdict": "conditional_go",
                  "rationale": "A clear, measurable extension with positive evidence of the gap; the main risk is that "
                               "the master's project covers more than its abstract says.",
                  "conditions": ["Read the full text of the master's project; if it already used live lecture "
                                 "questions or analysed the largest cluster, reframe this as a replication on new data"],
                  "unresolved_risks": ["Annotation effort and agreement", "Small, single-course data"]}},
    {"title": "Does the starry sky help instructors more than a ranked list?",
     "question_type": "novel", "derived_from": ["L5", "L6"], "category": "unverified_novelty_hypothesis",
     "mode": "original", "status": "kept",
     "research_question": "With the same clustered questions, do instructors identify the most widely shared questions "
                          "faster and more accurately with a frequency-encoded constellation view than with a ranked "
                          "list?",
     "motivation": "Clustering dashboards were evaluated with interviews only "
                   "[@srivastava2025learnlens; @liu2026asknow].",
     "supporting_papers": ["srivastava2025learnlens", "liu2026asknow"],
     "closest_existing_work": [
         {"key": "srivastava2025learnlens", "how_it_differs": "Middle-school open responses, word clouds and "
          "summaries; qualitative evaluation, no list baseline", "read_level": "abstract", "overlap": "partial"},
         {"key": "liu2026asknow", "how_it_differs": "Lists topics; no comparison of visualisations",
          "read_level": "full_text", "overlap": "partial"}],
     "gap_evidence": [
         {"text": "Both dashboards were evaluated qualitatively, without a list baseline", "level": "verified",
          "sources": ["srivastava2025learnlens", "liu2026asknow"]}],
     "contribution": "A controlled within-subjects comparison of a constellation view and a ranked list on time, "
                     "accuracy and workload.",
     "novelty": {"confidence": "very_low",
                 "uncertainty": "General visualisation research on size-encoded displays versus sorted lists may "
                                "already predict the result; that literature was not searched. " + LIMITED,
                 "signal": "no_close_match_in_this_search", "ceiling": "low",
                 "challenge_searches": ["visualization student questions instructor",
                                        "real-time classroom dashboard visualization questions",
                                        "instructor dashboard student confusion visualization",
                                        "question cluster visualization user study",
                                        "teacher orchestration dashboard evaluation"]},
     "feasibility": [{"text": "12 to 16 instructors or TAs, recorded question sets, about 30 minutes each",
                      "level": "estimate"}],
     "methodological_risks": [
         {"type": "confound", "status": "found",
          "evidence": {"text": "A sorted list makes the largest group trivially visible; a star map may look better "
                               "but be slower", "level": "estimate"},
          "mitigation": "Include tasks beyond finding the largest group (related questions, the second most common "
                        "topic); counterbalance order"},
         {"type": "weak_baseline", "status": "checked_ok", "evidence": "Ranked list with counts as the baseline"},
         {"type": "insufficient_runs", "status": "found",
          "evidence": {"text": "Small participant pool", "level": "estimate"},
          "mitigation": "Within-subjects design; report effect sizes with intervals"}],
     "decision": {"verdict": "conditional_go",
                  "rationale": "A useful secondary study, but a list may win on pure find-the-biggest tasks.",
                  "conditions": ["Check visualisation research on bubble charts versus sorted bar charts before "
                                 "running the study"],
                  "unresolved_risks": ["The result may be predictable from perception research"]}},
    {"title": "Build an app that clusters live questions and shows the most frequent ones",
     "question_type": "answered", "derived_from": ["L1"], "category": "well_studied", "mode": "original",
     "status": "rejected",
     "revision_note": "AskNow already deployed embedding-based grouping of live student questions with a view of the "
                      "five most frequent topics in three courses; building it again is engineering, not a research "
                      "contribution.",
     "research_question": "Can an LLM-based system cluster live student questions and show instructors the most "
                          "common ones?",
     "motivation": "The original project idea.",
     "supporting_papers": ["liu2026asknow"],
     "closest_existing_work": [{"key": "liu2026asknow", "how_it_differs": "Same function; differs only in visual "
                                "design (list modes versus a star map)", "read_level": "full_text",
                                "overlap": "same_experiment"}],
     "gap_evidence": [],
     "contribution": "None as research; the app remains valuable as the instrument for questions 1 to 3.",
     "novelty": {"confidence": "very_low", "uncertainty": "Already demonstrated by AskNow.",
                 "signal": "no_close_match_in_this_search", "ceiling": "low",
                 "challenge_searches": ["clustering student questions evaluation", "student question deduplication"]},
     "decision": {"verdict": "no_go", "rationale": "Already done as a system; use the app to answer questions 1 to 3."}},
]

report = {
    "type": "opportunity_report", "schema_version": 3,
    "title": "Research opportunities for a live-lecture question clustering app (starry sky)",
    "date": "2026-10-19",
    "constraints": {"field": "educational technology, HCI and NLP", "project": "classroom app clustering student questions",
                    "hardware": "CPU or one consumer GPU with 8 GB VRAM", "time_budget_weeks": 8,
                    "experience": "undergraduate, comfortable with Python",
                    "defaults_used": ["hardware", "time_budget_weeks", "experience"]},
    "search_log": {
        "sources_ok": ["crossref", "huggingface"],
        "sources_failed": [{"source": "openalex", "reason": "keyless daily quota exhausted"},
                           {"source": "semantic_scholar", "reason": "rate_limited (HTTP 429)"},
                           {"source": "arxiv", "reason": "partly rate-limited (map and targeted search)"}],
        "strategies": ["keyword", "surveys", "negative", "comparisons", "critique", "reproducibility", "recent",
                       "design-based queries", "citation expansion", "ordinary web search"],
        "queries": ["student questions lecture clustering", "audience response system questions",
                    "classroom question aggregation", "similar student questions grouping",
                    "LLM clustering student questions", "classroom backchannel questions",
                    "live lecture question upvoting", "clustering student questions", "student question deduplication",
                    "large lecture anonymous questions", "summarizing student questions LLM",
                    "student questions MOOC forum clustering", "instructor question prioritization"],
        "n_retrieved": 544, "date": "2026-10-19",
        "notes": ["The closest paper (AskNow) was found only by ordinary web search; no API search or challenge "
                  "retrieved it.",
                  "A web result gave AskNow's arXiv ID as 2511.01248, but the arXiv API returns a different paper "
                  "(FocusView) for that ID, so AskNow is cited by its ACM DOI.",
                  "Eleven ordinary web searches supplemented the API searches."]},
    "papers": papers, "evidence_ledger": ledger, "opportunities": opps,
    "datasets": [
        {"name": "EduVidQA", "url": "https://huggingface.co/datasets/vqamaster/EduVidQA",
         "purpose": "possible public source of student questions on lecture videos",
         "size": "2.15 GB including transcripts (rows not reported)", "format": "json", "license": "mit",
         "access": "open", "preprocessing": "keep real-world questions only; drop transcripts",
         "suitability": "no vote counts; mixes synthetic and real questions", "verified": True},
        {"name": "Dataset MOOC Forum edX", "url": "https://zenodo.org/records/5115573",
         "purpose": "forum questions from three programming MOOCs", "size": "556 MB (one MongoDB dump)",
         "format": "mongo", "license": "cc-by-4.0", "access": "open", "preprocessing": "schema not documented",
         "suitability": "forum posts, not live lecture questions; whether votes are included is not reported",
         "verified": True}],
    "sections": {
        "summary": "The app itself has largely been built before: AskNow [@liu2026asknow] groups live student questions "
                   "by embedding similarity and shows instructors the most frequent clusters, in a deployment with 117 "
                   "students. Its paper, read in full, never checks whether the clusters are right, whether the most "
                   "frequent clusters are the ones instructors most need, or how frequency compares with upvoting. "
                   "Those omissions are where a student paper can contribute, with the app as the research instrument.",
        "well_explored": ["Audience response systems and clickers in lectures (a large literature, mostly engagement "
                          "and perception studies)",
                          "Anonymous digital backchannels in lectures [@du2012classcommons; @iosub2025askaway]",
                          "Duplicate and related question detection in course forums and question banks "
                          "[@chowdhary2022qdup; @onan2020moocclustering]",
                          "LLM answering of student questions [@miroyan2025edison; @ray2025eduvidqa]"],
        "recommendation": "Make question 1 (upvotes versus cluster size) the main hypothesis, with question 2 "
                          "(clustering accuracy) as the necessary first step, since a star's brightness only means "
                          "something if the clusters are right. Question 3 is optional. The app collects the data for "
                          "all three."},
    "limitations": ["OpenAlex and Semantic Scholar were unavailable and arXiv was rate-limited for part of the search; "
                    "ACM Digital Library venues were not searched directly",
                    "Most papers were read at abstract level; only AskNow was read in full",
                    "Novelty confidence is very low for every question"],
}
(HERE / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("written", len(papers), "papers")
