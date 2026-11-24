# Fine-tuning readiness checklist

A tool from Season 4, started in E6 and completed in E10. Work through it before you commission
a fine-tuning project. Each line says what to check and, where Season 4 measured it, what the
Halvard tasks showed. Halvard Home is invented; its numbers are one worked case, not a rule.

**Status: draft.** Sections 1 to 5 carry Season 4's numbers up to E7; section 6 is written in E10.

## 1. Is tuning the right fix?

- [ ] **Name the gap.** If the model lacks facts, retrieve them (Season 2). Tune only for
      behaviour: a format, a routing rule, a house style. *(S4 E1: the cheapest model read every
      product correctly and lost items on Halvard's rules.)*
- [ ] **Try the cheap rungs first,** and measure each: written definitions, then examples, then
      an enforced format. *(S4 E2: definitions alone took triage from 521 to 587 of 600.)*
- [ ] **Know what tuning would buy.** A tuned small model may match a good prompt rather than beat
      it; the gain may be a shorter prompt and a smaller model, not more right answers.
      *(S4 E5: tuned 592 against 587 for the prompt, not distinguishable, with an eighth of the
      input.)*

## 2. How much labelled data do you need?

- [ ] **Label a few hundred examples first and draw the curve** before labelling thousands.
      *(S4 E6: fully right out of 600 was 24 untuned, 60 at 50 examples, 450 at 200, 589 at 800
      and 592 at 1,600, against 587 for the best prompt. 800 matched the prompt; 200 did not.)*
- [ ] **Buy more data only where the curve is still rising.** *(S4 E6: 800 to 1,600 added three
      items, not distinguishable; doubling the data doubled the training time for nothing.)*
- [ ] **Check the valid-output rate at small sizes.** A model tuned on too few examples learns
      the output's shape before its allowed values. *(S4 E6: at 50 examples, 67 of 600 replies
      were valid and no incident was flagged.)*
- [ ] **Check the rare cases are in every training set,** not just the total. *(Halvard's safety
      items are about 10% of each set: 7 in 50, 22 in 200, 88 in 800.)*

## 3. Are the labels right?

- [ ] **Write the labelling rules down first,** the same rules the model is later judged by.
- [ ] **Check labels with a second, independent labeller,** and count disagreements.
      *(Halvard's data: a model from a third provider relabelled every item blind; disagreements
      were discarded and counted.)*
- [ ] **Know what discarding does.** Dropping the items two labellers disagree on leaves the
      easy ones. *(Halvard: 54 messages naming non-existent products were discarded and 8 kept,
      so that hard case is under-represented.)*
- [ ] **Check the target outputs for habits, not just facts.** Tuning copies whatever the
      training targets do, including what no rule asks for. *(S4 E7: 459 of 600 target replies
      restated the customer's question; the tuned model did it in 260 of 300, and a style judge
      marked it down.)*
- [ ] **Have a person check a sample** of the final test set before it is frozen. *(Halvard: 50
      triage and 20 reply items, no errors found; that bounds the error rate at about 6% and
      15%, not zero.)*

## 4. Is there a test set nobody tuned on?

- [ ] **Split before you look:** train to learn from, dev to make choices on, test to report.
- [ ] **Freeze the test set** and record its hash, so any change is visible. *(Halvard:
      `datasets/halvard-tasks/MANIFEST.json`, checked by a test.)*
- [ ] **Never choose a prompt, a model or a setting on test.**
- [ ] **Remove near duplicates** between train and test, by a stated rule.

## 5. Can you reproduce and account for every training run?

- [ ] **Record each job:** base model and its exact version, settings, seed, data hash, and the
      resulting model's hash. *(Season 4: `results/<arm>/job.json` in each episode.)*
- [ ] **Never relaunch a run silently.** Training is not cached like a response. *(S4 E5: one
      accidental rerun, logged; it reproduced every answer, because prediction was greedy on
      pinned weights.)*
- [ ] **Know where the training data goes.** Tuning on a provider's service sends your examples
      to that provider. *(Season 11 covers this.)*

## 6. What does tuning break?

*Written in E10.*
