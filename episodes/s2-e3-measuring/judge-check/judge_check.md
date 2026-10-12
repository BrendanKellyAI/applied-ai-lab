# Judge check: marking sheet

10 items, each shown exactly as the judge saw it. The judge's verdicts are not shown. For each item, fill in `declined`, `correct` and `faithful` in `judge_check.csv` with y or n, and add a note where the call was close.

Mark by the same rules the judge was given:

> You grade one answer from a question-answering system for Halvard Home, an appliance maker.
>
> You are given:
> - the question, with any earlier turns of the conversation;
> - whether the question can be answered from the company's documents;
> - a reference answer, written by a person who knows the documents;
> - the passages the system was given;
> - the system's answer.
>
> Decide three things.
>
> declined: true if the answer says it cannot find or cannot give the answer, and gives no
> answer of its own. False if it gives an answer, even a hedged one.
>
> correct: if the question can be answered, true when the answer gives the same facts as the
> reference answer; extra detail is fine if it is not wrong. If the question cannot be answered,
> true only when the answer declines.
>
> faithful: true when every claim in the answer is supported by the passages the system was
> given. Judge against the passages, not against the reference answer or your own knowledge. An
> answer that declines and makes no claim is faithful.

---

## 1. POL-SINGLE-035

Question: What happens if my Fenwick cooker hood takes a long time to fix?

Can the question be answered from the documents: yes

Reference answer: If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement.

Passages given to the system:
[P1] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P2] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P3] Warranty
checks that you can safely carry out yourself. You do not need to remove covers, handle wiring or dismantle the appliance to make a claim.

Stop using the Fenwick cooker hood if it produces smoke, smells of burning or appears electrically unsafe. Disconnect it from the electricity supply if you can do so safely. Tell us about the concern when you contact us so that we can arrange appropriate support.

We confirm a fault through the information you provide, remote assessment or an engineer’s inspection, as appropriate. We will tell you when the fault has been confirmed and whether it is covered. If we decline cover, we will explain the reason clearly and give you the opportunity to provide further information.

Warranty cover applies to faults arising from defective materials or workmanship under normal household use. It does not cover damage caused by misuse, accidental damage, unsuitable installation or alterations that cause the fault. A fault unrelated to such circumstances will still be assessed fairly.

Where an engineer needs to visit, we will agree an appointment with you. Please make sure the engineer can safely reach the Fenwick cooker hood and its electrical connection. Let us know about access restrictions or support needs when the appointment is arranged.

A warranty repair to the Fenwick cooker hood is completed within 37 working days of the fault

[P4] Warranty
checks that you can safely carry out yourself. You do not need to remove covers, handle wiring or dismantle the appliance to make a claim.

Stop using the Fenwick cooker hood if it produces smoke, smells of burning or appears electrically unsafe. Disconnect it from the electricity supply if you can do so safely. Tell us about the concern when you contact us so that we can arrange appropriate support.

We confirm a fault through the information you provide, remote assessment or an engineer’s inspection, as appropriate. We will tell you when the fault has been confirmed and whether it is covered. If we decline cover, we will explain the reason clearly and give you the opportunity to provide further information.

Warranty cover applies to faults arising from defective materials or workmanship under normal household use. It does not cover damage caused by misuse, accidental damage, unsuitable installation or alterations that cause the fault. A fault unrelated to such circumstances will still be assessed fairly.

Where an engineer needs to visit, we will agree an appointment with you. Please make sure the engineer can safely reach the Fenwick cooker hood and its electrical connection. Let us know about access restrictions or support needs when the appointment is arranged.

A warranty repair to the Fenwick cooker hood is completed within 37 working days of the fault

[P5] Engineer service manual (extract)
where required, test results and any remaining concerns. Leave the work area safe and give the customer clear operating advice relevant to the repair.

## Fenwick cooker hood

### Internal repair limits

Engineers may fit parts to the Fenwick cooker hood worth up to £282.00 without approval. Apply this limit to the combined value of parts needed for the repair, not to each part separately. Check current internal parts pricing before committing stock or telling the customer that work can proceed.

If the proposed repair exceeds this allowance, stop and seek approval through the service authorisation process. Record the symptoms, diagnosis, proposed parts and reason for replacement. Do not split the repair across visits or job records to avoid approval. Keep the customer informed without promising an outcome that has not been authorised.

Before starting work, confirm that the appliance is the Fenwick cooker hood and check the service history. Ask the customer about the reported fault and any recent changes to its operation. Inspect accessible areas for damage, contamination, loose fixings and signs of overheating.

Isolate the electrical supply and verify that the appliance is safe before opening covers or handling internal components. Follow the approved isolation procedure and use suitable protective equipment. Do not bypass protective devices, alter wiring arrangements or improvise repairs to damaged electrical

System's answer:
Your Fenwick cooker hood warranty repair should be completed within **37 working days of the fault being confirmed**. [P3][P1]

If the repair takes **longer than 10 working days**, Halvard Home will lend you a replacement **at no charge while the warranty repair is being completed**. They will arrange the loan, explain safe use, organise any necessary installation, and agree how it will be collected. You won’t be responsible for disconnecting equipment that needs professional attention. [P1]

If there’s a problem with the repair arrangements, they will contact you and explain how they will resolve it. [P1]

---

## 2. SHARED-007

Question: Why does my Orrin heat pump warm my home gradually, and why do the radiators feel cooler than those connected to a boiler?

Can the question be answered from the documents: yes

Reference answer: Your Orrin heat pump warms your home gradually, so radiators may feel cooler than those connected to a boiler.

Passages given to the system:
[P1] Orrin heat pump heating slowly
Orrin heat pump heating slowly

Your Orrin heat pump warms your home gradually, so radiators may feel cooler than those connected to a boiler. This does not necessarily mean there is a fault.

