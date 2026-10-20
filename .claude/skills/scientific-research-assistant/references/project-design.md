# Workflow C: Research project design

Turn an idea or a chosen paper into a plan whose result will be interpretable whichever way it comes out. Output type: `research_proposal` (`references/report-schema.md`).

## 1. Problem, question, hypothesis

- **Problem statement:** what is unknown or unverified, and who needs to know. Cite the papers that establish it.
- **Research question:** one question that names the comparison, the setting and the measure. "Does A outperform B on task T measured by M under condition C?"
- **Hypothesis:** a prediction that data could contradict, with its direction and, where possible, a size ("A exceeds B by at least 1 accuracy point").
- **Falsification rule:** written before any run: which observation supports the hypothesis, which rejects it, and which is inconclusive.
- **Project type:** original, reproduction, replication or extension.

## 2. Choose the simplest valid method

Match the method to the question, not to what is fashionable.

| Question type | Start with |
| --- | --- |
| Does a reported result hold? | the original code and protocol, more seeds |
| Is a complex method needed? | the strongest simple baseline, tuned with the same budget |
| Is there a relationship between variables? | descriptive statistics, correlation, regression |
| Does a treatment change an outcome? | controlled comparison with a significance test and effect size |
| Classification or regression on small tabular or text data | linear or logistic regression, tree ensembles, bag-of-words models |
| Does a method transfer to a new setting? | the existing method unchanged on the new data, then one adaptation |

Use deep learning when simpler models have been shown inadequate for the task or the question is about deep models. Say in the proposal why the chosen method is sufficient and what a more complex one would add. A weak baseline makes any result uninterpretable, so always include at least one simple, well-tuned baseline and, where they exist, the published numbers.

## 3. Variables and confounds

- **Independent variables:** what you change (method, data size, a hyperparameter).
- **Dependent variables:** what you measure (metrics, run time, memory).
- **Controlled variables:** what is held fixed (data splits, preprocessing, tuning budget, hardware).
- **Confounds to rule out:** unequal hyperparameter tuning between methods; different preprocessing or tokenisation; different pretrained resources; test-set selection; implementation differences between frameworks; dataset version drift.

## 4. Data and leakage

Verify every dataset with `dataset-verify` and report licence, size and access. Then:

- Use published splits when they exist; otherwise create fixed, seeded, stratified splits and publish them.
- Keep the test set untouched until the final evaluation. Tune on validation data only.
- Fit all preprocessing (vocabulary, scaling, feature selection) on training data only.
- Check for duplicates and near-duplicates across splits; group related items (same patient, author, document) into the same split.
- For time-ordered data, split by time.
- Methods that see test inputs during training (transductive setups) must be compared with care against inductive ones; say which each method is.

**If no suitable dataset exists**, synthetic data is acceptable when: the generating process is fully specified and seeded; its assumptions are stated and justified; conclusions are limited to what the generator can support; and, where possible, a small real sample checks the findings. Do not present synthetic results as evidence about real-world performance.

## 5. Metrics and statistics

- Choose the metric the literature uses for the task, plus one that exposes its blind spot (macro-F1 beside accuracy for imbalanced classes).
- Run several random seeds (five is a reasonable default; three is the minimum for a spread) and report mean and standard deviation or a confidence interval.
- Compare methods with a test suited to the design: paired tests over seeds or folds, bootstrap confidence intervals on the test set, McNemar's test for paired classifications. Correct for multiple comparisons when testing many pairs.
- Report effect sizes, not only p-values, and state what difference counts as practically meaningful.
- Decide the analysis before seeing test results.

## 6. Procedure and budget

Write numbered steps someone else could follow: environment setup with pinned versions, data preparation, baseline runs, main runs, analysis. Estimate time and compute per step and label them as estimates. Include a minimum viable version of the project (what is reported if only half the time is available) and the main risks with a fallback for each.

## 7. Proposal contents

Title; problem statement; literature background; research question; hypothesis and falsification rule; dataset; methodology (project type, variables, confounds and leakage controls); baselines; evaluation metrics; experimental procedure; statistical analysis; compute and time; expected contribution; limitations and risks; references. Every reference must pass `verify-refs`.
