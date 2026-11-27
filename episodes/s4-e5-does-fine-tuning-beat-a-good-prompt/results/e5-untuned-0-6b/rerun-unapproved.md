# An unapproved second run of the pilot, 23 November 2026

The pilot (attempt 1) succeeded at 22:00 UTC and was recorded. A second run of the same job then
started at 22:07 UTC and finished at 22:22 UTC (`rerun-unapproved-job_result.json`).

**Why it ran:** the notebook's `JOB_DIR` was changed in the browser to the next job's folder, but
Colab failed to save that edit ("updated remotely or in another tab"). The saved notebook, still
pointing at this folder, was run again. The copy of `job.json` on Drive still showed attempt 1 as
launched, because only the local record had been updated, so the notebook's guard let it run.

**What it changed:** nothing in the record. It cost no money (free Colab) and was not used for
any result. Its predictions were compared with the recorded ones: **identical on all 200 dev and
all 600 test items**, so greedy decoding on the pinned weights reproduces exactly.

**Fixes:** the Drive copy of this job's `job.json` is renamed so the folder cannot run again, and
each later job gets its own notebook copy with `JOB_DIR` already set.