If heating seems unusually slow or weak:

- Check that heating mode is selected and the timer allows heating now.
- Set the room thermostat 2°C above the current room temperature to request heat.
- Keep doors and windows closed while the home warms up.
- Check the outdoor unit for leaves or other loose debris blocking airflow. Do not remove covers or touch internal parts.

Cold weather and defrost cycles can temporarily reduce heat output. Avoid repeatedly switching the system off and on.

If performance remains poor, contact Halvard Home support or a qualified heat pump engineer.

[P2] Energy-saving settings for your Orrin heat pump
Energy-saving settings for your Orrin heat pump

Start with a room temperature of 19°C, then adjust it to suit your comfort. Lowering your usual setting by 1°C can reduce energy use, provided your home stays warm enough for everyone.

Use your heating schedule to match your routine. Heat pumps generally work best with steady temperatures, so try a small overnight reduction rather than switching the heating off completely.

If weather compensation is available, use it to help the system adjust heating water temperature as outdoor conditions change. Ask your installer to check the settings if rooms feel too warm or too cold.

Avoid changing hot water hygiene settings to save energy. These help keep stored water safe.

[P3] Orrin heat pump not switching on
Orrin heat pump not switching on

If your Orrin heat pump will not switch on, start with these checks:

- Check that the wall controller is on and its display is lit. If it uses batteries, replace them if the display is blank.
- Select heating mode and set the target temperature 2°C above the current room temperature.
- Check whether a timer or holiday setting is preventing heating.
- Make sure the heat pump’s power switch is on, provided it is safe to access.

After changing the settings, wait five minutes before checking again. Avoid repeatedly switching the power off and on.

If the unit still does not start, contact Halvard Home support. Do not remove covers or touch wiring. If you notice smoke or a burning smell, keep away and seek urgent assistance.

[P4] Using your Orrin in a holiday home
Using your Orrin in a holiday home

Keep your Orrin heat pump connected to the electricity supply while your holiday home is empty during cold weather. Switching it off at the mains can prevent frost protection from working.

Before leaving, clear leaves and other debris from around the outdoor unit so air can circulate freely. Check that doors and windows are closed.

If your controller has a holiday setting, use it to reduce heating while you are away. Otherwise, choose a lower room temperature rather than switching the heating off completely. Follow your installer’s advice on a suitable temperature for the property.

Allow time for the home to warm up when you return; heat pumps generally heat rooms gradually.

[P5] Orrin heat pump: first installation warning
Orrin heat pump: first installation warning

On a newly installed Halvard Home Orrin heat pump, E-6763 means air remains trapped in the heating circuit, preventing steady water flow during commissioning. The unit pauses heating to protect itself.

Leave the heat pump switched off using its normal power control and contact your installer. Ask them to complete the heating circuit purge, check that the isolation valves are fully open, and confirm that water flows correctly before restarting commissioning.

Do not remove the casing, loosen pipe connections or repeatedly restart the unit. Purging the circuit is an installer task, not a routine customer reset.

Once the installer has cleared the trapped air, they should restart commissioning and check that the warning does not return.

System's answer:
Your Orrin heat pump heats your home gradually rather than delivering the intense heat you may be used to from a boiler. Its radiators may therefore feel cooler, but this does not necessarily mean there’s a fault.

Heat pumps generally work best with steady temperatures, so allow time for rooms to warm up and avoid repeatedly switching the system off and on. Cold weather and defrost cycles can also temporarily reduce heat output.

---

## 3. ABSENT-005

Question: How often should the Mira robot vacuum be serviced?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Servicing and engineer visits
of your Mira robot vacuum, together with any advice recorded by a Halvard Home engineer. We will explain when a service is due when your schedule is agreed. If your circumstances change, contact us so we can review whether that schedule remains suitable.

A reminder is sent 7 weeks before a service is due. We use the contact details held on your service record, so please tell us if those details change. The reminder invites you to arrange a visit; it does not reserve an appointment or give us permission to enter your home.

You remain responsible for arranging the service, even if a reminder does not reach you. If you are unsure whether your Mira robot vacuum is due for servicing, contact Halvard Home. We can check the available service history and explain the next step without asking you to guess from how the appliance looks or sounds.

A routine service of the Mira robot vacuum takes about 164 minutes. This is an estimate for the service work, not a guaranteed appointment length. Access difficulties, the condition of the appliance or a fault requiring investigation may affect the visit. Your engineer will explain any change to the planned work.

A routine service of the Mira robot vacuum costs £115.00. We will confirm what the routine service includes when you book. Rep

[P2] Servicing and engineer visits
of your Mira robot vacuum, together with any advice recorded by a Halvard Home engineer. We will explain when a service is due when your schedule is agreed. If your circumstances change, contact us so we can review whether that schedule remains suitable.

A reminder is sent 7 weeks before a service is due. We use the contact details held on your service record, so please tell us if those details change. The reminder invites you to arrange a visit; it does not reserve an appointment or give us permission to enter your home.

You remain responsible for arranging the service, even if a reminder does not reach you. If you are unsure whether your Mira robot vacuum is due for servicing, contact Halvard Home. We can check the available service history and explain the next step without asking you to guess from how the appliance looks or sounds.

A routine service of the Mira robot vacuum takes about 164 minutes. This is an estimate for the service work, not a guaranteed appointment length. Access difficulties, the condition of the appliance or a fault requiring investigation may affect the visit. Your engineer will explain any change to the planned work.

A routine service of the Mira robot vacuum costs £115.00. We will confirm what the routine service includes when you book. Rep

[P3] Servicing and engineer visits
include clearing blocked suction paths, replacing worn brushes, repairing wheel assemblies and dealing with charging faults. Our support team will help identify the problem and explain whether it can be resolved at home or needs an engineer.

