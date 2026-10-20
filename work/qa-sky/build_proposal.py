"""Research proposal for the starry-sky project. Papers are copied from the verified opportunity report."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
opp = json.loads((HERE / "report.json").read_text(encoding="utf-8"))
keep = ["liu2026asknow", "mangado2025grouping", "wei2025kcluster", "onan2020moocclustering", "chowdhary2022qdup",
        "srivastava2025learnlens", "du2012classcommons", "iosub2025askaway", "ray2025eduvidqa"]
papers = [{k: v for k, v in p.items() if k != "verification"} for p in opp["papers"] if p["key"] in keep]

V, E, S = "verified", "estimate", "speculative"

proposal = {
    "problem_statement": [
        {"text": "In large lectures, many students have the same confusion but few ask. Live question tools let students "
                 "ask anonymously, and the instructor then has to decide which questions to answer first.",
         "level": E},
        {"text": "AskNow groups live student questions by embedding similarity and shows instructors the five most "
                 "frequent groups, but its paper does not evaluate whether the groups are correct, whether the most "
                 "frequent groups are the ones instructors most need, or how frequency compares with upvoting "
                 "[@liu2026asknow].", "level": V, "sources": ["liu2026asknow"]},
        {"text": "Widely used tools rank questions by upvotes instead. Upvotes measure visible agreement with a question "
                 "someone else wrote; the number of students who independently ask the same thing measures how widely "
                 "the confusion is shared. Which signal better tells an instructor what to answer has not been tested "
                 "in any paper this search found.", "level": E},
    ],
    "background": [
        {"text": "AskNow: embedding-based grouping of live lecture questions (threshold K-means on text-embedding-3-small) "
                 "with a top-5 topic view; one-week deployment in three CS courses with 117 students; clustering "
                 "quality and threshold not reported [@liu2026asknow].", "level": V, "sources": ["liu2026asknow"]},
        {"text": "Grouping of 93 student questions on one topic with six multilingual encoders, UMAP and HDBSCAN, scored "
                 "against six instructors and eight students with AMI, ARI and V-measure; tuned clustering approached the "
                 "lower bound of human agreement [@mangado2025grouping].", "level": V, "sources": ["mangado2025grouping"]},
        {"text": "LLM-induced question similarity clusters assessment items into knowledge components "
                 "[@wei2025kcluster]; embedding clustering finds question topics in MOOC forums [@onan2020moocclustering]; "
                 "unsupervised pipelines detect duplicate questions in question repositories [@chowdhary2022qdup]. None "
                 "of these used short questions typed during a live lecture.", "level": V,
         "sources": ["wei2025kcluster", "onan2020moocclustering", "chowdhary2022qdup"]},
        {"text": "Teacher dashboards that summarise or cluster student input were evaluated with interviews, not with "
                 "measured task accuracy [@srivastava2025learnlens]. Classroom backchannels and anonymous question forms "
                 "are established practice [@du2012classcommons; @iosub2025askaway].", "level": V,
         "sources": ["srivastava2025learnlens", "du2012classcommons", "iosub2025askaway"]},
    ],
    "research_question": [
        "RQ1 (Study 1). How well do lexical, sentence-embedding and LLM-based clusterings of live lecture questions agree "
        "with human groupings, and how often do they identify the same largest group (the brightest star) as humans?",
        "RQ2 (Study 2). When the same questions are both grouped and upvoted, does ranking groups by the number of "
        "distinct students who asked them match the instructor's priorities better than ranking by upvotes?",
    ],
    "hypothesis": [
        {"text": "H1 (Study 1): sentence-embedding clustering reaches an AMI with the consensus human grouping that lies "
                 "within the range of agreement between individual annotators, and exceeds TF-IDF clustering by at least "
                 "0.05 AMI on average across sessions.", "level": S},
        {"text": "H2 (Study 2): ranking question groups by the number of distinct askers gives a higher NDCG@5 against "
                 "the instructor's blind priority ranking than ranking by total upvotes.", "level": S},
    ],
    "falsification": [
        "Fixed before any data is analysed.",
        "H1 is supported if mean AMI (embedding vs consensus) is at least the lowest pairwise human AMI and the paired "
        "difference to TF-IDF has a 95% bootstrap confidence interval above 0.05; rejected if embedding AMI is below "
        "the lowest human-human AMI in most sessions or the interval for the difference includes or lies below 0; "
        "otherwise inconclusive.",
        "H2 is supported if the 95% bootstrap confidence interval (resampling sessions, then groups) of NDCG@5(size) "
        "minus NDCG@5(upvotes) lies above 0; rejected if it lies below 0; inconclusive if it contains 0. With few "
        "sessions an inconclusive result is likely and will be reported as such.",
    ],
    "project_type": "Original study (Study 2) built on an extension (Study 1) of published question-grouping "
                    "evaluations to live lecture questions. The app is the data-collection instrument, not the "
                    "contribution.",
    "dataset": [
        {"text": "Primary data: questions collected with the app in real lectures. Target: at least 4 sessions and "
                 "300 questions in total; 8 sessions if available. Stored per question: text, session, anonymous "
                 "student ID (random per session), submission time, phase, and upvotes with voter IDs.", "level": E},
        {"text": "Each session has two phases: an ask phase in which students submit questions privately (no feed "
                 "visible), and a short voting phase in which all questions are shown in random order and students "
                 "upvote. Both signals are then measured on the same questions, and the feed cannot suppress repeat "
                 "asking.", "level": E},
        {"text": "Fallback for Study 1 if no class is available: real-world (not synthetic) questions from EduVidQA, "
                 "grouped by lecture video; it has no upvotes, so Study 2 cannot use it.", "level": E},
        {"text": "Ethics: university ethics approval and informed consent before any collection; participation never "
                 "affects grades; no names stored; questions released only after review for identifying content.",
         "level": E},
    ],
    "methodology": [
        "Study 1 (RQ1). Three annotators (the instructor or TA, and two others; at least one not the project author) "
        "group each session's questions independently with a written guideline: two questions belong together if one "
        "answer from the instructor would resolve both. A consensus grouping is formed by majority co-assignment.",
        "Clustering methods, all with the same distance-threshold agglomerative clustering so only the representation "
        "differs: (a) TF-IDF cosine; (b) sentence embeddings from two small open models (e.g. all-MiniLM-L6-v2 and "
        "BGE-small); (c) an LLM pair judge ('would one answer resolve both questions?') turned into a similarity "
        "graph; (d) UMAP plus HDBSCAN on embeddings, as in the closest prior work.",
        "Thresholds are tuned by leave-one-session-out: tuned on all other sessions, evaluated on the held-out one.",
        "Study 2 (RQ2). After each lecture the instructor ranks the consensus question groups by how important they "
        "are to answer for the whole class, without seeing group sizes or votes (groups shown in random order). "
        "Rankings by each signal are then compared with this ranking.",
    ],
    "variables": [
        "Independent (Study 1): question representation and clustering method; distance threshold (swept).",
        "Independent (Study 2): prioritisation signal: distinct askers per group; total upvotes; upvotes from distinct "
        "students; distinct askers plus distinct upvoters; most recent first; random.",
        "Dependent: AMI, ARI and V-measure against each annotator and the consensus; largest-group match; NDCG@5 and "
        "precision@3 against the instructor ranking.",
        "Controlled: same questions, same preprocessing (lower-casing, no stemming), same clustering algorithm across "
        "representations, same tuning protocol.",
    ],
    "confounds": [
        "Upvote position and time bias: questions shown first or longer collect more votes. Controlled by the random "
        "order in the voting phase and a fixed voting window.",
        "A visible feed suppresses repeat asking (students upvote instead of re-asking), which would bias group sizes. "
        "Controlled by the private ask phase.",
        "Instructor knowledge of counts: the ranking is made blind to sizes and votes.",
        "Annotator influence: annotators group independently before any consensus; agreement is reported.",
        "Threshold tuned on the test session: avoided by leave-one-session-out tuning.",
        "Duplicate submissions by the same student count once toward distinct askers.",
    ],
    "baselines": [
        "Study 1: TF-IDF clustering (lexical baseline); a trivial baseline that puts every question in its own group; "
        "the human-human agreement range as the ceiling.",
        "Study 2: recency ordering and random ordering, besides the two signals being compared.",
    ],
    "metrics": [
        "AMI as the primary clustering metric (corrected for chance, comparable across sessions with different numbers "
        "of groups); ARI and V-measure as secondary, as in the closest prior work.",
        "Largest-group match: the largest machine group and the largest consensus group overlap with Jaccard at least "
        "0.5.",
        "Threshold stability: how many of the top-3 groups stay the same across neighbouring thresholds.",
        "NDCG@5 (primary) and precision@3 against the instructor ranking.",
    ],
    "procedure": [
        "1. Week 1: ethics application; build the app's minimum version (two phases, anonymous IDs, logging, export).",
        "2. Week 2: pilot in one session or with volunteers; write and test the annotation guideline.",
        "3. Weeks 3-5: collect sessions; annotators group questions within a week of each session; instructor rankings "
        "right after each lecture.",
        "4. Week 6: Study 1 analysis (all methods, thresholds, agreement).",
        "5. Week 7: Study 2 analysis on the consensus groups.",
        "6. Week 8: write the paper; release code and the anonymised data if consent allows.",
        "Minimum version if sessions fall through: Study 1 on EduVidQA real-world questions plus any collected sessions; "
        "Study 2 reported as a protocol with pilot data.",
    ],
    "statistics": [
        "Sessions are the unit of replication. Report per-session values and the mean with a 95% bootstrap confidence "
        "interval (10,000 resamples of sessions). Compare methods and signals with paired differences on the same "
        "sessions.",
        "Clustering methods with a random element (UMAP, HDBSCAN) are run with 5 seeds; report the spread.",
        "Two pre-specified primary comparisons (H1, H2); everything else is labelled exploratory. No significance claims "
        "beyond the confidence intervals; with 4-8 sessions the study is exploratory.",
        "Inter-annotator agreement (pairwise AMI) is reported before any method results.",
    ],
    "feasibility": [
        {"text": "Compute: clustering a few hundred short questions with small embedding models runs on a laptop CPU in "
                 "minutes; an LLM pair judge with a small local model fits an 8 GB GPU, or can be skipped.", "level": E},
        {"text": "Main cost is people: about 4-8 lecture sessions, 3 annotators at roughly 30-60 minutes per session, "
                 "and an instructor's 10-minute ranking after each lecture.", "level": E},
        {"text": "Main schedule risk: ethics approval time. Apply in week 1; the fallback keeps Study 1 possible.",
         "level": E},
    ],
    "contribution": [
        "The first measured comparison, to our knowledge, of upvotes and question-group size as signals of what "
        "instructors should answer, with an interface design (private ask phase) that measures both on the same "
        "questions. Novelty confidence is very low: ACM venues still need a direct search.",
        "An evaluation of question grouping on live lecture questions, including how stable the top group is, which "
        "the closest deployed system did not report.",
        "An anonymised dataset of live lecture questions with groupings, upvotes and instructor priorities, if consent "
        "allows release.",
    ],
    "risks": [
        "Too few sessions: results stay exploratory; report per session and widen the confidence intervals honestly.",
        "Low annotator agreement: then the 'correct grouping' is ill-defined; report agreement as a finding and "
        "evaluate against each annotator separately.",
        "Few questions per session (common in small classes): pool sessions for Study 1 and treat Study 2 as a pilot.",
        "A paper found later that already compares upvotes and group size: reframe Study 2 as a replication in a new "
        "setting.",
        "Privacy: questions can reveal identity or health information; review before any release.",
    ],
}

report = {
    "type": "research_proposal",
    "title": "Brightest stars: do question clusters or upvotes better show what a lecture class needs answered?",
    "date": "2026-10-19",
    "constraints": {"field": "educational technology, HCI and NLP", "project": "starry-sky live question app",
                    "hardware": "CPU or one consumer GPU with 8 GB VRAM", "time_budget_weeks": 8,
                    "experience": "undergraduate, comfortable with Python",
                    "class_access": "unknown at time of writing; fallback included",
                    "defaults_used": ["hardware", "time_budget_weeks", "experience"]},
    "search_log": opp["search_log"],
    "papers": papers,
    "datasets": [d for d in opp["datasets"] if d["name"] == "EduVidQA"],
    "proposal": proposal,
    "limitations": [
        "The literature search had OpenAlex and Semantic Scholar unavailable and did not search the ACM Digital Library "
        "directly; the gap behind Study 2 rests on absence of evidence.",
        "Most cited papers were read at abstract level; only AskNow was read in full. Read the master's project "
        "(mangado2025grouping) in full before finalising Study 1.",
        "Effect sizes and session counts are estimates; nothing has been run.",
    ],
}
(HERE / "proposal.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("written", len(papers), "papers")