If the appliance stops unexpectedly, makes an unusual noise or leaves dirt behind, switch it off before inspecting it. Disconnect the charging dock from the mains before cleaning around its contacts. Do not reach into moving parts or open sealed covers.

Check accessible areas for trapped hair, thread and debris, following the cleaning instructions supplied with the appliance. A blocked brush or suction inlet can affect cleaning without indicating a mechanical fault. Stop if removing an obstruction would require force or dismantling.

Replace the filter of the Mira robot vacuum every 13 weeks. Use a compatible filter approved for the appliance, and fit it as described in the care instructions. An incorrectly fitted or damaged filter can reduce suction and allow dust into internal components.

Brushes can become tangled, bent or worn through normal use. If cleaning does not restore their movement, contact us for advice about replacement. Do not trim damaged bristles or alter the brush housing, as this may affect cleaning and safe operation.

Wheel problems may cause the appliance to drag, turn unexpectedly or struggle to move. Remove visible debris from accessible wheel areas

[P4] Servicing and engineer visits
include clearing blocked suction paths, replacing worn brushes, repairing wheel assemblies and dealing with charging faults. Our support team will help identify the problem and explain whether it can be resolved at home or needs an engineer.

If the appliance stops unexpectedly, makes an unusual noise or leaves dirt behind, switch it off before inspecting it. Disconnect the charging dock from the mains before cleaning around its contacts. Do not reach into moving parts or open sealed covers.

Check accessible areas for trapped hair, thread and debris, following the cleaning instructions supplied with the appliance. A blocked brush or suction inlet can affect cleaning without indicating a mechanical fault. Stop if removing an obstruction would require force or dismantling.

Replace the filter of the Mira robot vacuum every 13 weeks. Use a compatible filter approved for the appliance, and fit it as described in the care instructions. An incorrectly fitted or damaged filter can reduce suction and allow dust into internal components.

Brushes can become tangled, bent or worn through normal use. If cleaning does not restore their movement, contact us for advice about replacement. Do not trim damaged bristles or alter the brush housing, as this may affect cleaning and safe operation.

Wheel problems may cause the appliance to drag, turn unexpectedly or struggle to move. Remove visible debris from accessible wheel areas

[P5] Servicing and engineer visits
airs, replacement parts or work outside that scope are not automatically authorised by your booking. We will explain any proposed additional charges and seek your agreement before proceeding with chargeable work.

When booking, tell us about changes in performance, unusual noises, charging problems, visible damage or warning messages. Describe what happens and the circumstances in which it occurs. This helps us decide whether a routine service is appropriate or whether your Mira robot vacuum needs a fault assessment instead.

Do not wait for a scheduled service if you suspect that your Mira robot vacuum is unsafe. Stop using it if there is smoke, a burning smell, unusual heat or damage that could expose electrical parts. Follow the safety instructions supplied with the appliance and contact Halvard Home for advice.

Before the visit, make sure the engineer can reach the Mira robot vacuum and its charging area safely. Clear loose items from the working area and keep pets away while work is being carried out. Tell us about access restrictions or support needs when arranging the appointment so we can discuss suitable arrangements.

Please have the Mira robot vacuum available with the accessories relevant to any problem you have reported. Do not dismantle it or attempt to expose internal parts for the engineer. If it cannot be moved safely, leave it in place and explain the situation when we

System's answer:
The passages do not specify a fixed servicing interval. Servicing follows an agreed schedule; contact Halvard Home to check when your Mira robot vacuum is due. A reminder is sent 7 weeks before the service is due. [P1]

---

## 4. PARA-016

Question: What should I send the service team to get a replacement part for my cooktop?

Can the question be answered from the documents: yes

Reference answer: Include the photo, model details and a short description of what you need in your enquiry.

Passages given to the system:
[P1] Servicing and engineer visits
Problems with heating may be caused by unsuitable cookware, an electrical supply issue or a faulty internal component. The engineer will check the cause before recommending replacement parts. Work on your household wiring or electricity supply is not included in an appliance repair and may need a qualified electrician.

Unresponsive controls can result from moisture, residue, damage or a fault within the control assembly. Clean and dry the surface only as described in your user instructions. If the problem remains, leave internal checks to the engineer. Forcing the controls or applying cleaning liquid around damaged areas may worsen the fault.

A damaged glass surface will normally need replacement rather than a cosmetic repair. The engineer will also inspect the supporting components for damage. We will explain whether the appliance can be repaired safely and whether the condition of the surrounding worktop affects the proposed work.

Cooling fan faults and blocked ventilation can interfere with normal operation. Keep ventilation openings clear and avoid storing items where they could obstruct airflow. The engineer may need access beneath the hob to inspect these areas. Please remove loose belongings from the relevant cupboard before the visit.

Where an extraction filter is fitted, follow the cleaning and fitting instructions supplied with it. Replace the filter every 24 weeks. A clogged or incorrectly fitted filter can affect extraction performance.

[P2] Servicing and engineer visits
Problems with heating may be caused by unsuitable cookware, an electrical supply issue or a faulty internal component. The engineer will check the cause before recommending replacement parts. Work on your household wiring or electricity supply is not included in an appliance repair and may need a qualified electrician.

Unresponsive controls can result from moisture, residue, damage or a fault within the control assembly. Clean and dry the surface only as described in your user instructions. If the problem remains, leave internal checks to the engineer. Forcing the controls or applying cleaning liquid around damaged areas may worsen the fault.

A damaged glass surface will normally need replacement rather than a cosmetic repair. The engineer will also inspect the supporting components for damage. We will explain whether the appliance can be repaired safely and whether the condition of the surrounding worktop affects the proposed work.

Cooling fan faults and blocked ventilation can interfere with normal operation. Keep ventilation openings clear and avoid storing items where they could obstruct airflow. The engineer may need access beneath the hob to inspect these areas. Please remove loose belongings from the relevant cupboard before the visit.

Where an extraction filter is fitted, follow the cleaning and fitting instructions supplied with it. Replace the filter every 24 weeks. A clogged or incorrectly fitted filter can affect extraction performance.

[P3] Engineer service manual (extract)
If the proposed parts exceed the allowance, obtain approval through the internal service process before fitting them. Record what is required and why. If approval is unavailable, leave the appliance safe, explain the position without promising authorisation, and arrange the appropriate follow-up through the service team.

Record the diagnosis, parts fitted, approval details where applicable, and the outcome of the checks. Note any unresolved fault or restriction on use. Do not return an unsafe appliance to service; follow the isolation procedure and make sure the customer understands the safety advice given.

## Corra induction hob

### Internal repair limits

Confirm that the appliance is the Corra induction hob and check the reported fault against the service history. Inspect the glass, controls, supply connection and accessible wiring for damage. Record what you find before deciding whether an internal repair is appropriate.

Engineers may fit parts to the Corra induction hob worth up to £113.00 without approval. Apply this limit to the combined value of the parts needed for the repair, not to each part separately. Check current internal parts prices before proceeding. Do not split a repair into separate jobs to avoid approval.

If the required parts exceed the limit, stop and request authorisation through the service approval process. Include the symptoms, diagnostic findings, proposed parts

[P4] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 302 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

[P5] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 189 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

System's answer:
Send the service team:

- A description of the fault and what happens when you use the cooktop.
- Your delivery documents or repair confirmation, if available.
- If a previously fitted replacement part has failed, the repair details—especially the fitting date. [P4][P5]

The engineer will diagnose the problem before recommending replacement parts. If approval is needed, they will submit the symptoms, diagnostic findings and proposed parts through the service process. [P1][P3]

Report the fault promptly, and stop using the cooktop if you believe it may be unsafe. [P4][P5]

---

## 5. RESTRICT-STAFF-035

Question: What should I do if a complaint about the Lumen smart thermostat stays unresolved for too long?

Can the question be answered from the documents: yes

Reference answer: Complaints about the Lumen smart thermostat not resolved within 54 hours go to a team leader.

Passages given to the system:
[P1] Escalation playbook
explain the outcome clearly and tell the customer how to challenge it if they remain dissatisfied.

## Lumen smart thermostat

### Escalating a complaint

Listen to the customer’s account and acknowledge the effect the problem has had on them. Keep your language calm and straightforward. Check what outcome they want, without suggesting that escalation guarantees a refund, replacement or compensation. Avoid blaming the customer or dismissing their concerns about the Lumen smart thermostat.

Review the complaint record before asking the customer to repeat information. Confirm the reported fault, troubleshooting already attempted, advice given and commitments made. Record relevant contact details and the customer’s preferred contact method. Correct gaps or conflicting notes, making clear what the customer has confirmed and what remains uncertain.

Complaints about the Lumen smart thermostat not resolved within 54 hours go to a team leader.

Use the complaint record to check whether this escalation rule applies. Do not delay referral while waiting for the customer to repeat troubleshooting or supply information that is not essential to the handover. If responsibility for the complaint is unclear, ask a team leader to assign ownership.

Treat reports of overheating, burning smells, electrical damage or unsafe heating behaviour as safety concerns. Stop routine troubleshooting and seek urgent guidance through the safety escalation process. Do not ask the customer

[P2] Escalation playbook
to open the Lumen smart thermostat, touch exposed wiring or attempt repairs. If there is immediate danger, advise them to move to safety and contact the emergency services.

Prepare a clear handover explaining the unresolved issue, its impact, the action already taken and the customer’s requested outcome. Include relevant correspondence and supporting evidence through approved systems. Highlight safety concerns, accessibility needs and disputed facts. Distinguish the customer’s account from findings confirmed by staff.

The most a team leader may offer in compensation for the Lumen smart thermostat is £42.00.

Do not promise compensation or imply that the maximum is an automatic entitlement. Refer requests outside the team leader’s authority for further approval. Keep compensation discussions separate from any rights the customer may have.

Tell the customer that their complaint has been escalated, who will manage it and how they will receive an update. Record the handover and any agreed action. Check that the receiving colleague has accepted ownership so the complaint is not left unattended.

## Keel washing machine

### Escalating a complaint

Listen to the customer and confirm what has gone wrong with their Keel washing machine. Acknowledge the impact without guessing the cause or accepting liability. Explain that you will record their concerns and arrange the appropriate review. Use clear language and avoid

[P3] Lumen thermostat responding slowly
Lumen thermostat responding slowly

If your Lumen smart thermostat responds slowly or your home feels slow to warm up, check whether the delay affects the thermostat, the app or the heating itself.

For a simple heating check, set the target temperature 2°C above the room temperature shown on the display. Make sure heating is enabled and that a schedule has not lowered the target.

If changes made in the app take time to appear, check that your home Wi-Fi is working. Try adjusting the temperature directly on the thermostat to help identify a connection issue.

Keep furniture and curtains clear of the thermostat so air can circulate around it.

If the thermostat responds but the heating remains weak, contact your heating engineer. For persistent control delays, contact Halvard Home support.

[P4] Booking a Lumen engineer visit
Booking a Lumen engineer visit

To request an engineer visit for your Lumen smart thermostat, contact Halvard Home customer support. Provide your name, installation address, contact number and a short description of the problem.

Before contacting support, check whether the thermostat display is on and note whether your heating responds when you change the target temperature. Share these observations so the team can assess the issue.

Tell support which days you are available and mention any access requirements. Ask about call-out charges and warranty cover before agreeing to the visit.

Your appointment is only confirmed once support gives you a date and arrival window. On the day, keep the thermostat accessible and arrange for an adult to be at home.

[P5] Known-faults register
### Faults under investigation

Use this entry when handling enquiries, returns or service cases involving the Lumen smart thermostat. The fault remains under investigation. Do not present a suspected cause as confirmed, or assume that a reported problem is covered by this investigation without checking the case evidence.

The current fault rate on returned Lumen smart thermostat units is 15%. This statement concerns returned units, not the installed population. Do not describe it as the likelihood that a customer’s thermostat will fail or use it to predict an individual outcome.

Ask the customer to describe what happened, what they expected and whether the thermostat displayed a message. Record their wording accurately. Note the installation context and whether they can control their heating. Keep observations separate from assumptions, and avoid leading questions that suggest a diagnosis.

Follow the approved troubleshooting guidance available through the support process. Do not suggest unapproved resets, wiring changes or software changes. If the guidance does not cover the reported behaviour, refer the case for technical review rather than improvising a workaround.

Treat signs of electrical danger or loss of safe heating as a safety concern, not simply a fault investigation. Follow the relevant safety and escalation procedures. Do not ask a customer to open the thermostat, touch wiring or continue using equipment they believe is unsafe.

Ex

System's answer:
If a complaint about the Lumen smart thermostat remains unresolved for **54 hours, escalate it to a team leader**. [P1]

Review the complaint record and prepare a handover covering the unresolved issue, its impact, actions already taken and the customer’s requested outcome. Don’t delay referral to repeat troubleshooting or obtain information that isn’t essential to the handover. [P1–P2]

Tell the customer who will manage the complaint and how they’ll receive an update, record the handover, and confirm that the receiving colleague has accepted ownership. Don’t promise a refund, replacement or compensation. [P1–P2]

If there are safety concerns—such as overheating, burning smells or unsafe heating behaviour—stop routine troubleshooting and use the **urgent safety escalation process**, rather than waiting 54 hours. [P1]

---

## 6. PARA-018

Question: How can I get my heating controller to show up in its companion software?

Can the question be answered from the documents: yes

Reference answer: If the Halvard Home app cannot find your Lumen smart thermostat, start by checking that the thermostat is powered on and its screen responds.

Passages given to the system:
[P1] Orrin heat pump not appearing in the app
Orrin heat pump not appearing in the app

If the app cannot find your Orrin heat pump, start by checking that the heat pump is switched on and your phone is connected to your home Wi-Fi.

Try these steps in order:

1. Move your phone closer to the heat pump.
2. Check your phone’s settings and allow the app any requested Bluetooth or local network access.
3. Turn your phone’s Wi-Fi off for 10 seconds, then turn it back on.
4. Close the app completely, reopen it and try adding the device again.
5. Check your app store for an update.

If the device still does not appear, contact Halvard Home support. Tell us your phone model and what happens when you try to connect.

[P2] Corra induction hob not appearing in the app
Corra induction hob not appearing in the app

If the app cannot find your Corra induction hob, first check that the hob has power and your phone is close to it.

Try these steps:

1. Turn on Bluetooth and Wi-Fi on your phone.
2. In your phone’s settings, allow the app to access Bluetooth and nearby devices. Allow local network access if prompted.
3. Close the app completely, wait 30 seconds, then open it again.
4. Follow the app’s instructions to put the hob into pairing mode, then search again.

If the hob was previously connected, check whether it already appears under another account or home in the app.

Still having trouble? Contact Halvard Home support with your phone model and a description of where setup stops.

[P3] Lumen thermostat not appearing in the app
Lumen thermostat not appearing in the app

If the Halvard Home app cannot find your Lumen smart thermostat, start by checking that the thermostat is powered on and its screen responds.

Turn on Bluetooth in your phone’s settings, then connect your phone to your home Wi-Fi. Keep your phone close to the thermostat while searching.

Open your phone’s app settings and check that the Halvard Home app has any requested Bluetooth, nearby device or local network permissions. Close the app fully, reopen it and try adding the thermostat again.

If it still does not appear, restart your phone and check for app updates. Avoid factory resetting the thermostat at this stage.

Contact Halvard Home support if the problem continues, explaining which checks you have completed.

[P4] Brio kettle not appearing in the app
Brio kettle not appearing in the app

On the Brio kettle, E-7484 means the wireless pairing window has expired, so the app can no longer discover the kettle. This is a connection issue, not a heating fault.

To reconnect:

1. Place the kettle on its powered base, but do not start boiling.
2. Press and hold the wireless button for five seconds, until its light flashes blue.
3. Open the Halvard Home app and select **Add device** within two minutes.
4. Keep your phone within one metre of the kettle until pairing finishes.

If the kettle still does not appear, enable Bluetooth on your phone and allow the app to find nearby devices. Close and reopen the app, then repeat the pairing steps.

[P5] Connecting your Orrin heat pump to wi-fi
Connecting your Orrin heat pump to wi-fi

On the Orrin heat pump, E-6922 means the heat pump has tried to join a 5 GHz wi-fi network, which it does not support. Use a 2.4 GHz network instead.

To connect:

1. Check your router settings and make sure the 2.4 GHz network is switched on.
2. If both bands share a network name, follow your router’s instructions to give them separate names.
3. On the heat pump’s control panel, open Settings, then Wi-fi, and select the 2.4 GHz network.
4. Enter your wi-fi password carefully, including any capital letters.

Wait one minute for the connection to complete. If it still fails, restart your router and try again. Contact Halvard Home support if the same message returns.

System's answer:
If you mean the **Lumen smart thermostat** and the **Halvard Home app**, try these steps:

1. Make sure the thermostat is powered on and its screen responds.
2. Turn on your phone’s Bluetooth and connect it to your home Wi-Fi.
3. Keep your phone close to the thermostat while searching.
4. In your phone’s app settings, allow Halvard Home any requested **Bluetooth, nearby-device, or local-network permissions**.
5. Close the app completely, reopen it, and try adding the thermostat again.
6. If it still doesn’t appear, restart your phone and check for app updates.

**Don’t factory-reset the thermostat at this stage.** If the problem continues, contact Halvard Home support and explain which checks you’ve completed.

If you mean the Orrin heat pump rather than the Lumen thermostat, let me know—the troubleshooting steps differ slightly.

---

## 7. IDENT-030

Question: What does error E-9454 mean?

Can the question be answered from the documents: yes

Reference answer: For the Halvard Home Mira robot vacuum, E-9454 means the battery protection system has blocked startup because the battery charge is too low.

Passages given to the system:
[P1] Saving energy with your Tessa dishwasher
Saving energy with your Tessa dishwasher

The Tessa dishwasher’s Eco programme uses lower wash temperatures and a longer cycle to reduce electricity use. For everyday loads, select Eco and wait until the dishwasher is full before starting, without blocking the spray arms.

Error code E-9544 means the temperature sensor has detected overheating during Eco mode, so the dishwasher has paused the programme to prevent unnecessary energy use.

Switch the dishwasher off at the mains for five minutes, then restore power and select Eco again. If the warning returns, stop using the appliance and contact Halvard Home support to arrange a sensor check. Do not remove any panels or attempt repairs yourself.

For further savings, switch off heated drying if your model offers this option.

[P2] Updating your Mira robot vacuum
Updating your Mira robot vacuum

On the Halvard Home Mira robot vacuum, error E-7804 means the firmware download was interrupted before installation could begin. Your vacuum is still using its previous firmware.

To retry the update:

1. Place Mira on its charging dock and leave the dock switched on.
2. Check that your home Wi-Fi is working and that Mira shows as connected in the Halvard Home app.
3. Open Mira’s settings in the app, select ‘Firmware update’, then tap ‘Retry’.
4. Keep the vacuum docked and your router switched on until the app confirms the update is complete.

If the update fails again, close and reopen the app, then retry once. Contact Halvard Home support if the problem continues.

[P3] Tessa dishwasher: delay start fault
Tessa dishwasher: delay start fault

On a Halvard Home Tessa dishwasher, E-9509 means the delay start timer has lost its saved countdown. The dishwasher pauses rather than starting at an unexpected time.

To reset the timer:

1. Press and hold the Start button for three seconds to cancel the delayed programme.
2. Switch the dishwasher off at the wall socket for one minute, then switch it back on.
3. Select your wash programme again.
4. Set the delay you want, press Start and close the door firmly.

The countdown begins only when the door is fully closed. Opening the door pauses it until you close it again.

If the fault returns, cancel delay start and contact Halvard Home support before trying another delayed wash.

[P4] Tessa dishwasher: flashing warning light
Tessa dishwasher: flashing warning light

On your Halvard Home Tessa dishwasher, a flashing warning light with E-4021 means water has not drained within three minutes. A blocked drain filter is the most common cause.

Stop the programme and switch the dishwasher off at the mains. If the water is hot, let it cool before opening the door fully. Place towels around the base to catch any spills.

Remove the bottom basket, then turn the filter anticlockwise and lift it out. Rinse it under warm running water, removing food scraps with a soft brush. Refit the filter securely before restoring power.

Run a rinse programme. If the warning returns or water remains inside, stop using the dishwasher and contact Halvard Home support.

[P5] Mira robot vacuum: blocked brush alert
Mira robot vacuum: blocked brush alert

The fault code E-0421 on your Mira robot vacuum means the main brush cannot turn freely. Hair, thread or debris wrapped around the brush is the usual cause.

To clear the fault:

1. Switch off the vacuum and remove it from the charging dock.
2. Turn it upside down on a soft, dry surface.
3. Unclip the main brush cover and lift out the brush.
4. Carefully remove tangled hair and debris, including anything caught around the brush ends.
5. Refit the brush and clip the cover securely into place.

Return the vacuum to the floor, switch it on and start cleaning. If the fault returns, stop using it and contact Halvard Home support.

System's answer:
Error **E-9454** isn’t listed in the provided passages, so I can’t confirm its meaning.

If you meant **E-9544**, it means the Tessa dishwasher’s temperature sensor detected overheating during Eco mode, causing the programme to pause.

---

## 8. DELETED-013

Question: What should I do if I have cleaning gel pouches from batch 1632 for my Ashby tumble dryer?

Can the question be answered from the documents: no

Reference answer: That notice was withdrawn on 2026-07-13.

Passages given to the system:
[P1] Cleaning gel pouch safety notice
Cleaning gel pouch safety notice

Stop using cleaning gel pouches from batch 1632 with the Ashby tumble dryer, and return them for a refund.

This notice applies to Halvard Home cleaning gel pouches labelled with the affected batch on the packaging. Please check the label before using a pouch. Keep affected pouches in their original packaging, away from children and pets. Do not open, puncture or empty them.

Contact Halvard Home customer support for help arranging your return and refund. If you have already used an affected pouch, leave the dryer switched off and ask our support team for advice before using it again.

[P2] Cleaning gel pouch safety notice
Cleaning gel pouch safety notice

Stop using cleaning gel pouches from batch 9421 with the Fenwick cooker hood, and return them for a refund.

Halvard Home asks customers to check the batch details printed on the pouch packaging before cleaning their cooker hood. If your pouches belong to the affected batch, leave them sealed and keep them away from children and pets. Please return them to the shop where you bought them, or contact Halvard Home customer support for help arranging a return and refund. Do not pour the gel down the sink or put it in household waste.

We apologise for the inconvenience and appreciate your help with this precaution.

[P3] Ashby side brush safety notice
Ashby side brush safety notice

Stop using side brushes from batch 3103 with the Ashby tumble dryer, and return them for a refund.

Halvard Home is asking customers to check the packaging of their side brushes for the affected batch details. If your brushes match, stop using them and keep them separate from your dryer accessories. Please contact Halvard Home customer support for return instructions and help arranging your refund. If you are unsure whether your brushes are affected, contact us before using them with your Ashby tumble dryer.

We are sorry for the inconvenience and appreciate your help in keeping our products safe to use.

[P4] Safety and recalls
cover the appliance or use it as a place to store objects that could block airflow or fall behind it.

Allow the programme to finish, including its cooling stage. If you must stop it before it finishes, remove the laundry and spread it out so heat can escape, provided this is safe. Do not leave hot laundry piled together or enclosed in a basket.

Switch off the appliance and disconnect it from the electricity supply before cleaning. Let the Ashby tumble dryer cool for 111 minutes before cleaning it. Follow the booklet’s cleaning instructions, and do not spray water into the casing or onto electrical parts.

Remove fluff from the lint filter after use, following the instructions for handling and refitting it. Do not push fluff into the appliance. If the filter is torn, distorted or cannot be secured correctly, stop using the appliance and arrange a suitable replacement.

Clean the air vents of the Ashby tumble dryer every 64 days. Keep ventilation openings unobstructed during use. Follow the booklet’s guidance for accessible surfaces, and do not remove panels or insert tools into openings to reach internal parts.

Have the Ashby tumble dryer safety-checked every 27 months. Arrange this through Halvard Home or a suitably qualified appliance technician. A scheduled check does not replace attention to

[P5] Safety and recalls
cover the appliance or use it as a place to store objects that could block airflow or fall behind it.

Allow the programme to finish, including its cooling stage. If you must stop it before it finishes, remove the laundry and spread it out so heat can escape, provided this is safe. Do not leave hot laundry piled together or enclosed in a basket.

Switch off the appliance and disconnect it from the electricity supply before cleaning. Let the Ashby tumble dryer cool for 111 minutes before cleaning it. Follow the booklet’s cleaning instructions, and do not spray water into the casing or onto electrical parts.

Remove fluff from the lint filter after use, following the instructions for handling and refitting it. Do not push fluff into the appliance. If the filter is torn, distorted or cannot be secured correctly, stop using the appliance and arrange a suitable replacement.

Clean the air vents of the Ashby tumble dryer every 64 days. Keep ventilation openings unobstructed during use. Follow the booklet’s guidance for accessible surfaces, and do not remove panels or insert tools into openings to reach internal parts.

Have the Ashby tumble dryer safety-checked every 27 months. Arrange this through Halvard Home or a suitably qualified appliance technician. A scheduled check does not replace attention to

System's answer:
Stop using cleaning gel pouches from **batch 1632** with your Ashby tumble dryer and return them for a refund.

- Keep them in their original packaging, away from children and pets.
- Do not open, puncture or empty them.
- Contact **Halvard Home customer support** to arrange the return and refund.
- If you have already used one, leave the dryer switched off and ask customer support for advice before using it again. [P1]

---

## 9. RESTRICT-PUBLIC-030

Question: How much can parts for the Fenwick cooker hood cost before an engineer needs to get approval to fit them?

Can the question be answered from the documents: no

Reference answer: Only staff documents give this.

Passages given to the system:
[P1] Engineer service manual (extract)
where required, test results and any remaining concerns. Leave the work area safe and give the customer clear operating advice relevant to the repair.

## Fenwick cooker hood

### Internal repair limits

Engineers may fit parts to the Fenwick cooker hood worth up to £282.00 without approval. Apply this limit to the combined value of parts needed for the repair, not to each part separately. Check current internal parts pricing before committing stock or telling the customer that work can proceed.

If the proposed repair exceeds this allowance, stop and seek approval through the service authorisation process. Record the symptoms, diagnosis, proposed parts and reason for replacement. Do not split the repair across visits or job records to avoid approval. Keep the customer informed without promising an outcome that has not been authorised.

Before starting work, confirm that the appliance is the Fenwick cooker hood and check the service history. Ask the customer about the reported fault and any recent changes to its operation. Inspect accessible areas for damage, contamination, loose fixings and signs of overheating.

Isolate the electrical supply and verify that the appliance is safe before opening covers or handling internal components. Follow the approved isolation procedure and use suitable protective equipment. Do not bypass protective devices, alter wiring arrangements or improvise repairs to damaged electrical

[P2] Booking a Fenwick cooker hood engineer visit
Booking a Fenwick cooker hood engineer visit

To arrange an engineer visit for your Fenwick cooker hood, contact Halvard Home customer support and explain what is wrong. Before getting in touch, write down when the problem started and whether it happens every time you use the hood.

Have your address, contact number and any purchase or warranty details ready. Tell the adviser if the hood is difficult to reach or if there are any access restrictions at your property.

Ask the adviser to confirm the appointment date, any call-out charge and what the visit includes before agreeing to the booking.

On the day, clear the hob and surrounding worktop so the engineer can reach the hood safely. Leave any inspection or dismantling to the engineer.

[P3] Servicing and engineer visits
restricted access, fragile surfaces or alterations to the installation. Do not dismantle the hood or remove fixed electrical fittings yourself.

The engineer will assess the Fenwick cooker hood in line with the applicable servicing instructions. The work may include examining accessible components, checking operation and looking for signs of wear or damage. The engineer will explain if the installation or condition prevents servicing from being completed safely.

If the engineer identifies work outside the agreed service, they will explain what is needed and how it can be arranged. Charges will be explained before you are asked to agree to chargeable work. A service booking does not authorise repairs beyond the agreed scope.

After the visit, you will receive a record explaining the service outcome and recommendations. Please keep this with your appliance documents. If work could not be completed, the record will explain the reason and the action needed before servicing can be completed.

An incomplete visit does not automatically change the service due date. Halvard Home will confirm how the service record has been updated and whether a further appointment is needed. Please contact us if the record does not match your understanding of the engineer’s advice.

Continue to follow the cleaning and filter care instructions supplied with your Fenwick cooker hood. These tasks are separate from the servicing schedule. Do not use the service reminder as a

[P4] Servicing and engineer visits
restricted access, fragile surfaces or alterations to the installation. Do not dismantle the hood or remove fixed electrical fittings yourself.

The engineer will assess the Fenwick cooker hood in line with the applicable servicing instructions. The work may include examining accessible components, checking operation and looking for signs of wear or damage. The engineer will explain if the installation or condition prevents servicing from being completed safely.

If the engineer identifies work outside the agreed service, they will explain what is needed and how it can be arranged. Charges will be explained before you are asked to agree to chargeable work. A service booking does not authorise repairs beyond the agreed scope.

After the visit, you will receive a record explaining the service outcome and recommendations. Please keep this with your appliance documents. If work could not be completed, the record will explain the reason and the action needed before servicing can be completed.

An incomplete visit does not automatically change the service due date. Halvard Home will confirm how the service record has been updated and whether a further appointment is needed. Please contact us if the record does not match your understanding of the engineer’s advice.

Continue to follow the cleaning and filter care instructions supplied with your Fenwick cooker hood. These tasks are separate from the servicing schedule. Do not use the service reminder as a

[P5] Safety and recalls
. If those requirements conflict with the proposed installation, do not proceed until a safe arrangement has been confirmed.

The supporting wall or structure must be suitable for the appliance and its fixings. Your installer should check for concealed wiring, pipes and other services before drilling. Do not rely on damaged surfaces or unsuitable plugs and screws. Seek specialist advice if the supporting structure is uncertain.

Ventilation and ducting must be assessed as part of the installation. Air must not be discharged into a flue used to remove fumes from an appliance burning gas or another fuel. Where fuel-burning appliances share the space, obtain professional advice about ventilation and the risk of fumes entering your home.

Use fittings and accessories approved for the Fenwick cooker hood and follow the installation instructions supplied with it. Do not cut, bend or remove structural parts to accommodate cupboards or ducting. Keep ventilation openings clear and ensure surrounding furniture does not obstruct access needed for cleaning or servicing.

Before moving the appliance, switch it off and disconnect it from the electricity supply. If it is connected through fixed wiring, arrange for a competent electrician to disconnect it. Never pull on the cable to remove the plug, and do not attempt to move the appliance while it remains connected.

Allow hot surfaces to cool before handling the

System's answer:
An engineer can fit parts costing up to **£282.00 in total** without approval. Approval is required if the combined cost of parts exceeds that amount.

---

## 10. ABSENT-042

Question: How long are repairs to the Fenwick cooker hood guaranteed for?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Fenwick cooker hood warranty
Fenwick cooker hood warranty

Your Halvard Home Fenwick cooker hood comes with a two-year warranty from the date of purchase. Keep your receipt or order confirmation, as you will need it to show when you bought the appliance.

The warranty covers faults caused by defective materials or workmanship during normal domestic use. It does not cover accidental damage, misuse or routine maintenance, such as cleaning grease filters.

If your cooker hood develops a fault during the warranty period, contact Halvard Home customer support. Have your proof of purchase ready and describe what is happening. Do not attempt internal repairs yourself; support can advise you on the next steps.

Your warranty does not affect your statutory rights.

[P2] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P3] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P4] Warranty
under law.

Replacement parts fitted to the Fenwick cooker hood are covered for a further 348 days. This parts cover begins on the date the replacement part is fitted under an authorised warranty repair. Keep the repair confirmation so that the fitting date can be checked.

The replacement parts cover applies to the part supplied and fitted, rather than restarting cover for the entire Fenwick cooker hood. If the original warranty is still active, it continues according to its existing terms alongside the protection for the replacement part.

Ask us if you are unsure which cover applies to a fault following a repair. We will check the delivery and repair records and explain the position. You do not need to decide which warranty provision applies before contacting us.

If the Fenwick cooker hood is sold on, the new owner must transfer the warranty within 39 days. This requirement runs from the date of sale. The new owner should contact Halvard Home to request the transfer and provide evidence of the change of ownership.

The seller should pass on the delivery confirmation, purchase receipt and any repair records. These documents help the new owner establish the original warranty dates and identify any replacement parts that remain covered. Personal information unrelated to the warranty can be removed.

Transferring the warranty does not restart or extend the original cover. The new

[P5] Warranty
under law.

Replacement parts fitted to the Fenwick cooker hood are covered for a further 348 days. This parts cover begins on the date the replacement part is fitted under an authorised warranty repair. Keep the repair confirmation so that the fitting date can be checked.

The replacement parts cover applies to the part supplied and fitted, rather than restarting cover for the entire Fenwick cooker hood. If the original warranty is still active, it continues according to its existing terms alongside the protection for the replacement part.

Ask us if you are unsure which cover applies to a fault following a repair. We will check the delivery and repair records and explain the position. You do not need to decide which warranty provision applies before contacting us.

If the Fenwick cooker hood is sold on, the new owner must transfer the warranty within 39 days. This requirement runs from the date of sale. The new owner should contact Halvard Home to request the transfer and provide evidence of the change of ownership.

The seller should pass on the delivery confirmation, purchase receipt and any repair records. These documents help the new owner establish the original warranty dates and identify any replacement parts that remain covered. Personal information unrelated to the warranty can be removed.

Transferring the warranty does not restart or extend the original cover. The new

System's answer:
Replacement parts fitted during an authorised repair are guaranteed for **348 days from the fitting date**. Refurbished parts are covered for **17 weeks**, including work needed to correct defects in those parts. [P4][P2]
