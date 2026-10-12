# Judge check: marking sheet

50 items, each shown exactly as the judge saw it. The judge's verdicts are not shown. For each item, fill in `declined`, `correct` and `faithful` in `judge_check.csv` with y or n, and add a note where the call was close.

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

## 1. DELETED-013

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

## 2. RESTRICT-PUBLIC-030

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

## 3. ABSENT-042

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

---

## 4. POL-SINGLE-009

Question: How long is the time slot for Halvard Home to arrive for a visit?

Can the question be answered from the documents: yes

Reference answer: Each visit is given an arrival window of 5 hours.

Passages given to the system:
[P1] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P2] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P3] Safety and recalls
sure the visiting specialist can reach your home safely.

We will discuss the appointment with you and explain how we will confirm it. Tell us which contact method is accessible for you. If communication services are unreliable where you live, we will agree a practical way to share arrangements and important safety information.

Please let us know about disability, mobility or communication needs that may affect the visit. You do not need to share a medical history. We will discuss reasonable adjustments with you and explain how these will be reflected in the arrangements.

An adult authorised to give access must be present for the visit. Please keep the route to the appliance clear where this can be done safely. Do not move a damaged appliance, disconnect fixed connections or undertake lifting to prepare for our arrival.

The visiting specialist will identify themselves and explain the purpose of the visit. If you are unsure whether a visitor represents Halvard Home, keep your door closed and contact us through an official channel. You should not feel pressured to allow access.

Recall collections in Island Areas are made within 44 working days.

If your recall notice requires collection, we will explain how it will be arranged and what preparation is safe. Leave the appliance in place unless we advise otherwise. Tell us if its location or condition makes removal difficult so that we can

[P4] Safety and recalls
sure the visiting specialist can reach your home safely.

We will discuss the appointment with you and explain how we will confirm it. Tell us which contact method is accessible for you. If communication services are unreliable where you live, we will agree a practical way to share arrangements and important safety information.

Please let us know about disability, mobility or communication needs that may affect the visit. You do not need to share a medical history. We will discuss reasonable adjustments with you and explain how these will be reflected in the arrangements.

An adult authorised to give access must be present for the visit. Please keep the route to the appliance clear where this can be done safely. Do not move a damaged appliance, disconnect fixed connections or undertake lifting to prepare for our arrival.

The visiting specialist will identify themselves and explain the purpose of the visit. If you are unsure whether a visitor represents Halvard Home, keep your door closed and contact us through an official channel. You should not feel pressured to allow access.

Recall collections in Island Areas are made within 44 working days.

If your recall notice requires collection, we will explain how it will be arranged and what preparation is safe. Leave the appliance in place unless we advise otherwise. Tell us if its location or condition makes removal difficult so that we can

[P5] Safety and recalls
Halvard Home website or your recall notice. Describe what has happened and tell us whether the appliance is still connected or in use. We may ask for a photograph of its identification label, but only if you can obtain it safely.

We assess urgency using the information you provide and the safety guidance for the reported issue. Urgent safety visits in London and South East are made within 64 hours. This commitment runs from when you report an issue that requires an urgent safety visit, rather than from when an appointment is booked.

Please tell us about access requirements when arranging the visit. These may include step-free access, entry arrangements for a shared building, communication preferences or a need for someone to support you. You do not need to disclose a diagnosis. We will discuss suitable arrangements with you and record what is needed.

We will confirm the appointment and explain how to recognise the person attending. Our visiting staff carry identification and will explain why they are there before asking to enter. If you are unsure about their identity, keep the door closed and contact us through our published support details.

Please make the route to the appliance accessible where this is safe. Keep children and pets away from the work area and tell the visitor about hazards they may not readily see. Do not move a heavy appliance or disturb

System's answer:
The passages do not specify an arrival time slot for a visit. Check your booking confirmation for the scheduled start time, or contact Halvard Home if the appointment details are unclear. [P1]

---

## 5. TWOPART-002

Question: How much longer is the repair guarantee for the Orrin heat pump than the extra return time Extended Care adds?

Can the question be answered from the documents: yes

Reference answer: Repairs to the Orrin heat pump are guaranteed for 211 days. Extended Care adds 59 days to the standard returns window.

Passages given to the system:
[P1] Warranty
supplied about reconnecting the appliance, cleaning it or restarting a programme. If the original problem remains or returns, contact us and describe what you have noticed.

If you are unhappy with the repair or our handling of your claim, ask customer support to review the case through our complaints process. We will consider the repair records and the information you provide. Your warranty rights are separate from your statutory consumer rights, which are not affected by this policy.

## Orrin heat pump

### Cover period

The Orrin heat pump is covered for 72 months from the date of delivery. Your delivery record establishes when the warranty begins. The date you register the appliance, arrange installation or start using it does not change that starting point.

Keep your order confirmation, delivery note and warranty details somewhere accessible. If your delivery record is missing or appears incorrect, contact Halvard Home so that we can help establish the delivery date. We may ask for supporting information from the retailer or delivery service.

This warranty applies to faults caused by defective materials or manufacture, subject to the conditions and exclusions in this policy. Being within the cover period does not mean that every fault, service visit or replacement is covered. We will explain our assessment before arranging work.

Labour for repairs to the Orrin heat pump is free

[P2] Warranty
supplied about reconnecting the appliance, cleaning it or restarting a programme. If the original problem remains or returns, contact us and describe what you have noticed.

If you are unhappy with the repair or our handling of your claim, ask customer support to review the case through our complaints process. We will consider the repair records and the information you provide. Your warranty rights are separate from your statutory consumer rights, which are not affected by this policy.

## Orrin heat pump

### Cover period

The Orrin heat pump is covered for 72 months from the date of delivery. Your delivery record establishes when the warranty begins. The date you register the appliance, arrange installation or start using it does not change that starting point.

Keep your order confirmation, delivery note and warranty details somewhere accessible. If your delivery record is missing or appears incorrect, contact Halvard Home so that we can help establish the delivery date. We may ask for supporting information from the retailer or delivery service.

This warranty applies to faults caused by defective materials or manufacture, subject to the conditions and exclusions in this policy. Being within the cover period does not mean that every fault, service visit or replacement is covered. We will explain our assessment before arranging work.

Labour for repairs to the Orrin heat pump is free

[P3] Warranty
Accurate details help us discuss a claim with the right person and avoid confusion about ownership. Updating an address or correcting a name does not alter the delivery date or extend the cover.

Routine maintenance, accidental damage and faults caused by misuse are not made eligible simply because they arise during the cover period. Follow the care and installation instructions supplied with the Orrin heat pump. If the cause of a fault is uncertain, contact us rather than attempting a repair yourself.

When the warranty ends, you can still contact Halvard Home for advice about repair options. Work outside the warranty may be chargeable, and we will explain the proposed terms before you agree. This warranty is additional to your statutory rights and does not replace or restrict them.

### Repairs under warranty

If your Orrin heat pump develops a fault covered by its warranty, Halvard Home will arrange a repair without charging you for the necessary assessment, labour or parts. Contact our customer support team to report the problem and explain what you have noticed. Please have your proof of purchase available.

We will ask for your contact details, the installation address and information about the fault. Photographs or a description of any message shown on the controls may help us understand the problem. We will explain how to send this information securely and use it

[P4] Warranty
Accurate details help us discuss a claim with the right person and avoid confusion about ownership. Updating an address or correcting a name does not alter the delivery date or extend the cover.

Routine maintenance, accidental damage and faults caused by misuse are not made eligible simply because they arise during the cover period. Follow the care and installation instructions supplied with the Orrin heat pump. If the cause of a fault is uncertain, contact us rather than attempting a repair yourself.

When the warranty ends, you can still contact Halvard Home for advice about repair options. Work outside the warranty may be chargeable, and we will explain the proposed terms before you agree. This warranty is additional to your statutory rights and does not replace or restrict them.

### Repairs under warranty

If your Orrin heat pump develops a fault covered by its warranty, Halvard Home will arrange a repair without charging you for the necessary assessment, labour or parts. Contact our customer support team to report the problem and explain what you have noticed. Please have your proof of purchase available.

We will ask for your contact details, the installation address and information about the fault. Photographs or a description of any message shown on the controls may help us understand the problem. We will explain how to send this information securely and use it

[P5] Servicing and engineer visits
sure they understand what has been reported and what the engineer may need to inspect. Let us know about communication or accessibility needs when booking.

The engineer will use suitable replacement parts and carry out checks relevant to the repair. They may need access to the controls, electricity supply and connected heating system. We will explain if the reported problem appears to come from equipment or installation work outside the scope of the agreed repair.

If a required part is unavailable, we will explain what this means for the work and agree how to proceed. We will not substitute an unsuitable component to complete a repair. If further work changes the proposed scope or price, we will seek your approval before carrying it out.

Some faults cannot be resolved safely through a routine repair. Extensive damage, unsuitable installation or defects elsewhere in the heating system may need specialist attention. If this applies, the engineer will explain the concern and identify the type of work needed before repair work can proceed.

Repairs to the Orrin heat pump are guaranteed for 211 days. This guarantee covers faults caused by the repair work or by a component supplied as part of that repair. Contact Halvard Home if you believe the repair has failed, and describe the symptoms so we can assess your concern.

The repair guarantee does not cover unrelated faults,

System's answer:
The Orrin heat pump’s repair guarantee is **211 days** [P5], but the passages don’t specify how much extra return time Extended Care adds, so the difference cannot be calculated.

---

## 6. DISTRACT-016

Question: How often does the Corra induction hob need servicing?

Can the question be answered from the documents: yes

Reference answer: The Corra induction hob should be serviced every 16 months.

Passages given to the system:
[P1] Servicing and engineer visits
installation date as the starting point for your servicing schedule. After a service, use the date recorded by the engineer to plan the next appointment. Keep the service record somewhere accessible so that you can refer to it when arranging another visit.

If you do not know when your hob was installed or last serviced, contact Halvard Home for advice. We may ask for installation paperwork or an existing service record. Where the service history is unclear, we can help you arrange an appropriate appointment.

Please arrange servicing through Halvard Home or an engineer authorised by us to service the Corra induction hob. Tell us that you are booking a routine service, rather than a repair, so that we can make suitable arrangements and explain what the visit will cover.

Let us know about any faults when you book. These may include unusual noises, unexpected switching off, cracked glass or controls that do not respond as expected. A routine service is not a substitute for investigating a fault, and a repair may need separate arrangements.

A routine service of the Corra induction hob takes about 120 minutes. The engineer will need clear access to the hob, its electrical isolation switch and any relevant cupboard space beneath it. Please tell us about access restrictions when arranging the appointment.

A routine service of the Corra induction hob costs £

[P2] Servicing and engineer visits
installation date as the starting point for your servicing schedule. After a service, use the date recorded by the engineer to plan the next appointment. Keep the service record somewhere accessible so that you can refer to it when arranging another visit.

If you do not know when your hob was installed or last serviced, contact Halvard Home for advice. We may ask for installation paperwork or an existing service record. Where the service history is unclear, we can help you arrange an appropriate appointment.

Please arrange servicing through Halvard Home or an engineer authorised by us to service the Corra induction hob. Tell us that you are booking a routine service, rather than a repair, so that we can make suitable arrangements and explain what the visit will cover.

Let us know about any faults when you book. These may include unusual noises, unexpected switching off, cracked glass or controls that do not respond as expected. A routine service is not a substitute for investigating a fault, and a repair may need separate arrangements.

A routine service of the Corra induction hob takes about 120 minutes. The engineer will need clear access to the hob, its electrical isolation switch and any relevant cupboard space beneath it. Please tell us about access restrictions when arranging the appointment.

A routine service of the Corra induction hob costs £

[P3] Safety and recalls
treat a residual heat warning as a sign that contact may cause burns. Do not rely on the display if the electrical supply has been interrupted or the appliance appears faulty.

Let the Corra induction hob cool for 114 minutes before cleaning it. Do not clean the surface while it remains warm, even after this cooling period. Switch off the hob and isolate its electrical supply before cleaning. Follow the care instructions for removing spills without exposing yourself to heat or damaging the glass.

Use a soft cloth and a cleaning product recommended in the care instructions. Do not use abrasive pads, corrosive cleaners or steam-cleaning equipment. Avoid letting liquid enter the casing, controls or electrical connections. Dry the surface before use, and remove cleaning residue that could affect the controls or mark the glass.

Clean the air vents of the Corra induction hob every 16 days. Follow the instructions for accessing and cleaning them without removing protective covers. Keep ventilation openings free from grease, dust and obstructions. Do not push tools into the vents. Contact Halvard Home if you cannot clean them safely.

Have the Corra induction hob safety-checked every 6 months. Arrange this through a suitably qualified professional and keep the service record. A scheduled check does not replace action when a fault appears. Stop using the hob

[P4] Safety and recalls
treat a residual heat warning as a sign that contact may cause burns. Do not rely on the display if the electrical supply has been interrupted or the appliance appears faulty.

Let the Corra induction hob cool for 114 minutes before cleaning it. Do not clean the surface while it remains warm, even after this cooling period. Switch off the hob and isolate its electrical supply before cleaning. Follow the care instructions for removing spills without exposing yourself to heat or damaging the glass.

Use a soft cloth and a cleaning product recommended in the care instructions. Do not use abrasive pads, corrosive cleaners or steam-cleaning equipment. Avoid letting liquid enter the casing, controls or electrical connections. Dry the surface before use, and remove cleaning residue that could affect the controls or mark the glass.

Clean the air vents of the Corra induction hob every 16 days. Follow the instructions for accessing and cleaning them without removing protective covers. Keep ventilation openings free from grease, dust and obstructions. Do not push tools into the vents. Contact Halvard Home if you cannot clean them safely.

Have the Corra induction hob safety-checked every 6 months. Arrange this through a suitably qualified professional and keep the service record. A scheduled check does not replace action when a fault appears. Stop using the hob

[P5] Servicing and engineer visits
connections. Our engineer will inspect the appliance to identify the fault and explain the recommended work. A reported symptom does not always mean that a part needs replacing.

Before arranging a visit, check that your cookware is suitable for induction cooking and that the hob is not locked. Follow the checks in your user instructions. Do not remove covers, attempt electrical repairs or continue testing the appliance if you notice damage, smoke or a burning smell.

If the glass surface is cracked, stop using the hob and isolate it from the electricity supply if you can do so safely. Do not use an unaffected cooking area while waiting for advice. Damage to the glass can make the appliance unsafe even when the controls appear to work normally.

Tell us what happens when you try to use the hob, including whether the problem affects heating, touch controls or ventilation. Please describe any message shown on the display without trying to interpret it. Photographs may help us assess visible damage, but they cannot replace an engineer’s inspection.

Diagnosing a fault on the Corra induction hob costs £80.00 if no repair follows. We will explain the applicable charges when you book and confirm the proposed repair price after diagnosis. The engineer will ask for your agreement before starting chargeable repair work. You may decline the repair.

System's answer:
The Corra induction hob should be safety-checked every **6 months** by a suitably qualified professional. [P3]

---

## 7. POL-SINGLE-035

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

## 8. RESTRICT-STAFF-025

Question: How long does the Keel washing machine’s built-in test take?

Can the question be answered from the documents: yes

Reference answer: The internal diagnostic test on the Keel washing machine runs for 22 minutes.

Passages given to the system:
[P1] Servicing and engineer visits
close the appliance’s water supply valve if it is safe and accessible, and contact us for advice.

A routine service of the Keel washing machine takes about 122 minutes. This is an estimate of the engineer’s working time, rather than a guaranteed appointment length. Access difficulties, the condition of the appliance or faults discovered during the visit may affect how the appointment proceeds. The engineer will explain any change to the planned work.

A routine service of the Keel washing machine costs £168.00. This price covers the routine service work described when you book. Repairs, replacement parts and work outside that scope require your agreement. If the engineer recommends additional work, we will explain what is needed and confirm the price before you decide whether to proceed.

When booking, tell us about any faults, warning messages or recent changes in performance. Mention any previous repairs or alterations that may be relevant. This helps us arrange suitable support and distinguish routine servicing from a repair visit. Have your appliance details and any available service records ready when you contact us.

Please also tell us about access restrictions, parking arrangements or anything that could affect the engineer’s ability to work safely. Let us know if the appliance is fitted into cabinetry or located where moving it may be difficult. We will discuss any preparation

[P2] Servicing and engineer visits
close the appliance’s water supply valve if it is safe and accessible, and contact us for advice.

A routine service of the Keel washing machine takes about 122 minutes. This is an estimate of the engineer’s working time, rather than a guaranteed appointment length. Access difficulties, the condition of the appliance or faults discovered during the visit may affect how the appointment proceeds. The engineer will explain any change to the planned work.

A routine service of the Keel washing machine costs £168.00. This price covers the routine service work described when you book. Repairs, replacement parts and work outside that scope require your agreement. If the engineer recommends additional work, we will explain what is needed and confirm the price before you decide whether to proceed.

When booking, tell us about any faults, warning messages or recent changes in performance. Mention any previous repairs or alterations that may be relevant. This helps us arrange suitable support and distinguish routine servicing from a repair visit. Have your appliance details and any available service records ready when you contact us.

Please also tell us about access restrictions, parking arrangements or anything that could affect the engineer’s ability to work safely. Let us know if the appliance is fitted into cabinetry or located where moving it may be difficult. We will discuss any preparation

[P3] Using delay start on your Keel washing machine
Using delay start on your Keel washing machine

Delay start lets you choose when your wash begins. A delay of 3 hours means the machine waits 3 hours before starting; it does not mean the wash will finish in 3 hours.

To set a delay, load the drum, add detergent and close the door firmly. Select your wash programme, then press Delay Start until the display shows the waiting time you want. Press Start to begin the countdown.

To wash straight away, cancel the delay by setting it to zero before pressing Start.

If the machine appears to be doing nothing, check whether a delay is active. During the countdown, the drum can remain still. This is normal and does not mean the machine has stopped working.

[P4] Safety and recalls
for 113 minutes before cleaning it. Use cleaning methods described in the care instructions. Do not spray water onto the controls, plug or electrical parts, and do not use a steam cleaner.

Clean the air vents of the Keel washing machine every 22 days. Keep vent openings free from lint and household dust without pushing debris inside. Do not remove protective covers or insert tools into the appliance. Ask an authorised repairer for help if a blockage cannot be reached safely.

Do not attempt repairs, bypass safety devices or continue using a damaged appliance. Contact Halvard Home through its official support channels for advice about faults or safety concerns. If a safety notice or recall applies to your Keel washing machine, stop using it and follow the notice’s instructions. Do not sell, donate or pass on an appliance affected by an unresolved safety recall.

### Installation and moving

Safe installation helps protect your household and prevents damage to the Keel washing machine. Follow the installation instructions supplied with the appliance alongside this policy. If the instructions are missing or unclear, contact Halvard Home rather than guessing how to proceed.

Arrange installation through a competent installer if you are unsure about plumbing, electrical connections or positioning the appliance. Electrical work must be carried out by a qualified electrician. Do not alter your

[P5] Safety and recalls
for 113 minutes before cleaning it. Use cleaning methods described in the care instructions. Do not spray water onto the controls, plug or electrical parts, and do not use a steam cleaner.

Clean the air vents of the Keel washing machine every 9 days. Keep vent openings free from lint and household dust without pushing debris inside. Do not remove protective covers or insert tools into the appliance. Ask an authorised repairer for help if a blockage cannot be reached safely.

Do not attempt repairs, bypass safety devices or continue using a damaged appliance. Contact Halvard Home through its official support channels for advice about faults or safety concerns. If a safety notice or recall applies to your Keel washing machine, stop using it and follow the notice’s instructions. Do not sell, donate or pass on an appliance affected by an unresolved safety recall.

### Installation and moving

Safe installation helps protect your household and prevents damage to the Keel washing machine. Follow the installation instructions supplied with the appliance alongside this policy. If the instructions are missing or unclear, contact Halvard Home rather than guessing how to proceed.

Arrange installation through a competent installer if you are unsure about plumbing, electrical connections or positioning the appliance. Electrical work must be carried out by a qualified electrician. Do not alter your

System's answer:
The passages do not state how long the Keel washing machine’s built-in test takes. They only give an estimated routine service time of 122 minutes.

---

## 9. TOPIC-002

Question: What does the Halvard kitchen design service include, and how can I book a consultation with Halvard Home?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Servicing and engineer visits
around it. Keep pets away from the working area and move fragile belongings out of reach. Please tell us about stairs, restricted parking or other access difficulties.

Do not disconnect, defrost or move the appliance unless Halvard Home asks you to do so. The engineer may need to assess it while it is operating. We will explain any preparation needed for your visit when confirming the booking.

Keep food stored safely while the service is carried out. If access to a compartment is needed, the engineer will explain what should be removed. Let us know about any concern that could make preparing the appliance difficult, rather than attempting an unsafe move or lift.

If you cannot attend the agreed appointment, contact Halvard Home to rearrange it. Do not assume that replying to an automated reminder will cancel a booking. Your appointment remains in place until we have confirmed the change.

If an engineer cannot safely reach or work on the appliance, the service may need to be rearranged. We will explain the obstacle and discuss what needs to change. The engineer will not ask you to carry out work that puts you at risk.

After the visit, keep the service report with your appliance records. It should describe the work completed, any concerns identified and the recommended next steps. Contact Halvard Home if anything

[P2] Servicing and engineer visits
around it. Keep pets away from the working area and move fragile belongings out of reach. Please tell us about stairs, restricted parking or other access difficulties.

Do not disconnect, defrost or move the appliance unless Halvard Home asks you to do so. The engineer may need to assess it while it is operating. We will explain any preparation needed for your visit when confirming the booking.

Keep food stored safely while the service is carried out. If access to a compartment is needed, the engineer will explain what should be removed. Let us know about any concern that could make preparing the appliance difficult, rather than attempting an unsafe move or lift.

If you cannot attend the agreed appointment, contact Halvard Home to rearrange it. Do not assume that replying to an automated reminder will cancel a booking. Your appointment remains in place until we have confirmed the change.

If an engineer cannot safely reach or work on the appliance, the service may need to be rearranged. We will explain the obstacle and discuss what needs to change. The engineer will not ask you to carry out work that puts you at risk.

After the visit, keep the service report with your appliance records. It should describe the work completed, any concerns identified and the recommended next steps. Contact Halvard Home if anything

[P3] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P4] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P5] Booking a Fenwick cooker hood engineer visit
Booking a Fenwick cooker hood engineer visit

To arrange an engineer visit for your Fenwick cooker hood, contact Halvard Home customer support and explain what is wrong. Before getting in touch, write down when the problem started and whether it happens every time you use the hood.

Have your address, contact number and any purchase or warranty details ready. Tell the adviser if the hood is difficult to reach or if there are any access restrictions at your property.

Ask the adviser to confirm the appointment date, any call-out charge and what the visit includes before agreeing to the booking.

On the day, clear the hob and surrounding worktop so the engineer can reach the hood safely. Leave any inspection or dismantling to the engineer.

System's answer:
The provided passages don’t describe Halvard’s kitchen design service or explain how to book a design consultation. They cover appliance servicing and engineer visits only.

For details about what the design service includes and how to arrange a consultation, contact Halvard Home customer support using the contact details on its website.

---

## 10. RESTRICT-PUBLIC-032

Question: How long does the Mira robot vacuum’s built-in check take?

Can the question be answered from the documents: no

Reference answer: Only staff documents give this.

Passages given to the system:
[P1] Warranty
and explain the repair arrangements.

A warranty repair to the Mira robot vacuum is completed within 13 working days of the fault being confirmed.

The repair may involve adjusting components, replacing faulty parts or updating the software needed for normal operation. We use parts that meet our safety and performance requirements. These may be new or refurbished, depending on the repair required and the parts available.

A refurbished part fitted to the Mira robot vacuum is covered for 33 weeks.

We will record the work carried out and test your Mira robot vacuum before returning it. The testing checks that the reported fault has been addressed and that the appliance operates safely. Your repair record will identify the parts replaced and explain the work in plain language.

If an unexpected problem affects the repair, we will contact you, explain the reason and discuss the arrangements. You should not have to chase us to find out whether your Mira robot vacuum is still being repaired.

If a repair to the Mira robot vacuum takes longer than 30 working days, Halvard Home lends a replacement.

The loan is arranged by our support team, who will explain delivery, care and return arrangements. Halvard Home covers the transport for the loan. Please look after the replacement, use it according to its instructions and tell us if it develops

[P2] Warranty
and explain the repair arrangements.

A warranty repair to the Mira robot vacuum is completed within 13 working days of the fault being confirmed.

The repair may involve adjusting components, replacing faulty parts or updating the software needed for normal operation. We use parts that meet our safety and performance requirements. These may be new or refurbished, depending on the repair required and the parts available.

A refurbished part fitted to the Mira robot vacuum is covered for 33 weeks.

We will record the work carried out and test your Mira robot vacuum before returning it. The testing checks that the reported fault has been addressed and that the appliance operates safely. Your repair record will identify the parts replaced and explain the work in plain language.

If an unexpected problem affects the repair, we will contact you, explain the reason and discuss the arrangements. You should not have to chase us to find out whether your Mira robot vacuum is still being repaired.

If a repair to the Mira robot vacuum takes longer than 30 working days, Halvard Home lends a replacement.

The loan is arranged by our support team, who will explain delivery, care and return arrangements. Halvard Home covers the transport for the loan. Please look after the replacement, use it according to its instructions and tell us if it develops

[P3] Servicing and engineer visits
of your Mira robot vacuum, together with any advice recorded by a Halvard Home engineer. We will explain when a service is due when your schedule is agreed. If your circumstances change, contact us so we can review whether that schedule remains suitable.

A reminder is sent 7 weeks before a service is due. We use the contact details held on your service record, so please tell us if those details change. The reminder invites you to arrange a visit; it does not reserve an appointment or give us permission to enter your home.

You remain responsible for arranging the service, even if a reminder does not reach you. If you are unsure whether your Mira robot vacuum is due for servicing, contact Halvard Home. We can check the available service history and explain the next step without asking you to guess from how the appliance looks or sounds.

A routine service of the Mira robot vacuum takes about 164 minutes. This is an estimate for the service work, not a guaranteed appointment length. Access difficulties, the condition of the appliance or a fault requiring investigation may affect the visit. Your engineer will explain any change to the planned work.

A routine service of the Mira robot vacuum costs £115.00. We will confirm what the routine service includes when you book. Rep

[P4] Servicing and engineer visits
of your Mira robot vacuum, together with any advice recorded by a Halvard Home engineer. We will explain when a service is due when your schedule is agreed. If your circumstances change, contact us so we can review whether that schedule remains suitable.

A reminder is sent 7 weeks before a service is due. We use the contact details held on your service record, so please tell us if those details change. The reminder invites you to arrange a visit; it does not reserve an appointment or give us permission to enter your home.

You remain responsible for arranging the service, even if a reminder does not reach you. If you are unsure whether your Mira robot vacuum is due for servicing, contact Halvard Home. We can check the available service history and explain the next step without asking you to guess from how the appliance looks or sounds.

A routine service of the Mira robot vacuum takes about 164 minutes. This is an estimate for the service work, not a guaranteed appointment length. Access difficulties, the condition of the appliance or a fault requiring investigation may affect the visit. Your engineer will explain any change to the planned work.

A routine service of the Mira robot vacuum costs £115.00. We will confirm what the routine service includes when you book. Rep

[P5] Booking an engineer for your Mira robot vacuum
Booking an engineer for your Mira robot vacuum

Contact Halvard Home customer support to request an engineer visit for your Mira robot vacuum. Explain what is happening, when the problem started and any checks you have already tried.

Have your address, contact details and proof of purchase ready. Let the team know your preferred appointment dates and mention any access requirements, such as stairs or parking restrictions.

Before agreeing to a booking, ask whether a call-out charge applies and what the visit will cover. Request confirmation of the appointment date and arrival window.

Before the engineer examines your Mira, switch it off and unplug its charging dock. Keep both accessible, and clear enough floor space for the engineer to check the vacuum safely.

System's answer:
The passages do not state how long the Mira robot vacuum’s built-in check takes. They only say a routine service takes about 164 minutes.

---

## 11. TWOPART-016

Question: If my warranty claim for a Vale fridge freezer is accepted in London and South East, how soon can an engineer visit, and how long would a routine service take?

Can the question be answered from the documents: yes

Reference answer: A routine service of the Vale fridge freezer takes about 154 minutes. In London and South East, a warranty engineer visit is offered within 60 hours of a claim being accepted.

Passages given to the system:
[P1] Warranty
warranty terms that apply to your purchase. Acceptance means we have confirmed that your claim qualifies for the warranty repair service, based on the information available. If an inspection reveals a different cause, we will explain what this means for your cover before proceeding with work outside it.

In London and South East, a warranty engineer visit is offered within 60 hours of a claim being accepted. We will contact you to discuss access and offer an appointment. Please tell us about any arrangements that could affect the visit, including building entry requirements, parking restrictions or assistance you need when communicating with us.

The appointment offer is separate from confirmation that the repair can be completed at that visit. The engineer may need to inspect the fault before deciding what work is required. We will explain whether the proposed visit is for assessment, repair or work that depends on suitable parts being available.

Parts for warranty repairs in London and South East arrive within 60 working days. Our support team will explain which parts are needed and how their delivery affects the repair arrangements. A parts delivery does not itself confirm an engineer appointment. We will contact you to arrange fitting where this is required.

Please make sure the engineer can reach the appliance safely and has suitable space to work. Clear personal belongings from the surrounding area where you can safely do

[P2] Warranty
warranty terms that apply to your purchase. Acceptance means we have confirmed that your claim qualifies for the warranty repair service, based on the information available. If an inspection reveals a different cause, we will explain what this means for your cover before proceeding with work outside it.

In London and South East, a warranty engineer visit is offered within 60 hours of a claim being accepted. We will contact you to discuss access and offer an appointment. Please tell us about any arrangements that could affect the visit, including building entry requirements, parking restrictions or assistance you need when communicating with us.

The appointment offer is separate from confirmation that the repair can be completed at that visit. The engineer may need to inspect the fault before deciding what work is required. We will explain whether the proposed visit is for assessment, repair or work that depends on suitable parts being available.

Parts for warranty repairs in London and South East arrive within 60 working days. Our support team will explain which parts are needed and how their delivery affects the repair arrangements. A parts delivery does not itself confirm an engineer appointment. We will contact you to arrange fitting where this is required.

Please make sure the engineer can reach the appliance safely and has suitable space to work. Clear personal belongings from the surrounding area where you can safely do

[P3] Servicing and engineer visits
, leaks, frost or door seals. Tell us whether the appliance is displaying a warning or behaving differently from normal. This helps us understand whether a routine service is appropriate or a repair assessment is needed.

A routine service of the Vale fridge freezer takes about 154 minutes. This is a guide rather than a promise about the engineer’s departure. Access difficulties, the condition of the appliance or a fault found during the visit may affect how the work proceeds.

A routine service of the Vale fridge freezer costs £177.00. The routine service charge does not cover repairs or replacement parts outside the agreed service work. If the engineer identifies work that would carry an additional charge, we will explain it and ask for your agreement before proceeding.

The routine service includes checking the appliance’s general condition, accessible seals, controls and cooling performance. The engineer will also look for signs of damage or wear and discuss any relevant care advice. Servicing cannot guarantee that a fault will not develop afterwards.

Please arrange for a responsible adult to be present who can let the engineer in, discuss the appliance and approve the agreed work. Tell us when booking if you need communication support or have an access requirement so we can discuss suitable arrangements.

Make sure the route to the appliance is clear and that the engineer can work safely

[P4] Servicing and engineer visits
, leaks, frost or door seals. Tell us whether the appliance is displaying a warning or behaving differently from normal. This helps us understand whether a routine service is appropriate or a repair assessment is needed.

A routine service of the Vale fridge freezer takes about 154 minutes. This is a guide rather than a promise about the engineer’s departure. Access difficulties, the condition of the appliance or a fault found during the visit may affect how the work proceeds.

A routine service of the Vale fridge freezer costs £177.00. The routine service charge does not cover repairs or replacement parts outside the agreed service work. If the engineer identifies work that would carry an additional charge, we will explain it and ask for your agreement before proceeding.

The routine service includes checking the appliance’s general condition, accessible seals, controls and cooling performance. The engineer will also look for signs of damage or wear and discuss any relevant care advice. Servicing cannot guarantee that a fault will not develop afterwards.

Please arrange for a responsible adult to be present who can let the engineer in, discuss the appliance and approve the agreed work. Tell us when booking if you need communication support or have an access requirement so we can discuss suitable arrangements.

Make sure the route to the appliance is clear and that the engineer can work safely

[P5] Warranty
if you are uncomfortable carrying out a suggested check.

If you notice smoke, a burning smell, damaged wiring or signs of an electrical fault, stop using the appliance. Disconnect it from the electricity supply if it is safe to do so. Contact us for advice rather than trying to investigate the fault yourself.

A warranty repair to the Vale fridge freezer is completed within 7 working days of the fault being confirmed.

We confirm the fault when our assessment establishes what is wrong and that the repair is covered by the warranty. We will tell you when this has happened and explain the proposed repair. If an engineer needs to inspect the appliance to confirm the fault, we will arrange an appointment with you.

Please tell us about access restrictions, parking arrangements or anything that could make the visit difficult or unsafe. Let us know about accessibility needs so that we can discuss suitable arrangements. The engineer will need clear, safe access to the appliance and its electricity supply.

You do not need to disconnect or move the appliance unless we have explained how to do so safely and you are comfortable with the request. Keep children and pets away from the work area. The engineer may ask you to remove food or stored items where these would obstruct the repair.

Repairs covered by the warranty include the work and parts needed to correct

System's answer:
In London and South East, an engineer visit is **offered within 60 hours of your warranty claim being accepted**. This does not guarantee the repair will be completed at that visit. [P1]

A routine service for a Vale fridge freezer takes **about 154 minutes** (2 hours 34 minutes), though access difficulties, appliance condition or faults found may affect the duration. [P3]

---

## 12. BRIDGE-019

Question: What arrival window do collection drivers give for my home in postcode area DD?

Can the question be answered from the documents: yes

Reference answer: The Scotland North service team covers postcode areas AB, IV, KW, PH and DD. Collection drivers in Scotland North give an arrival window of 156 minutes.

Passages given to the system:
[P1] Returns and refunds
the building or use a loading area, please arrange this with the person responsible for the property.

Collection drivers in North of England give an arrival window of 121 minutes. We will explain how that window will be shared with you. Please make sure someone authorised to hand over the return is available at the address and can answer questions about access.

Tell customer support if you need help preparing for collection because of a disability or access requirement. We will discuss suitable arrangements with you and explain what the collection team can provide. Please do not assume that a request has been passed to the driver unless we have confirmed it.

Before collection, follow the preparation instructions we provide. The item should be safe to handle, with personal belongings removed and loose parts secured where appropriate. Do not attempt work that requires specialist knowledge. If you are unsure how to prepare the return safely, contact us rather than risk injury or damage.

If the item needs disconnecting, we will explain whose responsibility this is when arranging the return. Collection does not automatically include disconnection or work on your property. Tell us if there is a leak, damage or another condition that could make handling unsafe, so we can agree a suitable approach.

Keep the original packaging if you have it, but contact us if it is unavailable or damaged.

[P2] Returns and refunds
the building or use a loading area, please arrange this with the person responsible for the property.

Collection drivers in North of England give an arrival window of 121 minutes. We will explain how that window will be shared with you. Please make sure someone authorised to hand over the return is available at the address and can answer questions about access.

Tell customer support if you need help preparing for collection because of a disability or access requirement. We will discuss suitable arrangements with you and explain what the collection team can provide. Please do not assume that a request has been passed to the driver unless we have confirmed it.

Before collection, follow the preparation instructions we provide. The item should be safe to handle, with personal belongings removed and loose parts secured where appropriate. Do not attempt work that requires specialist knowledge. If you are unsure how to prepare the return safely, contact us rather than risk injury or damage.

If the item needs disconnecting, we will explain whose responsibility this is when arranging the return. Collection does not automatically include disconnection or work on your property. Tell us if there is a leak, damage or another condition that could make handling unsafe, so we can agree a suitable approach.

Keep the original packaging if you have it, but contact us if it is unavailable or damaged.

[P3] Returns and refunds
are made within 47 working days of a return being booked. We will confirm when your booking has been accepted. Sending a return request does not itself confirm that a collection has been booked.

Collection drivers in Wales and West give an arrival window of 108 minutes. Please make sure we have your current contact details so that collection information can reach you. Tell us if you need us to use a particular contact method.

When arranging your collection, we will ask for the collection address, your order details and a description of the item being returned. Please check the booking confirmation carefully and contact us if anything is incorrect or missing.

Tell us about access arrangements that could affect the collection. This includes steps, restricted parking, shared entrances, locked gates and access through communal areas. If permission is needed to enter the property or use a loading area, please arrange this with the person responsible.

Please also tell us about accessibility needs or circumstances that may make the usual collection arrangements difficult. We will discuss suitable arrangements with you and confirm what the collection team can provide. Do not assume that a request has been agreed unless we have confirmed it.

The item must be safe to handle and ready for the agreed collection. Remove your personal belongings and follow the relevant safety instructions when preparing it. If you are unsure

[P4] Returns and refunds
are made within 47 working days of a return being booked. We will confirm when your booking has been accepted. Sending a return request does not itself confirm that a collection has been booked.

Collection drivers in Wales and West give an arrival window of 108 minutes. Please make sure we have your current contact details so that collection information can reach you. Tell us if you need us to use a particular contact method.

When arranging your collection, we will ask for the collection address, your order details and a description of the item being returned. Please check the booking confirmation carefully and contact us if anything is incorrect or missing.

Tell us about access arrangements that could affect the collection. This includes steps, restricted parking, shared entrances, locked gates and access through communal areas. If permission is needed to enter the property or use a loading area, please arrange this with the person responsible.

Please also tell us about accessibility needs or circumstances that may make the usual collection arrangements difficult. We will discuss suitable arrangements with you and confirm what the collection team can provide. Do not assume that a request has been agreed unless we have confirmed it.

The item must be safe to handle and ready for the agreed collection. Remove your personal belongings and follow the relevant safety instructions when preparing it. If you are unsure

[P5] Returns and refunds
.

Ask for confirmation that the item has been collected and keep it with your return correspondence. Collection confirms handover, not the outcome of any assessment. We will contact you about your refund or other agreed remedy after the return has been processed.

If a collection is missed or you have concerns about the driver’s conduct, contact us with the booking details and a description of what happened. We will investigate and explain the next steps. Nothing in these collection arrangements removes or restricts your statutory rights.

## North of England

### Collections in this region

If you are returning an item from an address in North of England, contact Halvard Home customer support to arrange a collection. We will explain whether collection is available for your return and confirm the information we need. Please do not arrange transport on our behalf unless we have agreed this with you.

Collections in North of England are made within 41 working days of a return being booked. Your booking confirmation will explain how we will contact you about the collection. Please check that the collection address and your contact details are correct, and tell us if anything needs changing.

When you book, please tell us about access to your address. This includes stairs, restricted parking, shared entrances or anything that could make collection difficult. If permission is needed to enter

System's answer:
The passages don’t specify an arrival window for postcode area DD. Contact Halvard Home customer support to confirm the collection window for your address.

---

## 13. FOLLOW-018

Question: What about the Brio kettle?

Conversation so far:
User: How long should I keep the box my Keel washing machine came in?
Assistant: Keep the original packaging of the Keel washing machine for 30 days in case it needs to be returned.

Can the question be answered from the documents: yes

Reference answer: Keep the original packaging of the Brio kettle for 73 days in case it needs to be returned.

Passages given to the system:
[P1] Safety and recalls
surface or damage seals. Follow the supplied instructions for descaling, and keep cleaning products away from children and food preparation areas.

Clean the air vents of the Brio kettle every 75 days. Keep the kettle unplugged during this task. Gently remove dust from accessible vent surfaces with a soft, dry brush. Do not push objects through the vents or allow moisture to enter them. Never cover the vents during use.

Stop using the kettle if you notice smoke, sparks, a burning smell or unusual behaviour. Disconnect it if this can be done safely. Do not attempt to open the casing or repair electrical parts yourself. Contact Halvard Home for advice about inspection, repair or disposal.

If Halvard Home issues a safety notice or recall affecting your Brio kettle, follow the notice and stop using it when instructed. Do not pass an affected kettle to someone else. Keep its identification details available so that customer support can help you check whether it is covered.

### Installation and moving

Choose a stable, level worktop for the Brio kettle, where it cannot rock, slide or be knocked over. The surface must be dry and suitable for heat and splashes. Do not place the kettle on a cloth, tray with an uneven base, or unstable furniture.

Keep the kettle away

[P2] Safety and recalls
surface or damage seals. Follow the supplied instructions for descaling, and keep cleaning products away from children and food preparation areas.

Clean the air vents of the Brio kettle every 71 days. Keep the kettle unplugged during this task. Gently remove dust from accessible vent surfaces with a soft, dry brush. Do not push objects through the vents or allow moisture to enter them. Never cover the vents during use.

Stop using the kettle if you notice smoke, sparks, a burning smell or unusual behaviour. Disconnect it if this can be done safely. Do not attempt to open the casing or repair electrical parts yourself. Contact Halvard Home for advice about inspection, repair or disposal.

If Halvard Home issues a safety notice or recall affecting your Brio kettle, follow the notice and stop using it when instructed. Do not pass an affected kettle to someone else. Keep its identification details available so that customer support can help you check whether it is covered.

### Installation and moving

Choose a stable, level worktop for the Brio kettle, where it cannot rock, slide or be knocked over. The surface must be dry and suitable for heat and splashes. Do not place the kettle on a cloth, tray with an uneven base, or unstable furniture.

Keep the kettle away

[P3] # Brio kettle making a strange noise
# Brio kettle making a strange noise

A gentle rumbling or hissing sound while your Brio kettle heats up is usually normal. A click when it switches off is also expected.

Limescale can make boiling sound louder, especially in hard water areas. To check safely, unplug the kettle and leave it to cool for at least 30 minutes before looking inside. White or chalky deposits suggest it needs descaling. Follow the descaling instructions in your user guide, then rinse thoroughly before making a drink.

Check that the base is on a firm, level surface and the kettle is seated properly.

If the noise is sudden or unusually loud, or comes with leaking, a burning smell or visible damage, stop using the kettle and contact Halvard Home support.

[P4] Servicing and engineer visits
of the Brio kettle takes about 135 minutes. This is a guide rather than a guarantee. The engineer will explain if the condition of your kettle affects the planned work or if a fault means that a separate repair appointment is needed.

A routine service of the Brio kettle costs £78.00. This price includes the engineer’s routine inspection, standard service checks and assessment of the kettle’s condition. Repairs, replacement parts and work outside the routine service are not included unless we expressly confirm otherwise when you book.

We will explain any proposed additional work and its price before asking for your agreement. You do not have to accept a repair simply because an engineer recommends it. If you decline work needed for safe operation, the engineer will explain why the kettle should not be used.

To arrange a service, contact Halvard Home through our usual customer support channels. Have your purchase details available if you can, and describe any changes in how the kettle works. Tell us about leaking, unusual smells, unexpected switching behaviour or visible damage rather than leaving these concerns until the visit.

A service appointment is not a substitute for reporting a suspected safety fault. If the kettle appears unsafe, stop using it and disconnect it from the electricity supply if you can do so safely. Contact Halvard Home for

[P5] Servicing and engineer visits
of the Brio kettle takes about 135 minutes. This is a guide rather than a guarantee. The engineer will explain if the condition of your kettle affects the planned work or if a fault means that a separate repair appointment is needed.

A routine service of the Brio kettle costs £78.00. This price includes the engineer’s routine inspection, standard service checks and assessment of the kettle’s condition. Repairs, replacement parts and work outside the routine service are not included unless we expressly confirm otherwise when you book.

We will explain any proposed additional work and its price before asking for your agreement. You do not have to accept a repair simply because an engineer recommends it. If you decline work needed for safe operation, the engineer will explain why the kettle should not be used.

To arrange a service, contact Halvard Home through our usual customer support channels. Have your purchase details available if you can, and describe any changes in how the kettle works. Tell us about leaking, unusual smells, unexpected switching behaviour or visible damage rather than leaving these concerns until the visit.

A service appointment is not a substitute for reporting a suspected safety fault. If the kettle appears unsafe, stop using it and disconnect it from the electricity supply if you can do so safely. Contact Halvard Home for

System's answer:
The supplied passages don’t say how long to keep the Brio kettle’s original packaging. Contact Halvard Home support to confirm the recommended period.

---

## 14. DELETED-019

Question: What should I do if I have side brushes from batch 6199 for my Orrin heat pump?

Can the question be answered from the documents: no

Reference answer: That notice was withdrawn on 2026-04-30.

Passages given to the system:
[P1] Orrin heat pump side brush notice
Orrin heat pump side brush notice

Halvard Home is asking customers to check the batch details on their side brush packaging before fitting or using these accessories.

Stop using side brushes from batch 6199 with the Orrin heat pump, and return them for a refund.

If your brushes are affected, remove them from use and keep them separate from other accessories. Please contact Halvard Home customer support for guidance on arranging your return and refund.

If you cannot find the batch details, leave the brushes unused and ask our support team for help.

We are sorry for the inconvenience and appreciate your cooperation.

[P2] Side brushes for the Orrin heat pump
Side brushes for the Orrin heat pump

Stop using side brushes from batch 3424 with the Orrin heat pump, and return them for a refund.

We are recalling the affected side brushes as a precaution. Please check the batch label on the packaging before using a brush. If the label is missing or unclear, leave the brush unused and contact Halvard Home customer support for help identifying it.

Keep affected brushes separate from your other cleaning accessories. Contact Halvard Home customer support to arrange your return and refund. Please have your purchase details ready, if available.

We apologise for the inconvenience and appreciate your help in keeping our products safe to use.

[P3] Orrin lint filter recall
Orrin lint filter recall

Stop using lint filters from batch 7921 with the Orrin heat pump, and return them for a refund.

Check the batch marking on your filter packaging to find out whether your filter is affected. If the marking matches, switch off the appliance and remove the filter when safe. Do not use the heat pump without a suitable lint filter fitted.

Please keep the packaging to help us identify the affected batch. Contact Halvard Home customer support for help arranging your return and refund, or if the marking is missing, damaged or unclear.

We apologise for the inconvenience and appreciate your help in keeping your appliance safe.

[P4] Safety and recalls
assessment by a qualified professional rather than attempting a temporary repair.

Do not use an extension lead or an adaptor to supply the Orrin heat pump. Do not modify its wiring, bypass protective devices or interfere with the electrical isolator. Electrical work must be carried out by a qualified electrician.

Before cleaning, switch the appliance off and isolate its electrical supply using the method explained by your installer. Do not rely on a remote control, an app or a standby setting to prevent it from starting.

Let the Orrin heat pump cool for 33 minutes before cleaning it. Keep away from surfaces that remain hot and do not begin cleaning while there is a risk of burns. If safe access is uncertain, ask a qualified professional to help.

Clean the air vents every 118 days. Follow the supplied cleaning instructions and remove accessible surface debris without pushing it into the appliance. Do not remove protective guards or reach inside the casing to clean internal components.

Use the cleaning method described in the instructions. Do not direct a hose or pressure washer at the appliance, and do not apply solvents or abrasive cleaners. Stop if cleaning exposes damage or reveals a loose component.

Have the Orrin heat pump safety-checked every 25 months. Arrange this through Halvard Home or a suitably qualified service provider.

[P5] Safety and recalls
assessment by a qualified professional rather than attempting a temporary repair.

Do not use an extension lead or an adaptor to supply the Orrin heat pump. Do not modify its wiring, bypass protective devices or interfere with the electrical isolator. Electrical work must be carried out by a qualified electrician.

Before cleaning, switch the appliance off and isolate its electrical supply using the method explained by your installer. Do not rely on a remote control, an app or a standby setting to prevent it from starting.

Let the Orrin heat pump cool for 33 minutes before cleaning it. Keep away from surfaces that remain hot and do not begin cleaning while there is a risk of burns. If safe access is uncertain, ask a qualified professional to help.

Clean the air vents every 118 days. Follow the supplied cleaning instructions and remove accessible surface debris without pushing it into the appliance. Do not remove protective guards or reach inside the casing to clean internal components.

Use the cleaning method described in the instructions. Do not direct a hose or pressure washer at the appliance, and do not apply solvents or abrasive cleaners. Stop if cleaning exposes damage or reveals a loose component.

Have the Orrin heat pump safety-checked every 25 months. Arrange this through Halvard Home or a suitably qualified service provider.

System's answer:
Stop using side brushes from batch **6199** with your Orrin heat pump. Keep them separate from your other accessories, and contact **Halvard Home customer support** to arrange a return and refund. [P1]

---

## 15. VERSION-015

Question: How long are replacement parts for the Corra induction hob covered after they’re installed?

Can the question be answered from the documents: yes

Reference answer: Replacement parts fitted to the Corra induction hob are covered for a further 189 days.

Passages given to the system:
[P1] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 302 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

[P2] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 189 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

[P3] Warranty
Please use it in accordance with the instructions provided and take reasonable care of it. Tell us if it develops a fault so that we can help.

The engineer will check the repaired appliance and explain the work carried out. Ask about anything you do not understand, including whether it is ready to use. If the fault remains or returns, contact us and describe what you have noticed so that we can review the repair.

Please take care with food affected by a cooling fault and follow appropriate food safety advice. Do not rely on smell or appearance alone to decide whether food is safe. Tell us about losses you believe resulted from the fault; we will explain how to submit a claim and how it will be assessed.

Your warranty does not replace or restrict your statutory rights. You may also have rights against the retailer that sold you the appliance. If you disagree with a warranty decision or are unhappy with the repair, contact Halvard Home customer support and ask for your complaint to be reviewed.

## Corra induction hob

### Cover period

The Corra induction hob is covered for 43 months from the date of delivery. This is the warranty period for the appliance. It begins when the hob is delivered to you, rather than when you install it, register it or start using it.

Keep your

[P4] Warranty
Please use it in accordance with the instructions provided and take reasonable care of it. Tell us if it develops a fault so that we can help.

The engineer will check the repaired appliance and explain the work carried out. Ask about anything you do not understand, including whether it is ready to use. If the fault remains or returns, contact us and describe what you have noticed so that we can review the repair.

Please take care with food affected by a cooling fault and follow appropriate food safety advice. Do not rely on smell or appearance alone to decide whether food is safe. Tell us about losses you believe resulted from the fault; we will explain how to submit a claim and how it will be assessed.

Your warranty does not replace or restrict your statutory rights. You may also have rights against the retailer that sold you the appliance. If you disagree with a warranty decision or are unhappy with the repair, contact Halvard Home customer support and ask for your complaint to be reviewed.

## Corra induction hob

### Cover period

The Corra induction hob is covered for 43 months from the date of delivery. This is the warranty period for the appliance. It begins when the hob is delivered to you, rather than when you install it, register it or start using it.

Keep your

[P5] Servicing and engineer visits
Do not wash a filter unless the user instructions state that it is washable.

Our engineer will use parts approved for the Corra induction hob. Spare parts for the Corra induction hob are stocked for 5 years after the model is discontinued. Availability of a particular component may still affect when a repair can be arranged. We will discuss any supply problem with you.

Please make sure the hob can be reached safely and that the area around it is clear. Tell us about restricted access, fixed panels or installation changes when booking. If safe access requires alterations to cabinetry or the worktop, we will explain what must be arranged before repair work can proceed.

Repairs are guaranteed for 150 days. This guarantee covers the work carried out and the parts fitted as part of that repair. It does not cover unrelated faults, accidental damage, misuse or problems caused by unauthorised alterations. Your statutory rights are not affected.

If the repaired fault returns, contact us and describe the symptoms. Keep your repair paperwork available so we can review the work completed. We will assess whether the issue falls within the repair guarantee and explain any proposed charge before you agree to further work.

After completing the repair, the engineer will carry out the relevant safety and operating checks and explain any care instructions. If

System's answer:
The passages conflict: **P1 says 302 days**, while **P2 says 189 days**, starting from the date the part is fitted during an authorised repair. The provided information therefore does not establish a single coverage period.

---

## 16. VERSION-024

Question: How much room should I leave around the Corra induction hob?

Can the question be answered from the documents: yes

Reference answer: Leave at least 11 centimetres of space around the Corra induction hob.

Passages given to the system:
[P1] Safety and recalls
understands the controls and the precautions described here.

Arrange installation through a suitably qualified professional. The electrical supply, connection and supporting surface must meet the requirements in the installation instructions. Do not use an extension lead or an adaptor. Do not alter the wiring, casing or protective parts, or attempt to fit the hob where its ventilation would be obstructed.

Leave at least 31 centimetres of space around the Corra induction hob. Keep this space clear of packaging, utensils and household items. Follow the installation instructions for positioning near walls, cupboards and other surfaces. If the proposed position does not meet those instructions, do not use the hob there.

Check the glass, controls and accessible cable for damage before use. Do not operate the hob if the glass is cracked, the cable is damaged or the controls behave unexpectedly. Switch it off and disconnect the electrical supply if safe. Contact Halvard Home for advice rather than attempting a repair yourself.

Choose cookware that the hob instructions identify as suitable for induction cooking. Its base should be flat, clean and dry. Position it securely over the cooking zone and keep handles away from edges and neighbouring heat sources. Lift cookware rather than dragging it across the glass, which can scratch or damage the surface.

Stay with the hob while

[P2] Safety and recalls
understands the controls and the precautions described here.

Arrange installation through a suitably qualified professional. The electrical supply, connection and supporting surface must meet the requirements in the installation instructions. Do not use an extension lead or an adaptor. Do not alter the wiring, casing or protective parts, or attempt to fit the hob where its ventilation would be obstructed.

Leave at least 11 centimetres of space around the Corra induction hob. Keep this space clear of packaging, utensils and household items. Follow the installation instructions for positioning near walls, cupboards and other surfaces. If the proposed position does not meet those instructions, do not use the hob there.

Check the glass, controls and accessible cable for damage before use. Do not operate the hob if the glass is cracked, the cable is damaged or the controls behave unexpectedly. Switch it off and disconnect the electrical supply if safe. Contact Halvard Home for advice rather than attempting a repair yourself.

Choose cookware that the hob instructions identify as suitable for induction cooking. Its base should be flat, clean and dry. Position it securely over the cooking zone and keep handles away from edges and neighbouring heat sources. Lift cookware rather than dragging it across the glass, which can scratch or damage the surface.

Stay with the hob while

[P3] Moving your Corra induction hob
Moving your Corra induction hob

Switch off the hob at the mains before preparing it for transport. If it is hardwired, ask a qualified electrician to disconnect it; do not cut or pull the cable.

Let the glass cool completely, then remove all cookware and loose items. Do not try to lift the hob while it is still secured to the worktop. Ask your installer to release any fixings or seals.

Use two people to lift the unit, supporting its body rather than pulling on the glass edges or cable. Pack it in its original packaging if available, with cushioning to prevent movement. Keep heavy objects off the glass.

After transport, have the hob checked and installed by a qualified installer before use.

[P4] Safety and recalls
. Keep the installation instructions somewhere you can find them without reaching across a hot cooking surface.

Before moving the hob, switch it off and let the cooking surface cool. Arrange for a qualified electrician to isolate and disconnect a fixed electrical connection. Do not assume that a dark display means the appliance is electrically isolated, and do not pull on the cable to release it.

Clear the carrying route and prepare a secure place to set the appliance down. Remove loose cookware and protect the glass against knocks. Arrange suitable assistance or lifting equipment rather than trying to manage an awkward load unaided. Keep children and pets away from the work area.

Do not tilt the Corra induction hob more than 54 degrees when carrying it.

Support the appliance by the parts identified for handling in its installation instructions. Do not lift it by the cable, controls or exposed glass edges. If it catches on the worktop or surrounding fittings, stop and have the obstruction checked rather than forcing it free.

For transport, use packaging that protects the glass and casing, and secure the appliance against sliding or impact. Do not place objects on top of it. Tell the person transporting it about the carrying restriction and make sure the cable is protected from crushing.

After moving the Corra induction hob, wait 17

[P5] Safety and recalls
. Keep the installation instructions somewhere you can find them without reaching across a hot cooking surface.

Before moving the hob, switch it off and let the cooking surface cool. Arrange for a qualified electrician to isolate and disconnect a fixed electrical connection. Do not assume that a dark display means the appliance is electrically isolated, and do not pull on the cable to release it.

Clear the carrying route and prepare a secure place to set the appliance down. Remove loose cookware and protect the glass against knocks. Arrange suitable assistance or lifting equipment rather than trying to manage an awkward load unaided. Keep children and pets away from the work area.

Do not tilt the Corra induction hob more than 48 degrees when carrying it.

Support the appliance by the parts identified for handling in its installation instructions. Do not lift it by the cable, controls or exposed glass edges. If it catches on the worktop or surrounding fittings, stop and have the obstruction checked rather than forcing it free.

For transport, use packaging that protects the glass and casing, and secure the appliance against sliding or impact. Do not place objects on top of it. Tell the person transporting it about the carrying restriction and make sure the cable is protected from crushing.

After moving the Corra induction hob, wait 31

System's answer:
The passages give conflicting clearances: **31 cm in P1** and **11 cm in P2**. Check the hob’s installation instructions or contact Halvard Home to confirm the required space before installing it.

---

## 17. SHARED-007

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

## 18. ABSENT-005

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

## 19. FOLLOW-003

Question: And the Tessa dishwasher?

Conversation so far:
User: How much room should I leave around the Brio kettle?
Assistant: Leave at least 24 centimetres of space around the Brio kettle.

Can the question be answered from the documents: yes

Reference answer: Leave at least 4 centimetres of space around the Tessa dishwasher.

Passages given to the system:
[P1] Safety and recalls
reached for servicing. Do not install it where frost, rain or standing water could affect its safe operation.

The Tessa dishwasher must not be placed near an open flame. Install it at least 146 centimetres from a gas hob or open flame. Keep packaging, cleaning cloths and other combustible materials away from cooking equipment while preparing the installation area. If the proposed position is unsuitable, choose a different location.

The electrical supply must be suitable for the appliance and properly earthed. It must be installed within 234 centimetres of its socket. The plug and socket must remain accessible after installation. Do not use an extension lead, an adaptor or a trailing socket to reach the appliance.

Ask a qualified electrician to resolve concerns about the socket, earthing or electrical supply. Never alter the plug or cable to make the appliance fit. Route the cable so it cannot become trapped beneath the appliance, caught by the door or pressed against a hot surface or sharp edge.

Water and drainage connections must follow the supplied installation instructions. Have a competent installer make these connections if you cannot do so safely. Use the specified connection parts and make sure hoses are not kinked, stretched or crushed. Keep the water shut-off valve accessible so the supply can be isolated.

Secure

[P2] Safety and recalls
reached for servicing. Do not install it where frost, rain or standing water could affect its safe operation.

The Tessa dishwasher must not be placed near an open flame. Install it at least 146 centimetres from a gas hob or open flame. Keep packaging, cleaning cloths and other combustible materials away from cooking equipment while preparing the installation area. If the proposed position is unsuitable, choose a different location.

The electrical supply must be suitable for the appliance and properly earthed. It must be installed within 234 centimetres of its socket. The plug and socket must remain accessible after installation. Do not use an extension lead, an adaptor or a trailing socket to reach the appliance.

Ask a qualified electrician to resolve concerns about the socket, earthing or electrical supply. Never alter the plug or cable to make the appliance fit. Route the cable so it cannot become trapped beneath the appliance, caught by the door or pressed against a hot surface or sharp edge.

Water and drainage connections must follow the supplied installation instructions. Have a competent installer make these connections if you cannot do so safely. Use the specified connection parts and make sure hoses are not kinked, stretched or crushed. Keep the water shut-off valve accessible so the supply can be isolated.

Secure

[P3] Safety and recalls
trip. Do not stand, sit or lean on it, and do not let children climb onto it or reach inside. Check that pets are clear before closing the door.

Avoid opening the door during a programme. Hot water and steam can escape and cause burns. If opening is necessary, use the pause or stop control as described in the operating instructions, then open the door cautiously. Keep your face and hands away from escaping steam.

Dishes and internal surfaces can remain hot after a programme ends. Allow them to cool until they can be handled safely. Take care when unloading glassware, and do not reach into cloudy water or concealed spaces where broken glass or sharp objects may be present.

Let the Tessa dishwasher cool for 11 minutes before cleaning it. Disconnect it from the electrical supply before carrying out cleaning that the instructions require to be done without power. If surfaces remain hot, allow them to become safe to touch. Never spray water onto electrical parts or use a steam cleaner.

Clean the air vents of the Tessa dishwasher every 98 days. Follow the cleaning instructions for the filters, seals and accessible surfaces. Wear protective gloves if there is a risk of contact with sharp debris. Do not remove protective panels or attempt repairs yourself.

Stop using the appliance if it leaks,

[P4] Safety and recalls
trip. Do not stand, sit or lean on it, and do not let children climb onto it or reach inside. Check that pets are clear before closing the door.

Avoid opening the door during a programme. Hot water and steam can escape and cause burns. If opening is necessary, use the pause or stop control as described in the operating instructions, then open the door cautiously. Keep your face and hands away from escaping steam.

Dishes and internal surfaces can remain hot after a programme ends. Allow them to cool until they can be handled safely. Take care when unloading glassware, and do not reach into cloudy water or concealed spaces where broken glass or sharp objects may be present.

Let the Tessa dishwasher cool for 7 minutes before cleaning it. Disconnect it from the electrical supply before carrying out cleaning that the instructions require to be done without power. If surfaces remain hot, allow them to become safe to touch. Never spray water onto electrical parts or use a steam cleaner.

Clean the air vents of the Tessa dishwasher every 98 days. Follow the cleaning instructions for the filters, seals and accessible surfaces. Wear protective gloves if there is a risk of contact with sharp debris. Do not remove protective panels or attempt repairs yourself.

Stop using the appliance if it leaks,

[P5] Installing your Tessa dishwasher
Installing your Tessa dishwasher

Before installing your Halvard Home Tessa dishwasher, remove all packaging and check for transport damage. Do not connect the appliance if it is damaged.

Switch off the electricity and turn off the water supply before connecting anything. Follow the supplied installation guide when attaching the inlet and drain hoses. Make sure neither hose is kinked or trapped behind the dishwasher.

Adjust the feet until the dishwasher is level and stable. Connect it to an earthed socket; do not use an extension lead. If plumbing or electrical work is needed, use a qualified professional.

Turn the water supply back on and check the connections for leaks. Before loading dishes, run one empty wash cycle, following the installation guide’s first-use instructions.

System's answer:
For the Tessa dishwasher, leave at least **146 cm between it and a gas hob or open flame**, and install it **within 234 cm of its socket**. The passages don’t specify a general clearance around it.

---

## 20. PARA-014

Question: How can I safely relocate my built-in cooktop?

Can the question be answered from the documents: yes

Reference answer: Use two people to lift the unit, supporting its body rather than pulling on the glass edges or cable.

Passages given to the system:
[P1] Safety and recalls
heat.

Install it at least 118 centimetres from a gas hob or open flame. Also follow the siting requirements supplied with your cooking appliance. If the requirements cannot be met together, do not proceed. Ask a qualified installer to assess a suitable alternative location.

Keep the ventilation openings clear. Do not cover them with packaging, furniture, curtains or stored items. Follow the supplied installation instructions for positioning the appliance beside walls and cabinets. Do not enclose it in furniture unless those instructions expressly allow that arrangement.

Plan a clear route before bringing the appliance into position. Remove obstacles and protect flooring without creating a slipping hazard. Keep children and pets away from the work area. Arrange trained help and suitable moving equipment rather than attempting to lift or control the appliance unaided.

Do not lift, pull or steer the appliance by its doors, handles, shelves or pipework. These parts are not lifting points and may break or become detached. Use the handling points and methods described in the supplied instructions, keeping hands clear of trapping points.

Keep the appliance upright during handling and transport, following the transport instructions supplied with it. Secure it against sliding or falling using suitable equipment that will not damage the cabinet. Do not drag it across the floor or let its weight rest on the power cable

[P2] Safety and recalls
heat.

Install it at least 118 centimetres from a gas hob or open flame. Also follow the siting requirements supplied with your cooking appliance. If the requirements cannot be met together, do not proceed. Ask a qualified installer to assess a suitable alternative location.

Keep the ventilation openings clear. Do not cover them with packaging, furniture, curtains or stored items. Follow the supplied installation instructions for positioning the appliance beside walls and cabinets. Do not enclose it in furniture unless those instructions expressly allow that arrangement.

Plan a clear route before bringing the appliance into position. Remove obstacles and protect flooring without creating a slipping hazard. Keep children and pets away from the work area. Arrange trained help and suitable moving equipment rather than attempting to lift or control the appliance unaided.

Do not lift, pull or steer the appliance by its doors, handles, shelves or pipework. These parts are not lifting points and may break or become detached. Use the handling points and methods described in the supplied instructions, keeping hands clear of trapping points.

Keep the appliance upright during handling and transport, following the transport instructions supplied with it. Secure it against sliding or falling using suitable equipment that will not damage the cabinet. Do not drag it across the floor or let its weight rest on the power cable

[P3] Safety and recalls
. Keep the installation instructions somewhere you can find them without reaching across a hot cooking surface.

Before moving the hob, switch it off and let the cooking surface cool. Arrange for a qualified electrician to isolate and disconnect a fixed electrical connection. Do not assume that a dark display means the appliance is electrically isolated, and do not pull on the cable to release it.

Clear the carrying route and prepare a secure place to set the appliance down. Remove loose cookware and protect the glass against knocks. Arrange suitable assistance or lifting equipment rather than trying to manage an awkward load unaided. Keep children and pets away from the work area.

Do not tilt the Corra induction hob more than 48 degrees when carrying it.

Support the appliance by the parts identified for handling in its installation instructions. Do not lift it by the cable, controls or exposed glass edges. If it catches on the worktop or surrounding fittings, stop and have the obstruction checked rather than forcing it free.

For transport, use packaging that protects the glass and casing, and secure the appliance against sliding or impact. Do not place objects on top of it. Tell the person transporting it about the carrying restriction and make sure the cable is protected from crushing.

After moving the Corra induction hob, wait 31

[P4] Safety and recalls
. Keep the installation instructions somewhere you can find them without reaching across a hot cooking surface.

Before moving the hob, switch it off and let the cooking surface cool. Arrange for a qualified electrician to isolate and disconnect a fixed electrical connection. Do not assume that a dark display means the appliance is electrically isolated, and do not pull on the cable to release it.

Clear the carrying route and prepare a secure place to set the appliance down. Remove loose cookware and protect the glass against knocks. Arrange suitable assistance or lifting equipment rather than trying to manage an awkward load unaided. Keep children and pets away from the work area.

Do not tilt the Corra induction hob more than 54 degrees when carrying it.

Support the appliance by the parts identified for handling in its installation instructions. Do not lift it by the cable, controls or exposed glass edges. If it catches on the worktop or surrounding fittings, stop and have the obstruction checked rather than forcing it free.

For transport, use packaging that protects the glass and casing, and secure the appliance against sliding or impact. Do not place objects on top of it. Tell the person transporting it about the carrying restriction and make sure the cable is protected from crushing.

After moving the Corra induction hob, wait 17

[P5] Moving your Corra induction hob
Moving your Corra induction hob

Switch off the hob at the mains before preparing it for transport. If it is hardwired, ask a qualified electrician to disconnect it; do not cut or pull the cable.

Let the glass cool completely, then remove all cookware and loose items. Do not try to lift the hob while it is still secured to the worktop. Ask your installer to release any fixings or seals.

Use two people to lift the unit, supporting its body rather than pulling on the glass edges or cable. Pack it in its original packaging if available, with cushioning to prevent movement. Keep heavy objects off the glass.

After transport, have the hob checked and installed by a qualified installer before use.

System's answer:
To safely relocate your built-in cooktop:

1. **Switch it off and let the glass cool completely.** If it is hardwired, have a qualified electrician isolate and disconnect it. A dark display does not prove it is electrically isolated. Never cut or pull the cable.
2. **Have an installer release the fixings or seals** securing it to the worktop. Do not lift it while it is still attached or force it free if it catches.
3. **Prepare the route and lifting area.** Remove cookware and loose items, clear obstacles, prepare a secure place to set it down, and keep children and pets away.
4. **Use two people or suitable lifting equipment.** Support the body at the handling points specified in the installation instructions—not by the cable, controls, or exposed glass edges.
5. **Protect it during transport.** Use the original packaging if available, or suitable cushioning that protects the glass and casing. Secure it against sliding and impact, protect the cable from crushing, and place nothing on top.
6. **Have a qualified installer check and reinstall it before use.** [P3–P5]

**Check the model-specific instructions for carrying-angle and waiting-time restrictions.** The supplied Corra passages conflict on the maximum tilt angle (48° versus 54°), and their post-move waiting times are incomplete, so neither should be treated as a confirmed requirement. [P3–P4]

---

## 21. DISTRACT-011

Question: How long does it take you to check a Fenwick cooker hood after you receive it back?

Can the question be answered from the documents: yes

Reference answer: A returned Fenwick cooker hood is inspected within 38 days of arrival.

Passages given to the system:
[P1] Returns and refunds
make sure it is disconnected safely. If it is wired into your electrical supply, arrange for a qualified electrician to disconnect it. Do not cut cables or attempt work you are not qualified to carry out. Collection does not include removal from its installed position.

Allow the appliance to cool and make sure it is clean and dry before handling it. Take care around exposed edges and loose fittings. If the appliance is damaged in a way that makes it unsafe to move or pack, contact us for advice rather than trying to prepare it yourself.

Use the original packaging if you still have it and it is suitable for transport. Otherwise, use strong packaging that protects the appliance and prevents movement inside the package. Protect exposed surfaces and secure loose parts separately so they cannot scratch or damage the appliance during handling.

An exchange for a Fenwick cooker hood in a different colour must be requested within 96 days.

Tell us which colour you would prefer when making your request. An exchange depends on availability, and we will confirm what we can offer before you send the appliance back. Please do not assume that requesting an exchange reserves stock or confirms dispatch.

Include the accessories, fittings and documents supplied with the appliance unless we have asked you to retain them. Let us know if anything is missing. Do not include unrelated

[P2] Returns and refunds
make sure it is disconnected safely. If it is wired into your electrical supply, arrange for a qualified electrician to disconnect it. Do not cut cables or attempt work you are not qualified to carry out. Collection does not include removal from its installed position.

Allow the appliance to cool and make sure it is clean and dry before handling it. Take care around exposed edges and loose fittings. If the appliance is damaged in a way that makes it unsafe to move or pack, contact us for advice rather than trying to prepare it yourself.

Use the original packaging if you still have it and it is suitable for transport. Otherwise, use strong packaging that protects the appliance and prevents movement inside the package. Protect exposed surfaces and secure loose parts separately so they cannot scratch or damage the appliance during handling.

An exchange for a Fenwick cooker hood in a different colour must be requested within 96 days.

Tell us which colour you would prefer when making your request. An exchange depends on availability, and we will confirm what we can offer before you send the appliance back. Please do not assume that requesting an exchange reserves stock or confirms dispatch.

Include the accessories, fittings and documents supplied with the appliance unless we have asked you to retain them. Let us know if anything is missing. Do not include unrelated

[P3] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P4] Warranty
being confirmed. We are responsible for arranging the work and obtaining the parts needed. If there is a problem with the arrangements, we will contact you and explain how we will resolve it.

If a repair to the Fenwick cooker hood takes longer than 10 working days, Halvard Home lends a replacement. We will contact you to arrange the loan, explain how the replacement can be used safely and organise any installation needed for its safe use.

The loan replacement remains the property of Halvard Home. There is no loan charge while your warranty repair is being completed. We will explain the care arrangements and agree how it will be collected, without leaving you responsible for disconnecting equipment that requires professional attention.

Our engineer will assess the fault and carry out the work needed to restore normal operation. This may involve adjusting the appliance or replacing faulty parts. We use suitable parts that meet our safety and performance requirements, and we may use refurbished parts where appropriate.

A refurbished part fitted to the Fenwick cooker hood is covered for 17 weeks. This cover applies to defects in the fitted part and includes the work needed to put those defects right. It does not reduce any protection remaining under your appliance warranty.

Please tell us if the fault continues after the repair or if you notice a problem with the work

[P5] Warranty
checks that you can safely carry out yourself. You do not need to remove covers, handle wiring or dismantle the appliance to make a claim.

Stop using the Fenwick cooker hood if it produces smoke, smells of burning or appears electrically unsafe. Disconnect it from the electricity supply if you can do so safely. Tell us about the concern when you contact us so that we can arrange appropriate support.

We confirm a fault through the information you provide, remote assessment or an engineer’s inspection, as appropriate. We will tell you when the fault has been confirmed and whether it is covered. If we decline cover, we will explain the reason clearly and give you the opportunity to provide further information.

Warranty cover applies to faults arising from defective materials or workmanship under normal household use. It does not cover damage caused by misuse, accidental damage, unsuitable installation or alterations that cause the fault. A fault unrelated to such circumstances will still be assessed fairly.

Where an engineer needs to visit, we will agree an appointment with you. Please make sure the engineer can safely reach the Fenwick cooker hood and its electrical connection. Let us know about access restrictions or support needs when the appointment is arranged.

A warranty repair to the Fenwick cooker hood is completed within 37 working days of the fault

System's answer:
The passages provided do not state how long it takes to check a Fenwick cooker hood after receiving it back.

---

## 22. PARA-016

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

## 23. RESTRICT-STAFF-035

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

## 24. IDENT-030

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

## 25. TOPIC-014

Question: What is the bottle capacity of the Halvard wine cooler?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Vale fridge freezer warranty period
Vale fridge freezer warranty period

Your Halvard Home Vale fridge freezer comes with a two-year warranty from the date of purchase. Keep your receipt or order confirmation as proof of when cover began.

On this model, E-5338 means the purchase date is missing from the appliance’s warranty record, preventing it from displaying the correct warranty end date. This is a registration fault, not a cooling fault, and does not itself mean your warranty has expired.

Contact Halvard Home support with your proof of purchase and ask for the warranty record to be corrected. There is no need to unplug the appliance or change its temperature settings for this message.

Your warranty does not affect your statutory rights.

[P2] Ordering a spare accessory for your Vale fridge freezer
Ordering a spare accessory for your Vale fridge freezer

To order a spare accessory, contact Halvard Home customer support with your fridge freezer’s model details and the name of the item you need, such as a shelf, drawer or door tray.

Before contacting support, take one clear photo of the accessory and one of the space where it fits. If the accessory is missing, photograph the empty space instead. This helps support identify the right replacement.

Ask support to confirm compatibility, the total price including delivery, and the expected delivery time before placing your order. Do not choose an accessory by appearance alone, as similar items may have different fittings.

Keep your order confirmation until the replacement arrives and you have checked that it fits.

[P3] Vale fridge freezer cooling slowly
Vale fridge freezer cooling slowly

On the Vale fridge freezer, E-7190 means the freezer’s air circulation fan is running too slowly, reducing the flow of cold air and weakening cooling.

Check that food packets are not covering the air vents inside either compartment. Leave a clear gap around each vent, and make sure both doors close fully.

Set the fridge to 4°C and the freezer to −18°C. Keep the doors closed as much as possible and allow six hours for cooling to improve.

If the warning remains or returns, contact Halvard Home support to arrange a fan inspection. Do not remove internal panels or try to turn the fan yourself. Move perishable food to another working fridge if it is no longer staying cold.

[P4] Frost or condensation in your Vale fridge freezer
Frost or condensation in your Vale fridge freezer

Frost or water droplets can build up when warm, moist air enters the appliance. Frequent door opening, uncovered food and a poor door seal can make this worse.

Set the fridge to 4°C and the freezer to −18°C. Check that food containers are not stopping either door from closing fully. Wipe the door seals with a soft cloth and warm, soapy water, then dry them.

Cover food and wipe away condensation with a clean cloth. Keep internal air vents clear so cold air can circulate.

If thick ice builds up, unplug the appliance and move food to suitable cold storage before defrosting. Never use sharp tools or a hairdryer to remove ice.

Contact Halvard Home support if the build-up keeps returning.

[P5] Returns and refunds
contact Halvard Home for advice. Do not assume that damage to the outer box means the appliance itself is damaged.

If you have already disposed of the original packaging, tell us before arranging a return. Do not pack the Vale fridge freezer in an unsuitable substitute or send it without protection. We will discuss how it can be collected safely. Missing packaging does not, by itself, remove your statutory rights.

Handle the Vale fridge freezer carefully while deciding whether it is suitable for your home. You may inspect it as you would reasonably inspect an appliance in a shop. Avoid removing protective materials unnecessarily, and take care not to scratch the finish, damage the fittings or mark the interior.

If you are returning it because you have changed your mind, tell us whether it has been installed, connected or used. Describe its condition honestly, including marks or damage. Use does not automatically prevent a return, but handling beyond what is needed to inspect it may affect your refund where the law allows.

If you believe the Vale fridge freezer is faulty, describe the problem rather than trying to repair it. Do not remove panels, alter wiring or dismantle fittings that are not intended to be removed by the customer. Contact us for guidance if the fault makes disconnecting, moving or packing it unsafe.

Before preparing an

System's answer:
The provided passages don’t state the bottle capacity of the Halvard wine cooler. They only cover the Vale fridge freezer.

---

## 26. POL-HEAD-000

Question: How often should I change the filter in my Corra induction hob?

Can the question be answered from the documents: yes

Reference answer: Replace the filter of the Corra induction hob every 24 weeks.

Passages given to the system:
[P1] Cleaning your Corra hob filter
Cleaning your Corra hob filter

Switch off your Corra induction hob and its extractor, then let everything cool before cleaning the filter.

Remove the filter as shown in your user manual. Avoid forcing it if it does not lift out easily. Wash it in warm water with a little washing-up liquid, using a soft brush to loosen grease. Rinse thoroughly with clean water.

Do not use abrasive pads, oven cleaner or sharp tools, as these can damage the filter. Let it dry completely before refitting it, and check that it sits securely in place.

Wipe the surrounding accessible area with a soft, damp cloth. Never pour water into the extractor opening. If the filter is damaged or will not fit securely, contact Halvard Home support.

[P2] Servicing and engineer visits
Do not wash a filter unless the user instructions state that it is washable.

Our engineer will use parts approved for the Corra induction hob. Spare parts for the Corra induction hob are stocked for 20 years after the model is discontinued. Availability of a particular component may still affect when a repair can be arranged. We will discuss any supply problem with you.

Please make sure the hob can be reached safely and that the area around it is clear. Tell us about restricted access, fixed panels or installation changes when booking. If safe access requires alterations to cabinetry or the worktop, we will explain what must be arranged before repair work can proceed.

Repairs are guaranteed for 150 days. This guarantee covers the work carried out and the parts fitted as part of that repair. It does not cover unrelated faults, accidental damage, misuse or problems caused by unauthorised alterations. Your statutory rights are not affected.

If the repaired fault returns, contact us and describe the symptoms. Keep your repair paperwork available so we can review the work completed. We will assess whether the issue falls within the repair guarantee and explain any proposed charge before you agree to further work.

After completing the repair, the engineer will carry out the relevant safety and operating checks and explain any care instructions. If

[P3] Servicing and engineer visits
Do not wash a filter unless the user instructions state that it is washable.

Our engineer will use parts approved for the Corra induction hob. Spare parts for the Corra induction hob are stocked for 5 years after the model is discontinued. Availability of a particular component may still affect when a repair can be arranged. We will discuss any supply problem with you.

Please make sure the hob can be reached safely and that the area around it is clear. Tell us about restricted access, fixed panels or installation changes when booking. If safe access requires alterations to cabinetry or the worktop, we will explain what must be arranged before repair work can proceed.

Repairs are guaranteed for 150 days. This guarantee covers the work carried out and the parts fitted as part of that repair. It does not cover unrelated faults, accidental damage, misuse or problems caused by unauthorised alterations. Your statutory rights are not affected.

If the repaired fault returns, contact us and describe the symptoms. Keep your repair paperwork available so we can review the work completed. We will assess whether the issue falls within the repair guarantee and explain any proposed charge before you agree to further work.

After completing the repair, the engineer will carry out the relevant safety and operating checks and explain any care instructions. If

[P4] Safety and recalls
treat a residual heat warning as a sign that contact may cause burns. Do not rely on the display if the electrical supply has been interrupted or the appliance appears faulty.

Let the Corra induction hob cool for 114 minutes before cleaning it. Do not clean the surface while it remains warm, even after this cooling period. Switch off the hob and isolate its electrical supply before cleaning. Follow the care instructions for removing spills without exposing yourself to heat or damaging the glass.

Use a soft cloth and a cleaning product recommended in the care instructions. Do not use abrasive pads, corrosive cleaners or steam-cleaning equipment. Avoid letting liquid enter the casing, controls or electrical connections. Dry the surface before use, and remove cleaning residue that could affect the controls or mark the glass.

Clean the air vents of the Corra induction hob every 16 days. Follow the instructions for accessing and cleaning them without removing protective covers. Keep ventilation openings free from grease, dust and obstructions. Do not push tools into the vents. Contact Halvard Home if you cannot clean them safely.

Have the Corra induction hob safety-checked every 6 months. Arrange this through a suitably qualified professional and keep the service record. A scheduled check does not replace action when a fault appears. Stop using the hob

[P5] Safety and recalls
treat a residual heat warning as a sign that contact may cause burns. Do not rely on the display if the electrical supply has been interrupted or the appliance appears faulty.

Let the Corra induction hob cool for 114 minutes before cleaning it. Do not clean the surface while it remains warm, even after this cooling period. Switch off the hob and isolate its electrical supply before cleaning. Follow the care instructions for removing spills without exposing yourself to heat or damaging the glass.

Use a soft cloth and a cleaning product recommended in the care instructions. Do not use abrasive pads, corrosive cleaners or steam-cleaning equipment. Avoid letting liquid enter the casing, controls or electrical connections. Dry the surface before use, and remove cleaning residue that could affect the controls or mark the glass.

Clean the air vents of the Corra induction hob every 16 days. Follow the instructions for accessing and cleaning them without removing protective covers. Keep ventilation openings free from grease, dust and obstructions. Do not push tools into the vents. Contact Halvard Home if you cannot clean them safely.

Have the Corra induction hob safety-checked every 6 months. Arrange this through a suitably qualified professional and keep the service record. A scheduled check does not replace action when a fault appears. Stop using the hob

System's answer:
The passages don’t specify how often to replace the filter. They recommend cleaning it according to the user manual, but only washing it if the instructions say it is washable. If the filter is damaged or won’t fit securely, contact Halvard Home support. [P1–P3]

---

## 27. BRIDGE-009

Question: How long do parts for warranty repairs take to arrive at my home in postcode area HS?

Can the question be answered from the documents: yes

Reference answer: The Island Areas service team covers postcode areas GY, JE, IM, HS and ZE. Parts for warranty repairs in Island Areas arrive within 59 working days.

Passages given to the system:
[P1] Warranty
Areas

### Warranty repairs in this region

Warranty repairs in Island Areas are arranged through Halvard Home or an authorised service partner. Contact our customer care team to report a fault and explain what has happened. We will help you understand whether the repair can be handled under your warranty.

Please have your proof of purchase available when you contact us. We may also ask for photographs of the fault, a description of how the appliance behaves and details of where it is installed. This helps us assess the claim and arrange suitable support.

We will tell you when your claim has been accepted. Acceptance means that we have assessed the information supplied and agreed to arrange a repair under the warranty, subject to the engineer confirming that the reported fault is covered.

In Island Areas, a warranty engineer visit is offered within 89 hours of a claim being accepted.

This commitment concerns the offer of a visit, rather than completion of the repair. We will contact you to discuss an appointment and explain the arrangements for reaching your address. The appointment offered will take account of local travel conditions and access requirements.

Island travel may depend on ferry services, weather conditions and local transport arrangements. Tell us about access restrictions when you report the fault. This could include a private landing point, a restricted road or a property

[P2] Warranty
Areas

### Warranty repairs in this region

Warranty repairs in Island Areas are arranged through Halvard Home or an authorised service partner. Contact our customer care team to report a fault and explain what has happened. We will help you understand whether the repair can be handled under your warranty.

Please have your proof of purchase available when you contact us. We may also ask for photographs of the fault, a description of how the appliance behaves and details of where it is installed. This helps us assess the claim and arrange suitable support.

We will tell you when your claim has been accepted. Acceptance means that we have assessed the information supplied and agreed to arrange a repair under the warranty, subject to the engineer confirming that the reported fault is covered.

In Island Areas, a warranty engineer visit is offered within 89 hours of a claim being accepted.

This commitment concerns the offer of a visit, rather than completion of the repair. We will contact you to discuss an appointment and explain the arrangements for reaching your address. The appointment offered will take account of local travel conditions and access requirements.

Island travel may depend on ferry services, weather conditions and local transport arrangements. Tell us about access restrictions when you report the fault. This could include a private landing point, a restricted road or a property

[P3] Warranty
warranty terms that apply to your purchase. Acceptance means we have confirmed that your claim qualifies for the warranty repair service, based on the information available. If an inspection reveals a different cause, we will explain what this means for your cover before proceeding with work outside it.

In London and South East, a warranty engineer visit is offered within 60 hours of a claim being accepted. We will contact you to discuss access and offer an appointment. Please tell us about any arrangements that could affect the visit, including building entry requirements, parking restrictions or assistance you need when communicating with us.

The appointment offer is separate from confirmation that the repair can be completed at that visit. The engineer may need to inspect the fault before deciding what work is required. We will explain whether the proposed visit is for assessment, repair or work that depends on suitable parts being available.

Parts for warranty repairs in London and South East arrive within 60 working days. Our support team will explain which parts are needed and how their delivery affects the repair arrangements. A parts delivery does not itself confirm an engineer appointment. We will contact you to arrange fitting where this is required.

Please make sure the engineer can reach the appliance safely and has suitable space to work. Clear personal belongings from the surrounding area where you can safely do

[P4] Warranty
warranty terms that apply to your purchase. Acceptance means we have confirmed that your claim qualifies for the warranty repair service, based on the information available. If an inspection reveals a different cause, we will explain what this means for your cover before proceeding with work outside it.

In London and South East, a warranty engineer visit is offered within 60 hours of a claim being accepted. We will contact you to discuss access and offer an appointment. Please tell us about any arrangements that could affect the visit, including building entry requirements, parking restrictions or assistance you need when communicating with us.

The appointment offer is separate from confirmation that the repair can be completed at that visit. The engineer may need to inspect the fault before deciding what work is required. We will explain whether the proposed visit is for assessment, repair or work that depends on suitable parts being available.

Parts for warranty repairs in London and South East arrive within 60 working days. Our support team will explain which parts are needed and how their delivery affects the repair arrangements. A parts delivery does not itself confirm an engineer appointment. We will contact you to arrange fitting where this is required.

Please make sure the engineer can reach the appliance safely and has suitable space to work. Clear personal belongings from the surrounding area where you can safely do

[P5] Warranty
that cannot be reached by a service vehicle.

If travel disruption affects an agreed appointment, we will explain the situation and contact you to arrange a replacement appointment. You do not need to submit a fresh claim because an engineer cannot travel. Your accepted claim will remain with our service team.

Parts for warranty repairs in Island Areas arrive within 59 working days.

We will explain which parts are needed after the fault has been assessed. Where a part must be sent to an authorised service partner rather than directly to your address, we will make that arrangement and tell you how the repair will proceed.

Please do not order parts or arrange an independent repair on our behalf unless we have agreed this with you. We cannot promise to cover work that we have not authorised. If you are unsure whether an arrangement has been approved, contact customer care.

Before the engineer attends, please make the appliance accessible and clear the surrounding area. Tell us if moving it requires specialist assistance or if its installation makes access difficult. Do not attempt to move something that could cause injury or damage your home.

An adult who can explain the fault and authorise access must be present for the visit. Please ensure that pets are kept away from the work area and tell the engineer about a hazard that could affect safe working.

If you need

System's answer:
For postcode area HS (Island Areas), parts for warranty repairs arrive within **59 working days**. They may be sent to an authorised service partner rather than directly to your home; the support team will explain the arrangements. [P5]

---

## 28. DISTRACT-028

Question: How much does it cost to have the Vale fridge freezer picked up if I return it?

Can the question be answered from the documents: yes

Reference answer: Collection of a returned Vale fridge freezer costs £84.00.

Passages given to the system:
[P1] Returns and refunds
contact Halvard Home for advice. Do not assume that damage to the outer box means the appliance itself is damaged.

If you have already disposed of the original packaging, tell us before arranging a return. Do not pack the Vale fridge freezer in an unsuitable substitute or send it without protection. We will discuss how it can be collected safely. Missing packaging does not, by itself, remove your statutory rights.

Handle the Vale fridge freezer carefully while deciding whether it is suitable for your home. You may inspect it as you would reasonably inspect an appliance in a shop. Avoid removing protective materials unnecessarily, and take care not to scratch the finish, damage the fittings or mark the interior.

If you are returning it because you have changed your mind, tell us whether it has been installed, connected or used. Describe its condition honestly, including marks or damage. Use does not automatically prevent a return, but handling beyond what is needed to inspect it may affect your refund where the law allows.

If you believe the Vale fridge freezer is faulty, describe the problem rather than trying to repair it. Do not remove panels, alter wiring or dismantle fittings that are not intended to be removed by the customer. Contact us for guidance if the fault makes disconnecting, moving or packing it unsafe.

Before preparing an

[P2] Returns and refunds
contact Halvard Home for advice. Do not assume that damage to the outer box means the appliance itself is damaged.

If you have already disposed of the original packaging, tell us before arranging a return. Do not pack the Vale fridge freezer in an unsuitable substitute or send it without protection. We will discuss how it can be collected safely. Missing packaging does not, by itself, remove your statutory rights.

Handle the Vale fridge freezer carefully while deciding whether it is suitable for your home. You may inspect it as you would reasonably inspect an appliance in a shop. Avoid removing protective materials unnecessarily, and take care not to scratch the finish, damage the fittings or mark the interior.

If you are returning it because you have changed your mind, tell us whether it has been installed, connected or used. Describe its condition honestly, including marks or damage. Use does not automatically prevent a return, but handling beyond what is needed to inspect it may affect your refund where the law allows.

If you believe the Vale fridge freezer is faulty, describe the problem rather than trying to repair it. Do not remove panels, alter wiring or dismantle fittings that are not intended to be removed by the customer. Contact us for guidance if the fault makes disconnecting, moving or packing it unsafe.

Before preparing an

[P3] Returns and refunds
unsuitable packaging, we will explain what we found and consider the circumstances, including any packing advice we gave you. We will not automatically refuse a return because the carton is marked or opened. Any decision about charges or a reduced refund will respect your statutory rights.

## Vale fridge freezer

### Returning the appliance

If you would like to return your Vale fridge freezer, please contact Halvard Home customer support before arranging transport or disconnecting the appliance. Tell us why you want to return it and whether you would prefer a refund or an exchange. We will explain the return route that applies to your circumstances.

Please have your proof of purchase available when you contact us. This could be your order confirmation, receipt or another record showing that you bought the appliance from us. We may also ask for photographs if you are reporting damage or a fault.

If you bought your appliance from another retailer, contact that retailer about its returns process. Your rights against the seller are not affected by this policy. We can still help with questions about using the appliance or identifying a possible fault.

Our voluntary change of mind service is separate from your legal rights. Eligibility depends on the condition of the appliance and how it has been handled. Please describe any use, installation, damage or missing packaging so that we

[P4] Returns and refunds
unsuitable packaging, we will explain what we found and consider the circumstances, including any packing advice we gave you. We will not automatically refuse a return because the carton is marked or opened. Any decision about charges or a reduced refund will respect your statutory rights.

## Vale fridge freezer

### Returning the appliance

If you would like to return your Vale fridge freezer, please contact Halvard Home customer support before arranging transport or disconnecting the appliance. Tell us why you want to return it and whether you would prefer a refund or an exchange. We will explain the return route that applies to your circumstances.

Please have your proof of purchase available when you contact us. This could be your order confirmation, receipt or another record showing that you bought the appliance from us. We may also ask for photographs if you are reporting damage or a fault.

If you bought your appliance from another retailer, contact that retailer about its returns process. Your rights against the seller are not affected by this policy. We can still help with questions about using the appliance or identifying a possible fault.

Our voluntary change of mind service is separate from your legal rights. Eligibility depends on the condition of the appliance and how it has been handled. Please describe any use, installation, damage or missing packaging so that we

[P5] Returns and refunds
can explain what we can offer.

The following restocking charge applies to returns accepted under our voluntary change of mind service, rather than returns made under your statutory rights. A restocking charge of 6% of the price applies once the packaging is opened. We will explain any proposed deduction before you agree to proceed.

Collection of a returned Vale fridge freezer costs £84.00. This is our standard collection charge for an eligible change of mind return. It does not apply where we are responsible for collection because the appliance is faulty, damaged on arrival or not as described.

If you are exercising a legal cancellation right, we will explain the applicable return arrangements and any return costs you must bear. The voluntary restocking charge does not apply to statutory cancellations. Any deduction for handling will be limited to what the law allows.

An exchange for a Vale fridge freezer in a different colour must be requested within 13 days. For this voluntary exchange service, the request period runs from delivery. Availability depends on stock, and we will confirm whether your preferred colour is available before making arrangements.

That colour exchange condition does not limit your rights if we delivered the wrong colour or the appliance does not match its description. Tell us about the issue so that we can arrange an appropriate remedy without treating it as

System's answer:
The standard collection charge is **£84.00** for an eligible change-of-mind return. It does not apply if Halvard Home is responsible for collection because the fridge freezer is faulty, damaged on arrival, or not as described. [P5]

---

## 29. TOPIC-015

Question: How often does the Halvard water softener need maintenance?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Descaling your Keel washing machine
Descaling your Keel washing machine

Limescale can build up inside your Halvard Home Keel washing machine, especially in hard water areas. Use a descaler labelled as suitable for washing machines, and follow its instructions for the amount and treatment frequency.

1. Remove all laundry before descaling.
2. Add the descaler where its label directs. Do not add detergent or fabric conditioner.
3. Run the empty machine on the cycle and temperature specified by the descaler instructions, provided these are permitted in your machine’s care guide.
4. Once the cycle finishes, wipe the door seal with a damp cloth.

Never mix descaler with bleach or other cleaning products. If deposits remain, check the descaler instructions before repeating the treatment.

[P2] Servicing and engineer visits
After the repair, the engineer will check the work and explain what has been done. Testing may require access to water, drainage and electricity. If safe testing is not possible, we will explain the limitation and tell you whether the machine should remain unused.

We will provide a record of the repair and explain any care advice relevant to the fault. Contact us if the symptoms return or you believe the repair has not resolved the problem. Keep the repair record available so we can review the work and advise on the appropriate next step.

## Ashby tumble dryer

### Servicing schedule

Routine servicing helps keep your Ashby tumble dryer working as intended and gives an engineer the opportunity to identify wear, damage or faults that may need attention. Follow the servicing schedule recorded for your appliance, alongside the care instructions supplied with it. A service does not replace the cleaning and checks you are asked to carry out yourself.

Your service due date is recorded when your appliance is registered with Halvard Home. You can check this date through your customer account or ask our customer care team to confirm it. If you cannot find a servicing record, contact us rather than guessing whether your appliance is due for attention.

Owners of the Ashby tumble dryer are reminded when a service is due. A reminder is sent 3

[P3] Servicing and engineer visits
After the repair, the engineer will check the work and explain what has been done. Testing may require access to water, drainage and electricity. If safe testing is not possible, we will explain the limitation and tell you whether the machine should remain unused.

We will provide a record of the repair and explain any care advice relevant to the fault. Contact us if the symptoms return or you believe the repair has not resolved the problem. Keep the repair record available so we can review the work and advise on the appropriate next step.

## Ashby tumble dryer

### Servicing schedule

Routine servicing helps keep your Ashby tumble dryer working as intended and gives an engineer the opportunity to identify wear, damage or faults that may need attention. Follow the servicing schedule recorded for your appliance, alongside the care instructions supplied with it. A service does not replace the cleaning and checks you are asked to carry out yourself.

Your service due date is recorded when your appliance is registered with Halvard Home. You can check this date through your customer account or ask our customer care team to confirm it. If you cannot find a servicing record, contact us rather than guessing whether your appliance is due for attention.

Owners of the Ashby tumble dryer are reminded when a service is due. A reminder is sent 3

[P4] Servicing and engineer visits
. This schedule is intended to help keep your appliance working safely and reliably. Arrange servicing through Halvard Home or an appropriately qualified appliance engineer, and keep a record of the work carried out so that it is available when you need advice or repairs.

Use the installation date as the starting point for your servicing schedule. After a routine service, use the date recorded by the engineer to plan your next appointment. If you do not know when your appliance was installed or last serviced, contact us for help reviewing the information available.

The recommended schedule does not replace the care and cleaning instructions supplied with your appliance. Continue to follow those instructions, including guidance on cleaning accessible parts and checking for visible damage. Do not remove protective panels, alter electrical connections or attempt work that the instructions reserve for a qualified engineer.

Arrange an assessment if the appliance develops an unusual noise, an unexpected smell, a leak or a change in washing performance. Do not wait for the scheduled service if you think something is wrong. A fault assessment may involve different work from a routine service, and we will explain the appropriate booking arrangements.

If you notice smoke, a burning smell or signs of an electrical fault, stop using the appliance. Disconnect it from the electricity supply only if you can do so safely. If water is leaking,

[P5] Servicing and engineer visits
. This schedule is intended to help keep your appliance working safely and reliably. Arrange servicing through Halvard Home or an appropriately qualified appliance engineer, and keep a record of the work carried out so that it is available when you need advice or repairs.

Use the installation date as the starting point for your servicing schedule. After a routine service, use the date recorded by the engineer to plan your next appointment. If you do not know when your appliance was installed or last serviced, contact us for help reviewing the information available.

The recommended schedule does not replace the care and cleaning instructions supplied with your appliance. Continue to follow those instructions, including guidance on cleaning accessible parts and checking for visible damage. Do not remove protective panels, alter electrical connections or attempt work that the instructions reserve for a qualified engineer.

Arrange an assessment if the appliance develops an unusual noise, an unexpected smell, a leak or a change in washing performance. Do not wait for the scheduled service if you think something is wrong. A fault assessment may involve different work from a routine service, and we will explain the appropriate booking arrangements.

If you notice smoke, a burning smell or signs of an electrical fault, stop using the appliance. Disconnect it from the electricity supply only if you can do so safely. If water is leaking,

System's answer:
The passages do not specify how often a Halvard water softener needs maintenance. Check its care instructions or contact Halvard Home to confirm the maintenance schedule.

---

## 30. TWOPART-000

Question: How soon will Halvard Home offer a warranty engineer visit in North of England after accepting my claim, and how soon will you tell me about a recall after it is issued?

Can the question be answered from the documents: yes

Reference answer: In North of England, a warranty engineer visit is offered within 92 hours of a claim being accepted. Customers are told of a recall within 25 days of it being issued.

Passages given to the system:
[P1] Warranty
.

After the repair, the engineer will explain the work carried out and any advice relevant to safe use. Tell us if the original fault remains or returns. Keep your repair confirmation with your purchase records, as this helps us identify the work already authorised and assess any related concern.

If a covered repair cannot be completed, we will explain the available remedy under your warranty and applicable consumer law. You can ask customer care to review a decision or raise a complaint if you are unhappy with the handling of your claim. This warranty does not limit your statutory rights, including any rights you may have against the retailer.

## North of England

### Warranty repairs in this region

If you live in the North of England, contact Halvard Home customer support to request a warranty repair. Tell us what has happened and describe any warning signs, unusual behaviour or visible damage. We will explain what information we need to assess your claim.

We may ask for proof of purchase, details of the appliance and the address where it is installed. If you cannot find the documents we request, tell us. We will explain whether other evidence can help us confirm your warranty cover.

Please give us accurate contact details and let us know about anything that could affect access to your home. This might include parking restrictions, shared entrances

[P2] Warranty
.

After the repair, the engineer will explain the work carried out and any advice relevant to safe use. Tell us if the original fault remains or returns. Keep your repair confirmation with your purchase records, as this helps us identify the work already authorised and assess any related concern.

If a covered repair cannot be completed, we will explain the available remedy under your warranty and applicable consumer law. You can ask customer care to review a decision or raise a complaint if you are unhappy with the handling of your claim. This warranty does not limit your statutory rights, including any rights you may have against the retailer.

## North of England

### Warranty repairs in this region

If you live in the North of England, contact Halvard Home customer support to request a warranty repair. Tell us what has happened and describe any warning signs, unusual behaviour or visible damage. We will explain what information we need to assess your claim.

We may ask for proof of purchase, details of the appliance and the address where it is installed. If you cannot find the documents we request, tell us. We will explain whether other evidence can help us confirm your warranty cover.

Please give us accurate contact details and let us know about anything that could affect access to your home. This might include parking restrictions, shared entrances

[P3] Warranty
We will not ask you to agree to an alternative without explaining what it means for you.

If you are unhappy with the handling of your claim, contact customer care and ask for a review. Explain what you believe has gone wrong and the outcome you are seeking. We will consider the claim records and respond with our findings and proposed action.

Your Halvard Home warranty is separate from your statutory rights. Nothing in these repair arrangements limits the rights or remedies available to you under applicable consumer law, including rights you may have against the retailer. You may seek independent consumer advice if you are unsure about your options.

## London and South East

### Warranty repairs in this region

Warranty repairs in London and South East are arranged through Halvard Home or an authorised repair partner. This section explains how we assess your claim, arrange access and carry out a covered repair. Please contact our support team before arranging work yourself, so we can confirm whether the fault falls within your warranty.

When you contact us, describe the fault and explain what happens when you try to use the appliance. We may ask for proof of purchase, photographs or information from its identification label. Please share only the information needed to assess your claim. Our team will explain how to send it securely.

We assess your claim against the

[P4] Warranty
We will not ask you to agree to an alternative without explaining what it means for you.

If you are unhappy with the handling of your claim, contact customer care and ask for a review. Explain what you believe has gone wrong and the outcome you are seeking. We will consider the claim records and respond with our findings and proposed action.

Your Halvard Home warranty is separate from your statutory rights. Nothing in these repair arrangements limits the rights or remedies available to you under applicable consumer law, including rights you may have against the retailer. You may seek independent consumer advice if you are unsure about your options.

## London and South East

### Warranty repairs in this region

Warranty repairs in London and South East are arranged through Halvard Home or an authorised repair partner. This section explains how we assess your claim, arrange access and carry out a covered repair. Please contact our support team before arranging work yourself, so we can confirm whether the fault falls within your warranty.

When you contact us, describe the fault and explain what happens when you try to use the appliance. We may ask for proof of purchase, photographs or information from its identification label. Please share only the information needed to assess your claim. Our team will explain how to send it securely.

We assess your claim against the

[P5] Warranty
your claim. Updates may come from Halvard Home or the authorised repair partner handling the work. Please keep your contact details accurate and let us know your preferred contact method. Tell us if you need information in an accessible format.

After carrying out the repair, the engineer will check the work and explain any guidance relevant to using the appliance safely. Please raise any concerns about the repair with our support team. Describe what you have noticed and refer to your existing claim so we can review the repair record.

If a covered repair cannot be completed, we will explain the reason and discuss the options available under your warranty and applicable law. The outcome depends on the circumstances of your claim. We will not ask you to accept an alternative without explaining what it means for you.

If you are unhappy with how your claim has been handled, contact our support team and ask for a review. We will explain our complaints process and how to raise your concerns. Your warranty is separate from your statutory rights, which remain unaffected by this policy or by a repair arranged under it.

## Northern Ireland

### Warranty repairs in this region

Warranty repairs in Northern Ireland are arranged through our customer support team and carried out by an authorised engineer. Please contact us if you believe your appliance has developed a fault covered by its

System's answer:
The provided passages do not specify how soon Halvard Home will offer an engineer visit in the North of England after accepting your claim, or how soon it will notify you after a recall is issued.

Contact Halvard Home customer support to confirm both timeframes. The North of England guidance directs warranty repair requests to that team. [P1]

---

## 31. VERSION-036

Question: How much would I pay to find out what’s wrong with my Keel washing machine if I don’t go ahead with a repair?

Can the question be answered from the documents: yes

Reference answer: Diagnosing a fault on the Keel washing machine costs £38.00 if no repair follows.

Passages given to the system:
[P1] Servicing and engineer visits
.

Diagnosing a fault on the Keel washing machine costs £23.00 if no repair follows. We will explain whether this charge applies when you book, including where you choose not to proceed with a quoted repair. Any applicable warranty rights or statutory rights remain unaffected.

The engineer will explain the proposed repair and provide a quote before starting chargeable work. The quote will identify the work and parts included. We will ask for your agreement if the findings change what is needed. You may decline the revised work.

Drainage problems may be caused by trapped objects, a blocked filter or a faulty pump. The engineer will check the likely cause rather than replace the pump without inspection. Removing an obstruction may resolve the fault, although damage caused by the obstruction may also need repair.

Replace the filter every 25 weeks. Use a compatible replacement and follow the user guide for safe access and fitting. Switch off and unplug the machine before opening the filter cover. Take care when releasing trapped water, which may be hot, and protect the surrounding floor.

Leaks may come from a damaged door seal, a loose connection or an internal component. The engineer will identify the source where it can be safely accessed. Repairs to household pipework, taps or drainage outside the machine are not included

[P2] Servicing and engineer visits
.

Diagnosing a fault on the Keel washing machine costs £38.00 if no repair follows. We will explain whether this charge applies when you book, including where you choose not to proceed with a quoted repair. Any applicable warranty rights or statutory rights remain unaffected.

The engineer will explain the proposed repair and provide a quote before starting chargeable work. The quote will identify the work and parts included. We will ask for your agreement if the findings change what is needed. You may decline the revised work.

Drainage problems may be caused by trapped objects, a blocked filter or a faulty pump. The engineer will check the likely cause rather than replace the pump without inspection. Removing an obstruction may resolve the fault, although damage caused by the obstruction may also need repair.

Replace the filter every 25 weeks. Use a compatible replacement and follow the user guide for safe access and fitting. Switch off and unplug the machine before opening the filter cover. Take care when releasing trapped water, which may be hot, and protect the surrounding floor.

Leaks may come from a damaged door seal, a loose connection or an internal component. The engineer will identify the source where it can be safely accessed. Repairs to household pipework, taps or drainage outside the machine are not included

[P3] Warranty
check clearly. If you cannot carry it out safely, let us know so we can arrange suitable help.

A warranty repair to the Keel washing machine is completed within 24 working days of the fault being confirmed. We will tell you when the fault has been confirmed and explain what the repair involves. We will also tell you how to contact us for an update.

Where the fault is covered, Halvard Home pays for the work and parts needed to put it right, including the engineer’s visit. We will not ask you to pay for covered repair work. If our assessment finds something outside the warranty, we will explain the reason before asking you to approve any chargeable work.

An engineer visit for the Keel washing machine after the warranty has ended costs £61.00. This charge is for the visit, rather than an agreement to carry out whatever repair may be needed. We will explain any proposed repair charges and ask for your agreement before proceeding.

We will agree access arrangements with you when booking a repair. Please make sure the engineer can reach the machine safely and can access its water and electricity connections. Tell us about restricted access, stairs or any other conditions that could affect the work.

Please empty the drum and remove belongings from around the machine before the engineer attends. Keep

[P4] Warranty
check clearly. If you cannot carry it out safely, let us know so we can arrange suitable help.

A warranty repair to the Keel washing machine is completed within 24 working days of the fault being confirmed. We will tell you when the fault has been confirmed and explain what the repair involves. We will also tell you how to contact us for an update.

Where the fault is covered, Halvard Home pays for the work and parts needed to put it right, including the engineer’s visit. We will not ask you to pay for covered repair work. If our assessment finds something outside the warranty, we will explain the reason before asking you to approve any chargeable work.

An engineer visit for the Keel washing machine after the warranty has ended costs £119.00. This charge is for the visit, rather than an agreement to carry out whatever repair may be needed. We will explain any proposed repair charges and ask for your agreement before proceeding.

We will agree access arrangements with you when booking a repair. Please make sure the engineer can reach the machine safely and can access its water and electricity connections. Tell us about restricted access, stairs or any other conditions that could affect the work.

Please empty the drum and remove belongings from around the machine before the engineer attends. Keep

[P5] Servicing and engineer visits
close the appliance’s water supply valve if it is safe and accessible, and contact us for advice.

A routine service of the Keel washing machine takes about 122 minutes. This is an estimate of the engineer’s working time, rather than a guaranteed appointment length. Access difficulties, the condition of the appliance or faults discovered during the visit may affect how the appointment proceeds. The engineer will explain any change to the planned work.

A routine service of the Keel washing machine costs £168.00. This price covers the routine service work described when you book. Repairs, replacement parts and work outside that scope require your agreement. If the engineer recommends additional work, we will explain what is needed and confirm the price before you decide whether to proceed.

When booking, tell us about any faults, warning messages or recent changes in performance. Mention any previous repairs or alterations that may be relevant. This helps us arrange suitable support and distinguish routine servicing from a repair visit. Have your appliance details and any available service records ready when you contact us.

Please also tell us about access restrictions, parking arrangements or anything that could affect the engineer’s ability to work safely. Let us know if the appliance is fitted into cabinetry or located where moving it may be difficult. We will discuss any preparation

System's answer:
The passages give two different diagnostic charges if no repair follows: **£23.00 in P1** and **£38.00 in P2**. The applicable charge will be explained when you book, including if you decline a quoted repair.

---

## 32. POL-TWO-019

Question: How long should I keep the box my Vale fridge freezer came in in case I need to send it back?

Can the question be answered from the documents: yes

Reference answer: Keep the original packaging of the Vale fridge freezer for 18 days in case it needs to be returned.

Passages given to the system:
[P1] Returns and refunds
contact Halvard Home for advice. Do not assume that damage to the outer box means the appliance itself is damaged.

If you have already disposed of the original packaging, tell us before arranging a return. Do not pack the Vale fridge freezer in an unsuitable substitute or send it without protection. We will discuss how it can be collected safely. Missing packaging does not, by itself, remove your statutory rights.

Handle the Vale fridge freezer carefully while deciding whether it is suitable for your home. You may inspect it as you would reasonably inspect an appliance in a shop. Avoid removing protective materials unnecessarily, and take care not to scratch the finish, damage the fittings or mark the interior.

If you are returning it because you have changed your mind, tell us whether it has been installed, connected or used. Describe its condition honestly, including marks or damage. Use does not automatically prevent a return, but handling beyond what is needed to inspect it may affect your refund where the law allows.

If you believe the Vale fridge freezer is faulty, describe the problem rather than trying to repair it. Do not remove panels, alter wiring or dismantle fittings that are not intended to be removed by the customer. Contact us for guidance if the fault makes disconnecting, moving or packing it unsafe.

Before preparing an

[P2] Returns and refunds
contact Halvard Home for advice. Do not assume that damage to the outer box means the appliance itself is damaged.

If you have already disposed of the original packaging, tell us before arranging a return. Do not pack the Vale fridge freezer in an unsuitable substitute or send it without protection. We will discuss how it can be collected safely. Missing packaging does not, by itself, remove your statutory rights.

Handle the Vale fridge freezer carefully while deciding whether it is suitable for your home. You may inspect it as you would reasonably inspect an appliance in a shop. Avoid removing protective materials unnecessarily, and take care not to scratch the finish, damage the fittings or mark the interior.

If you are returning it because you have changed your mind, tell us whether it has been installed, connected or used. Describe its condition honestly, including marks or damage. Use does not automatically prevent a return, but handling beyond what is needed to inspect it may affect your refund where the law allows.

If you believe the Vale fridge freezer is faulty, describe the problem rather than trying to repair it. Do not remove panels, alter wiring or dismantle fittings that are not intended to be removed by the customer. Contact us for guidance if the fault makes disconnecting, moving or packing it unsafe.

Before preparing an

[P3] Returns and refunds
. Keep the collection route clear and make sure someone can provide access. Our collection team may decline to move the appliance if doing so would put people or property at risk.

We will inspect the returned appliance and confirm the outcome. If we believe a deduction is justified, we will explain the reason and how it has been calculated. You can ask us to review that decision and provide information about the appliance’s condition.

Approved refunds will normally go back to the original payment method, subject to applicable legal requirements. We will confirm when the refund has been processed. Nothing in this section excludes or reduces your statutory rights, including any right to reject goods or receive a repair, replacement or refund.

### Packaging and condition

The Vale fridge freezer travels safely only in its original box. Keep the original packaging for 18 days in case it needs to be returned.

Keep the protective inserts, corner supports and other packing materials with the box. Store them somewhere dry and away from anything that could crush, tear or stain them. Open the packaging carefully so that it can be used again without leaving the appliance exposed during handling or transport.

If the box arrives torn, wet or visibly damaged, take photographs of the packaging and the Vale fridge freezer if it is safe to do so. Keep the damaged materials and

[P4] Returns and refunds
. Keep the collection route clear and make sure someone can provide access. Our collection team may decline to move the appliance if doing so would put people or property at risk.

We will inspect the returned appliance and confirm the outcome. If we believe a deduction is justified, we will explain the reason and how it has been calculated. You can ask us to review that decision and provide information about the appliance’s condition.

Approved refunds will normally go back to the original payment method, subject to applicable legal requirements. We will confirm when the refund has been processed. Nothing in this section excludes or reduces your statutory rights, including any right to reject goods or receive a repair, replacement or refund.

### Packaging and condition

The Vale fridge freezer travels safely only in its original box. Keep the original packaging for 18 days in case it needs to be returned.

Keep the protective inserts, corner supports and other packing materials with the box. Store them somewhere dry and away from anything that could crush, tear or stain them. Open the packaging carefully so that it can be used again without leaving the appliance exposed during handling or transport.

If the box arrives torn, wet or visibly damaged, take photographs of the packaging and the Vale fridge freezer if it is safe to do so. Keep the damaged materials and

[P5] Returns and refunds
unsuitable packaging, we will explain what we found and consider the circumstances, including any packing advice we gave you. We will not automatically refuse a return because the carton is marked or opened. Any decision about charges or a reduced refund will respect your statutory rights.

## Vale fridge freezer

### Returning the appliance

If you would like to return your Vale fridge freezer, please contact Halvard Home customer support before arranging transport or disconnecting the appliance. Tell us why you want to return it and whether you would prefer a refund or an exchange. We will explain the return route that applies to your circumstances.

Please have your proof of purchase available when you contact us. This could be your order confirmation, receipt or another record showing that you bought the appliance from us. We may also ask for photographs if you are reporting damage or a fault.

If you bought your appliance from another retailer, contact that retailer about its returns process. Your rights against the seller are not affected by this policy. We can still help with questions about using the appliance or identifying a possible fault.

Our voluntary change of mind service is separate from your legal rights. Eligibility depends on the condition of the appliance and how it has been handled. Please describe any use, installation, damage or missing packaging so that we

System's answer:
Keep the original box and packing materials for **18 days** in case you need to return your Vale fridge freezer.

---

## 33. ABSENT-018

Question: What is the maximum angle I can tilt the Vale fridge freezer when carrying it?

Can the question be answered from the documents: no

Reference answer: The documents do not say.

Passages given to the system:
[P1] Moving your Vale fridge freezer
Moving your Vale fridge freezer

Keep your Vale fridge freezer upright during transport and use two people to move it safely.

Before moving, unplug the appliance, remove all food and take out loose shelves and drawers. Allow any ice to melt naturally, then dry the inside thoroughly. Do not use sharp tools to remove ice.

Secure the doors with a strap or removable tape, and protect the cabinet with blankets. Keep the power cable off the floor. Never lift the appliance by its doors or handles.

At its destination, place the fridge freezer on a firm, level floor with space around it for ventilation. Leave it standing upright for at least 24 hours before plugging it in. Let it cool fully before replacing food.

[P2] Safety and recalls
with the appliance and keep them accessible. If this guidance differs from a safety notice issued for your appliance, follow the safety notice and contact Halvard Home for advice.

Choose a firm, level surface where the appliance can stand securely. Keep it away from direct sunlight, cooking appliances and sources of heat or moisture. Do not install it where rain, splashes or standing water could reach the appliance or its electrical connection.

Leave at least 8 centimetres of space around the Vale fridge freezer. Keep the ventilation openings clear of packaging, furniture and stored belongings. Do not enclose the appliance in cabinetry unless the installation instructions expressly permit this arrangement.

Ask a suitably qualified installer to check the location and electrical connection if you are unsure whether they are suitable. The plug must remain accessible without moving the appliance dangerously. Do not place the power cable where it could be trapped, stretched, cut or exposed to heat.

Connect the appliance directly to a suitable earthed wall socket. Do not use an extension lead, adaptor or portable socket arrangement. Never remove the earth connection or alter the plug. A damaged plug, cable or socket must be assessed by a qualified professional before use.

Move the appliance with suitable assistance and handling equipment. Do not lift it by the doors, handles or pip

[P3] Safety and recalls
with the appliance and keep them accessible. If this guidance differs from a safety notice issued for your appliance, follow the safety notice and contact Halvard Home for advice.

Choose a firm, level surface where the appliance can stand securely. Keep it away from direct sunlight, cooking appliances and sources of heat or moisture. Do not install it where rain, splashes or standing water could reach the appliance or its electrical connection.

Leave at least 8 centimetres of space around the Vale fridge freezer. Keep the ventilation openings clear of packaging, furniture and stored belongings. Do not enclose the appliance in cabinetry unless the installation instructions expressly permit this arrangement.

Ask a suitably qualified installer to check the location and electrical connection if you are unsure whether they are suitable. The plug must remain accessible without moving the appliance dangerously. Do not place the power cable where it could be trapped, stretched, cut or exposed to heat.

Connect the appliance directly to a suitable earthed wall socket. Do not use an extension lead, adaptor or portable socket arrangement. Never remove the earth connection or alter the plug. A damaged plug, cable or socket must be assessed by a qualified professional before use.

Move the appliance with suitable assistance and handling equipment. Do not lift it by the doors, handles or pip

[P4] Safety and recalls
hoses or fittings.

Plan a clear route to the intended location. Check that doors can open freely and that the route is free from trailing leads, loose rugs and other obstacles. Protect the floor without creating a slippery surface or making the appliance unstable.

Do not attempt to lift or carry the appliance unaided. Use suitable handling equipment and seek help from people who can move it safely. Never use the door, control panel, power lead or attached fittings as lifting points.

Keep the appliance upright during handling and transport, following the supplied moving instructions. Secure the door and protect loose connections without damaging them. If safe handling is not possible, stop and arrange assistance from a competent installer or removal service.

After moving the Ashby tumble dryer, wait 38 hours before switching it on. Keep it disconnected while it settles, and prevent anyone from switching it on inadvertently.

Before reconnecting it, inspect the lead, plug, casing and connections for damage caused during the move. Confirm that it stands securely and that airflow is unobstructed. If anything appears damaged, displaced or unsafe, leave it disconnected and contact Halvard Home for advice.

## Vale fridge freezer

### Safe use

Use the Vale fridge freezer only for storing food and drink in a domestic setting. Follow the instructions supplied

[P5] Safety and recalls
hoses or fittings.

Plan a clear route to the intended location. Check that doors can open freely and that the route is free from trailing leads, loose rugs and other obstacles. Protect the floor without creating a slippery surface or making the appliance unstable.

Do not attempt to lift or carry the appliance unaided. Use suitable handling equipment and seek help from people who can move it safely. Never use the door, control panel, power lead or attached fittings as lifting points.

Keep the appliance upright during handling and transport, following the supplied moving instructions. Secure the door and protect loose connections without damaging them. If safe handling is not possible, stop and arrange assistance from a competent installer or removal service.

After moving the Ashby tumble dryer, wait 38 hours before switching it on. Keep it disconnected while it settles, and prevent anyone from switching it on inadvertently.

Before reconnecting it, inspect the lead, plug, casing and connections for damage caused during the move. Confirm that it stands securely and that airflow is unobstructed. If anything appears damaged, displaced or unsafe, leave it disconnected and contact Halvard Home for advice.

## Vale fridge freezer

### Safe use

Use the Vale fridge freezer only for storing food and drink in a domestic setting. Follow the instructions supplied

System's answer:
The passages do not specify a maximum tilt angle. They say to **keep the Vale fridge freezer upright during handling and transport** and use two people to move it safely. Do not lift it by its doors or handles. [P1]

If you cannot move it upright safely, contact Halvard Home or a competent removal service for advice.

---

## 34. POL-HEAD-013

Question: How much do you charge if I return the Orrin heat pump without cleaning it?

Can the question be answered from the documents: yes

Reference answer: A returned Orrin heat pump that needs cleaning is charged £17.00.

Passages given to the system:
[P1] Returns and refunds
83% of the price. Check the contents carefully and tell us about anything you cannot return. This deduction applies to eligible change of mind returns and does not override any statutory remedy you have for faulty or misdescribed goods.

A return that needs cleaning is charged £17.00. Remove ordinary surface dirt using the cleaning method described in the care instructions. Do not use abrasive materials, harsh chemicals or excessive moisture. These can damage finishes or components and may make the appliance unsafe to handle or transport.

Tell us if the appliance has been exposed to smoke, grease, pests, mould or other contamination. Do not conceal contamination beneath wrapping or attempt cleaning that could put you at risk. We may need to agree specialist handling arrangements rather than use the usual return process.

A returned Orrin heat pump is inspected within 5 days of arrival. We check its condition, the supplied contents and any signs of damage or contamination. We also consider the reason for return and any information you have given us about its delivery, installation, handling or use.

Photographs of the appliance and its packed condition can help if there is a question about damage during transport. Keep any relevant delivery records and tell us about marks, dents or damaged packaging you noticed on receipt. You do not need to hide

[P2] Returns and refunds
83% of the price. Check the contents carefully and tell us about anything you cannot return. This deduction applies to eligible change of mind returns and does not override any statutory remedy you have for faulty or misdescribed goods.

A return that needs cleaning is charged £17.00. Remove ordinary surface dirt using the cleaning method described in the care instructions. Do not use abrasive materials, harsh chemicals or excessive moisture. These can damage finishes or components and may make the appliance unsafe to handle or transport.

Tell us if the appliance has been exposed to smoke, grease, pests, mould or other contamination. Do not conceal contamination beneath wrapping or attempt cleaning that could put you at risk. We may need to agree specialist handling arrangements rather than use the usual return process.

A returned Orrin heat pump is inspected within 29 days of arrival. We check its condition, the supplied contents and any signs of damage or contamination. We also consider the reason for return and any information you have given us about its delivery, installation, handling or use.

Photographs of the appliance and its packed condition can help if there is a question about damage during transport. Keep any relevant delivery records and tell us about marks, dents or damaged packaging you noticed on receipt. You do not need to hide

[P3] Safety and recalls
assessment by a qualified professional rather than attempting a temporary repair.

Do not use an extension lead or an adaptor to supply the Orrin heat pump. Do not modify its wiring, bypass protective devices or interfere with the electrical isolator. Electrical work must be carried out by a qualified electrician.

Before cleaning, switch the appliance off and isolate its electrical supply using the method explained by your installer. Do not rely on a remote control, an app or a standby setting to prevent it from starting.

Let the Orrin heat pump cool for 33 minutes before cleaning it. Keep away from surfaces that remain hot and do not begin cleaning while there is a risk of burns. If safe access is uncertain, ask a qualified professional to help.

Clean the air vents every 118 days. Follow the supplied cleaning instructions and remove accessible surface debris without pushing it into the appliance. Do not remove protective guards or reach inside the casing to clean internal components.

Use the cleaning method described in the instructions. Do not direct a hose or pressure washer at the appliance, and do not apply solvents or abrasive cleaners. Stop if cleaning exposes damage or reveals a loose component.

Have the Orrin heat pump safety-checked every 25 months. Arrange this through Halvard Home or a suitably qualified service provider.

[P4] Safety and recalls
assessment by a qualified professional rather than attempting a temporary repair.

Do not use an extension lead or an adaptor to supply the Orrin heat pump. Do not modify its wiring, bypass protective devices or interfere with the electrical isolator. Electrical work must be carried out by a qualified electrician.

Before cleaning, switch the appliance off and isolate its electrical supply using the method explained by your installer. Do not rely on a remote control, an app or a standby setting to prevent it from starting.

Let the Orrin heat pump cool for 33 minutes before cleaning it. Keep away from surfaces that remain hot and do not begin cleaning while there is a risk of burns. If safe access is uncertain, ask a qualified professional to help.

Clean the air vents every 118 days. Follow the supplied cleaning instructions and remove accessible surface debris without pushing it into the appliance. Do not remove protective guards or reach inside the casing to clean internal components.

Use the cleaning method described in the instructions. Do not direct a hose or pressure washer at the appliance, and do not apply solvents or abrasive cleaners. Stop if cleaning exposes damage or reveals a loose component.

Have the Orrin heat pump safety-checked every 25 months. Arrange this through Halvard Home or a suitably qualified service provider.

[P5] Returns and refunds
explain the problem when you contact us. Photographs can help us understand visible damage, but do not dismantle the appliance or attempt repairs to gather evidence.

Returns because you have changed your mind are handled differently from returns involving a fault, damage or an incorrect description. We will explain which process applies to your request. Nothing in this policy limits your statutory rights.

For an accepted change of mind return, the following condition applies. A restocking charge of 13% of the price applies once the packaging is opened. This charge does not apply where applying it would conflict with your statutory rights.

Collection of a returned Orrin heat pump costs £93.00. This is the collection charge for an accepted change of mind return. Where we are legally responsible for return costs, we will arrange an appropriate return method without charging you.

A returns label for the Orrin heat pump is emailed within 22 hours of the request. Check that the email address you provide is correct and look in your junk folder if the message has not arrived.

The label identifies your return; it does not confirm a collection booking. Follow the instructions included with it and contact customer support if you cannot print it. Do not send the appliance to an address found elsewhere.

Keep the appliance safe while your return is being arranged

System's answer:
If the returned Orrin heat pump needs cleaning, the charge is **£17.00**.

---

## 35. SHARED-034

Question: How do I replace a damaged door seal on my Halvard Home Keel washing machine?

Can the question be answered from the documents: yes

Reference answer: Arrange fitting with a qualified repair technician.

Passages given to the system:
[P1] Replacing a Keel door seal
Replacing a Keel door seal

A damaged door seal can let water leak from the front of your Halvard Home Keel washing machine. Check the rubber seal for splits, holes or areas that have pulled away from the door opening.

Before inspecting it, switch the machine off, unplug it and turn off the water supply. Do not use the machine if the seal is torn or leaking.

To request a replacement, contact Halvard Home support with your machine’s model details and a clear photo of the damage. Ask them to confirm that the replacement seal fits your machine before ordering.

Arrange fitting with a qualified repair technician. A poorly fitted seal can leak, even if the replacement itself is undamaged.

[P2] Keel washing machine door will not close
Keel washing machine door will not close

If your Keel washing machine door bounces back instead of clicking shut, the door latch may be stuck in its closed position.

Switch off the machine and unplug it before checking the door. Remove any clothing trapped between the door and the rubber seal, then wipe away visible fluff around the latch opening. Try closing the door gently once. Do not slam it or push tools into the latch.

KX-5546 is the replacement door latch assembly for the Keel washing machine. If the latch remains stuck and the door still will not close, leave the machine unplugged and contact Halvard Home support to arrange replacement by a qualified technician.

[P3] Booking a Keel engineer visit
Booking a Keel engineer visit

For the Halvard Home Keel washing machine, KX-3928 identifies the drain pump housing. A crack in this housing can cause water to leak beneath the machine during draining. Stop using the machine if you notice this fault.

Switch the machine off and close its water supply tap. Unplug it only if the plug and surrounding area are dry and safe to reach. Do not remove panels or attempt to seal the leak yourself.

Contact Halvard Home customer support to book an engineer visit. Have your machine’s serial number, address and preferred appointment dates ready. Describe where the water appears and mention the part reference above. The engineer will inspect the leak and confirm whether the housing needs replacing.

[P4] Keel washing machine warranty
Keel washing machine warranty

Your Halvard Home Keel washing machine has a two-year warranty from the delivery date, covering manufacturing faults during normal domestic use. Keep your receipt or order confirmation as proof of purchase.

KX-2446 is the part number for the drain pump fitted to your Keel washing machine. If a manufacturing defect causes the pump housing to crack and leak within the warranty period, Halvard Home will repair or replace the faulty pump free of charge.

Stop using the machine if you notice water leaking underneath it. Switch it off and unplug it only if the plug and surrounding area are dry.

Contact Halvard Home support with your purchase details and a description of the leak. Arrange a warranty assessment before attempting repairs yourself.

[P5] Keel washing machine: first installation
Keel washing machine: first installation

On your Halvard Home Keel washing machine, E-4020 means the drum is still restrained by one or more transport bolts left in place during installation. These bolts protect the drum during delivery but must be removed before use.

To fix this:

- Stop the programme, switch off the machine and unplug it.
- Check the rear of the machine and remove all transport bolts, following the installation guide.
- Fit the supplied plastic caps into the empty bolt holes.
- Keep the bolts for any future move.

Once the machine is level and its hoses are securely connected, plug it in and run an empty rinse and spin programme. If the warning returns, stop using the machine and contact Halvard Home support.

System's answer:
To replace a damaged door seal on your Halvard Home Keel washing machine:

1. **Make it safe:** Switch the machine off, unplug it and turn off the water supply. Do not use it if the seal is torn or leaking.
2. **Check the damage:** Look for splits, holes or sections of the rubber seal that have pulled away from the door opening.
3. **Request the replacement:** Contact Halvard Home support with your machine’s model details and a clear photo of the damage. Ask them to confirm that the replacement seal fits your model before ordering.
4. **Arrange professional fitting:** Have a qualified repair technician install the seal. A poorly fitted seal can leak even when the new seal is undamaged.

---

## 36. POL-TWO-014

Question: How long can I get my Ashby tumble dryer fixed without paying for the work?

Can the question be answered from the documents: yes

Reference answer: Labour for repairs to the Ashby tumble dryer is free for the first 30 months.

Passages given to the system:
[P1] Servicing and engineer visits
not bypass the door catch or interfere with safety switches. The engineer will check the affected components and confirm whether adjustment or replacement is needed to restore safe operation.

Spare parts for the Ashby tumble dryer are stocked for 13 years after the model is discontinued. Availability for a particular visit still depends on the part required and current stock. If a part must be ordered, we will explain the next steps and arrange further work with you.

If a repair is not practical, or the appliance cannot be made safe through the proposed work, the engineer will explain why. We will not present a repair as suitable when it would leave a known safety concern unresolved. You can decline the proposed repair after receiving the assessment.

Paid repairs to the Ashby tumble dryer come with their own guarantee. Repairs are guaranteed for 105 days. Keep your repair confirmation and contact us if the repaired fault returns. We will review the work recorded and explain how the repair guarantee applies. It does not affect your statutory rights.

After completing the work, the engineer will check the repaired function and explain any care advice relevant to the fault. Tell us if anything remains unclear before using the appliance. If the same symptoms return, stop using it where safety may be affected and contact Halvard Home for guidance.

## Vale

[P2] Servicing and engineer visits
not bypass the door catch or interfere with safety switches. The engineer will check the affected components and confirm whether adjustment or replacement is needed to restore safe operation.

Spare parts for the Ashby tumble dryer are stocked for 13 years after the model is discontinued. Availability for a particular visit still depends on the part required and current stock. If a part must be ordered, we will explain the next steps and arrange further work with you.

If a repair is not practical, or the appliance cannot be made safe through the proposed work, the engineer will explain why. We will not present a repair as suitable when it would leave a known safety concern unresolved. You can decline the proposed repair after receiving the assessment.

Paid repairs to the Ashby tumble dryer come with their own guarantee. Repairs are guaranteed for 105 days. Keep your repair confirmation and contact us if the repaired fault returns. We will review the work recorded and explain how the repair guarantee applies. It does not affect your statutory rights.

After completing the work, the engineer will check the repaired function and explain any care advice relevant to the fault. Tell us if anything remains unclear before using the appliance. If the same symptoms return, stop using it where safety may be affected and contact Halvard Home for guidance.

## Vale

[P3] Servicing and engineer visits
or emptying the water container, where fitted. Do not remove panels, reach inside the casing or attempt to repair electrical components yourself.

If you notice smoke, a burning smell, sparks or unusual heat, stop using the appliance. Disconnect it from the electricity supply if it is safe to do so, and do not use it again until it has been assessed. If there is an immediate danger, leave the area and contact the emergency services.

When you contact Halvard Home, describe what happens when you try to use the dryer. Tell us about unusual sounds, interrupted programmes, damp laundry or visible damage. Please also mention any previous repair affecting the fault. This helps us arrange appropriate support, although the engineer may still need to inspect the appliance.

Diagnosing a fault on the Ashby tumble dryer costs £41.00 if no repair follows. We will explain how this charge applies before you agree to a visit. If the fault may be covered by a guarantee or your legal rights, tell us when booking so that we can check the appropriate route.

The engineer will assess the fault and explain the proposed repair, including the parts and labour involved. You will be told the total repair price before work begins. We will not carry out chargeable repair work without your agreement. If

[P4] Servicing and engineer visits
or emptying the water container, where fitted. Do not remove panels, reach inside the casing or attempt to repair electrical components yourself.

If you notice smoke, a burning smell, sparks or unusual heat, stop using the appliance. Disconnect it from the electricity supply if it is safe to do so, and do not use it again until it has been assessed. If there is an immediate danger, leave the area and contact the emergency services.

When you contact Halvard Home, describe what happens when you try to use the dryer. Tell us about unusual sounds, interrupted programmes, damp laundry or visible damage. Please also mention any previous repair affecting the fault. This helps us arrange appropriate support, although the engineer may still need to inspect the appliance.

Diagnosing a fault on the Ashby tumble dryer costs £41.00 if no repair follows. We will explain how this charge applies before you agree to a visit. If the fault may be covered by a guarantee or your legal rights, tell us when booking so that we can check the appropriate route.

The engineer will assess the fault and explain the proposed repair, including the parts and labour involved. You will be told the total repair price before work begins. We will not carry out chargeable repair work without your agreement. If

[P5] Warranty
cover damage caused by misuse, accidental damage, unsuitable installation or failure to follow the care instructions. A repair carried out elsewhere does not automatically remove your rights, but damage caused by that work may fall outside the warranty.

If our assessment finds that the problem is not covered, we will explain why. We will also explain any proposed charges before asking you to agree to work outside the warranty. You do not have to accept a paid repair, and we will not treat your request for a warranty assessment as permission to carry one out.

An engineer visit for the Ashby tumble dryer after the warranty has ended costs £56.00.

That visit charge does not include replacement parts or repair work. If further work is recommended, we will explain the proposed cost and ask for your agreement before proceeding. We will also consider whether the fault relates to a repair already covered by the warranty or whether your statutory rights may apply.

If you need to change an appointment, contact us so that we can discuss alternative arrangements. If access is unavailable or the appliance cannot be worked on safely, we will explain what needs to change before the repair can proceed. We will keep you informed about the status of your request.

If a repair does not resolve the reported fault, contact us with your repair record or the

System's answer:
Paid repairs to your Ashby tumble dryer are **guaranteed for 105 days**. If the repaired fault returns during that period, keep your repair confirmation and contact Halvard Home so they can review whether further work is covered. [P1]

The passages don’t state how long the dryer’s original warranty lasts, so they don’t establish the full period for free warranty repairs. Your statutory rights may also apply. [P5]

---

## 37. TWOPART-004

Question: How long does Halvard Home take to refund a recalled Vale fridge freezer, and when would it lend me a replacement if a repair takes too long?

Can the question be answered from the documents: yes

Reference answer: Refunds for recalled appliances are paid within 31 days. If a repair to the Vale fridge freezer takes longer than 25 working days, Halvard Home lends a replacement.

Passages given to the system:
[P1] Warranty
the confirmed fault. Our engineer will explain what needs to be done. If the inspection identifies work outside the warranty, we will explain why and ask for your agreement before carrying out work that you would have to pay for.

A fault may fall outside the warranty if it results from misuse, accidental damage or an installation that does not follow the supplied instructions. We will consider the circumstances rather than assume that damage or an unrelated alteration caused the reported fault. Our decision will be explained clearly.

Only an engineer authorised by Halvard Home should carry out a repair arranged under this warranty. If you have already asked someone else to inspect or repair the appliance, tell us what they did. This helps us assess the fault safely and explain whether their work affects the proposed warranty repair.

We will keep you informed about the repair and contact you if the arrangements change. If we cannot complete the work as promised, we will explain the reason, discuss the next steps and tell you how to raise concerns. You should not have to chase an explanation for a missed appointment.

If a repair to the Vale fridge freezer takes longer than 25 working days, Halvard Home lends a replacement.

We will contact you to arrange delivery and explain the loan terms in plain language. The replacement remains Halvard Home’s property.

[P2] Warranty
the confirmed fault. Our engineer will explain what needs to be done. If the inspection identifies work outside the warranty, we will explain why and ask for your agreement before carrying out work that you would have to pay for.

A fault may fall outside the warranty if it results from misuse, accidental damage or an installation that does not follow the supplied instructions. We will consider the circumstances rather than assume that damage or an unrelated alteration caused the reported fault. Our decision will be explained clearly.

Only an engineer authorised by Halvard Home should carry out a repair arranged under this warranty. If you have already asked someone else to inspect or repair the appliance, tell us what they did. This helps us assess the fault safely and explain whether their work affects the proposed warranty repair.

We will keep you informed about the repair and contact you if the arrangements change. If we cannot complete the work as promised, we will explain the reason, discuss the next steps and tell you how to raise concerns. You should not have to chase an explanation for a missed appointment.

If a repair to the Vale fridge freezer takes longer than 25 working days, Halvard Home lends a replacement.

We will contact you to arrange delivery and explain the loan terms in plain language. The replacement remains Halvard Home’s property.

[P3] Vale fridge freezer warranty period
Vale fridge freezer warranty period

Your Halvard Home Vale fridge freezer comes with a two-year warranty from the date of purchase. Keep your receipt or order confirmation as proof of when cover began.

On this model, E-5338 means the purchase date is missing from the appliance’s warranty record, preventing it from displaying the correct warranty end date. This is a registration fault, not a cooling fault, and does not itself mean your warranty has expired.

Contact Halvard Home support with your proof of purchase and ask for the warranty record to be corrected. There is no need to unplug the appliance or change its temperature settings for this message.

Your warranty does not affect your statutory rights.

[P4] Warranty
details of your visit. We will review the work and explain the appropriate remedy. Nothing in this warranty limits your statutory rights, including rights you may have against the retailer that sold you the appliance.

## Vale fridge freezer

### Cover period

The Vale fridge freezer is covered for 77 months from the date of delivery. This is the warranty period for faults covered by Halvard Home’s warranty. The delivery date, rather than the date you placed your order or paid for your appliance, determines when this cover starts.

Keep your proof of purchase and any delivery confirmation with your warranty documents. These records help us establish when your cover began and whether it is still active. Your documents should identify the Vale fridge freezer and show who supplied it.

If your purchase receipt and delivery confirmation show different dates, we use the delivery confirmation to establish the start of cover. If you collected the appliance yourself, we treat the collection date shown on your collection record as the delivery date.

If you cannot find your delivery confirmation, contact Halvard Home with the purchase information you have. We will review the available records and explain what evidence we need. Missing paperwork does not automatically mean that your warranty claim will be refused.

Registering your appliance helps us keep your details with your warranty record, but registration does not

[P5] Warranty
details of your visit. We will review the work and explain the appropriate remedy. Nothing in this warranty limits your statutory rights, including rights you may have against the retailer that sold you the appliance.

## Vale fridge freezer

### Cover period

The Vale fridge freezer is covered for 77 months from the date of delivery. This is the warranty period for faults covered by Halvard Home’s warranty. The delivery date, rather than the date you placed your order or paid for your appliance, determines when this cover starts.

Keep your proof of purchase and any delivery confirmation with your warranty documents. These records help us establish when your cover began and whether it is still active. Your documents should identify the Vale fridge freezer and show who supplied it.

If your purchase receipt and delivery confirmation show different dates, we use the delivery confirmation to establish the start of cover. If you collected the appliance yourself, we treat the collection date shown on your collection record as the delivery date.

If you cannot find your delivery confirmation, contact Halvard Home with the purchase information you have. We will review the available records and explain what evidence we need. Missing paperwork does not automatically mean that your warranty claim will be refused.

Registering your appliance helps us keep your details with your warranty record, but registration does not

System's answer:
The passages don’t state how long Halvard Home takes to refund a recalled Vale fridge freezer.

For a repair, Halvard Home will lend you a replacement if it takes **longer than 25 working days**. They’ll contact you to arrange delivery and explain the loan terms; the replacement remains their property. [P1–P2]

---

## 38. POL-HEAD-015

Question: How long are repairs to the Corra induction hob covered for?

Can the question be answered from the documents: yes

Reference answer: Repairs to the Corra induction hob are guaranteed for 150 days.

Passages given to the system:
[P1] Warranty
Please use it in accordance with the instructions provided and take reasonable care of it. Tell us if it develops a fault so that we can help.

The engineer will check the repaired appliance and explain the work carried out. Ask about anything you do not understand, including whether it is ready to use. If the fault remains or returns, contact us and describe what you have noticed so that we can review the repair.

Please take care with food affected by a cooling fault and follow appropriate food safety advice. Do not rely on smell or appearance alone to decide whether food is safe. Tell us about losses you believe resulted from the fault; we will explain how to submit a claim and how it will be assessed.

Your warranty does not replace or restrict your statutory rights. You may also have rights against the retailer that sold you the appliance. If you disagree with a warranty decision or are unhappy with the repair, contact Halvard Home customer support and ask for your complaint to be reviewed.

## Corra induction hob

### Cover period

The Corra induction hob is covered for 43 months from the date of delivery. This is the warranty period for the appliance. It begins when the hob is delivered to you, rather than when you install it, register it or start using it.

Keep your

[P2] Warranty
Please use it in accordance with the instructions provided and take reasonable care of it. Tell us if it develops a fault so that we can help.

The engineer will check the repaired appliance and explain the work carried out. Ask about anything you do not understand, including whether it is ready to use. If the fault remains or returns, contact us and describe what you have noticed so that we can review the repair.

Please take care with food affected by a cooling fault and follow appropriate food safety advice. Do not rely on smell or appearance alone to decide whether food is safe. Tell us about losses you believe resulted from the fault; we will explain how to submit a claim and how it will be assessed.

Your warranty does not replace or restrict your statutory rights. You may also have rights against the retailer that sold you the appliance. If you disagree with a warranty decision or are unhappy with the repair, contact Halvard Home customer support and ask for your complaint to be reviewed.

## Corra induction hob

### Cover period

The Corra induction hob is covered for 43 months from the date of delivery. This is the warranty period for the appliance. It begins when the hob is delivered to you, rather than when you install it, register it or start using it.

Keep your

[P3] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 189 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

[P4] Warranty
parts. When assessing a repair, we will explain how the appliance cover, replacement part cover and labour terms apply to your claim.

Replacement parts fitted to the Corra induction hob are covered for a further 302 days. This cover starts on the date the part is fitted during a repair authorised by Halvard Home. Keep the repair confirmation, as it records the fitting date.

Replacement part cover applies to the fitted part, not to the whole hob. It can continue beyond the appliance warranty’s expiry date. If the appliance warranty would cover that part for longer, fitting a replacement does not shorten that existing cover.

Fitting a replacement part does not restart the appliance warranty or renew free labour cover. If a fitted part develops a fault, contact us with the repair details. We will explain whether the part remains covered and whether labour charges apply.

Tell us about a fault as soon as you notice it. Describe what happens when you use the hob and provide your delivery or repair documents where available. Do not keep using the hob if you believe it may be unsafe.

If you report an eligible fault before the relevant cover expires, we will assess it using the date you contacted us. An appointment arranged after expiry will not, by itself, make that reported fault ineligible. Keep a copy of

[P5] Warranty
us if it develops a fault or is damaged. Do not attempt to repair or alter it. We will arrange its return as part of completing your repair and restoring your hob to use.

Refurbished parts are sometimes fitted to the Corra induction hob when new parts are scarce. A refurbished part is covered for 45 weeks.

Any refurbished part we fit will be checked for safety, condition and suitability. We will record the parts used in the repair and explain the cover that applies. Using a refurbished part does not remove your legal rights or reduce the warranty cover that otherwise applies to the hob.

We will keep you informed if the repair is delayed, if the engineer finds further damage, or if the proposed work changes. Please keep your contact details up to date so we can reach you. If you need to change an appointment, contact customer support so we can rearrange it.

After the repair, the engineer will check that the hob operates safely and explain any relevant care advice. Keep the repair record with your proof of purchase. If the fault returns or you are unhappy with the work, contact us and describe the problem so we can review it.

An engineer visit for the Corra induction hob after the warranty has ended costs £74.00.

This visit charge is separate from

System's answer:
The passages give conflicting repair-cover periods: **189 days** in [P3] and **302 days** in [P4], starting when the replacement part is fitted during an authorised repair. This cover applies to the fitted part, not the whole hob.

For **refurbished parts**, the stated cover is **45 weeks** [P5].

---

## 39. SHARED-006

Question: Is water leaking underneath the outdoor unit of my Orrin heat pump normal during defrosting?

Can the question be answered from the documents: yes

Reference answer: During defrosting, ice on the outdoor coil melts and drains away, leaving a puddle underneath.

Passages given to the system:
[P1] Water leaking underneath your Orrin heat pump
Water leaking underneath your Orrin heat pump

Water beneath the outdoor unit can be normal. During defrosting, ice on the outdoor coil melts and drains away, leaving a puddle underneath.

Check where the water is coming from without removing any covers. If it drains from beneath the outdoor unit during or shortly after defrosting, monitor it to see whether it stops.

Clear loose leaves from around the drainage area, but do not insert tools into the unit or try to chip away ice.

If water runs continuously, comes from a pipe joint or appears beneath an indoor unit, arrange an inspection by a qualified heat pump engineer.

Keep away from wet electrical connections. Contact Halvard Home support if you cannot identify the source safely.

[P2] Frost or condensation on your Orrin heat pump
Frost or condensation on your Orrin heat pump

A light coating of frost on the outdoor unit is normal in cold weather and should clear during automatic defrosting. Condensation beneath the unit is also normal.

KX-9512 is the condensate drain insert in the Orrin heat pump’s outdoor unit. If this insert becomes blocked with dirt, water can collect in the base and freeze, causing a thick layer of ice.

Switch the heat pump off using its controls and remove loose leaves from around the base, without opening any covers. Do not chip away ice or pour boiling water over the unit.

If thick ice remains or returns, leave the unit switched off and contact Halvard Home support to arrange inspection and cleaning of the drain insert.

[P3] Orrin heat pump display fault
Orrin heat pump display fault

On the Halvard Home Orrin heat pump, E-5946 means the outdoor coil temperature sensor is not providing a reliable reading. The heat pump stops its compressor because it cannot safely control the defrost cycle.

Switch the heat pump off using its controller, then turn off the power at the isolator. Leave it off for five minutes before restoring power and restarting it once.

If the fault returns, leave the unit switched off and contact Halvard Home support or a qualified heat pump engineer. Tell them that the outdoor coil sensor fault has returned after a restart.

Do not remove the casing, touch internal wiring or repeatedly reset the unit. The sensor and its connections need professional inspection.

[P4] Orrin heat pump heating slowly
Orrin heat pump heating slowly

Your Orrin heat pump warms your home gradually, so radiators may feel cooler than those connected to a boiler. This does not necessarily mean there is a fault.

If heating seems unusually slow or weak:

- Check that heating mode is selected and the timer allows heating now.
- Set the room thermostat 2°C above the current room temperature to request heat.
- Keep doors and windows closed while the home warms up.
- Check the outdoor unit for leaves or other loose debris blocking airflow. Do not remove covers or touch internal parts.

Cold weather and defrost cycles can temporarily reduce heat output. Avoid repeatedly switching the system off and on.

If performance remains poor, contact Halvard Home support or a qualified heat pump engineer.

[P5] # Strange noises from your Orrin heat pump
# Strange noises from your Orrin heat pump

A gentle hum or airflow sound is usually normal while your Orrin heat pump is running. A brief whoosh can occur when the unit changes operating mode.

If you hear an unfamiliar rattle, switch the heat pump off using its normal controls before checking around the outdoor unit. Look for loose objects nearby, such as plant pots or garden furniture, and move anything touching the casing. Do not remove panels or reach through the grille.

Restart the heat pump once the area is clear. If the noise continues, contact Halvard Home support and describe when it happens.

For loud grinding, scraping or repeated banging, stop using the heat pump and arrange a professional inspection.

System's answer:
Yes. Water beneath the outdoor unit during or shortly after defrosting is normal: ice on the outdoor coil melts and drains away, leaving a puddle.

Monitor it to check that it stops. If water runs continuously or comes from a pipe joint, arrange an inspection by a qualified heat pump engineer. Keep away from wet electrical connections.

---

## 40. POL-SINGLE-003

Question: If I sell my Fenwick cooker hood, how long does the buyer have to transfer the warranty into their name?

Can the question be answered from the documents: yes

Reference answer: If the Fenwick cooker hood is sold on, the new owner must transfer the warranty within 39 days.

Passages given to the system:
[P1] Warranty
owner receives the benefit of the cover that remains valid, subject to the warranty terms. We will confirm the transfer and explain any information still needed to complete our records.

If the transfer requirement has not been met, the new owner should contact us so that we can explain the position. Do not assume that a change of ownership has been recorded simply because the seller has provided the original paperwork.

This warranty is provided by Halvard Home in addition to your statutory rights. Its start date, end date and transfer requirements do not remove or restrict rights that cannot legally be excluded. You may also have rights against the retailer that sold you the Fenwick cooker hood.

### Repairs under warranty

If your Fenwick cooker hood develops a fault covered by the warranty, Halvard Home will arrange a repair without charging you for the necessary parts, labour or engineer travel. We will explain what happens next and keep you informed as your repair progresses.

Contact our customer care team to report the fault. Please describe what is happening and have your proof of purchase available, together with the product details shown on the appliance label. If you cannot find these details, we will help you locate them safely.

We may ask about installation, use and cleaning to help establish the cause of the problem. We may also suggest

[P2] Warranty
owner receives the benefit of the cover that remains valid, subject to the warranty terms. We will confirm the transfer and explain any information still needed to complete our records.

If the transfer requirement has not been met, the new owner should contact us so that we can explain the position. Do not assume that a change of ownership has been recorded simply because the seller has provided the original paperwork.

This warranty is provided by Halvard Home in addition to your statutory rights. Its start date, end date and transfer requirements do not remove or restrict rights that cannot legally be excluded. You may also have rights against the retailer that sold you the Fenwick cooker hood.

### Repairs under warranty

If your Fenwick cooker hood develops a fault covered by the warranty, Halvard Home will arrange a repair without charging you for the necessary parts, labour or engineer travel. We will explain what happens next and keep you informed as your repair progresses.

Contact our customer care team to report the fault. Please describe what is happening and have your proof of purchase available, together with the product details shown on the appliance label. If you cannot find these details, we will help you locate them safely.

We may ask about installation, use and cleaning to help establish the cause of the problem. We may also suggest

[P3] Warranty
under law.

Replacement parts fitted to the Fenwick cooker hood are covered for a further 348 days. This parts cover begins on the date the replacement part is fitted under an authorised warranty repair. Keep the repair confirmation so that the fitting date can be checked.

The replacement parts cover applies to the part supplied and fitted, rather than restarting cover for the entire Fenwick cooker hood. If the original warranty is still active, it continues according to its existing terms alongside the protection for the replacement part.

Ask us if you are unsure which cover applies to a fault following a repair. We will check the delivery and repair records and explain the position. You do not need to decide which warranty provision applies before contacting us.

If the Fenwick cooker hood is sold on, the new owner must transfer the warranty within 39 days. This requirement runs from the date of sale. The new owner should contact Halvard Home to request the transfer and provide evidence of the change of ownership.

The seller should pass on the delivery confirmation, purchase receipt and any repair records. These documents help the new owner establish the original warranty dates and identify any replacement parts that remain covered. Personal information unrelated to the warranty can be removed.

Transferring the warranty does not restart or extend the original cover. The new

[P4] Warranty
under law.

Replacement parts fitted to the Fenwick cooker hood are covered for a further 348 days. This parts cover begins on the date the replacement part is fitted under an authorised warranty repair. Keep the repair confirmation so that the fitting date can be checked.

The replacement parts cover applies to the part supplied and fitted, rather than restarting cover for the entire Fenwick cooker hood. If the original warranty is still active, it continues according to its existing terms alongside the protection for the replacement part.

Ask us if you are unsure which cover applies to a fault following a repair. We will check the delivery and repair records and explain the position. You do not need to decide which warranty provision applies before contacting us.

If the Fenwick cooker hood is sold on, the new owner must transfer the warranty within 39 days. This requirement runs from the date of sale. The new owner should contact Halvard Home to request the transfer and provide evidence of the change of ownership.

The seller should pass on the delivery confirmation, purchase receipt and any repair records. These documents help the new owner establish the original warranty dates and identify any replacement parts that remain covered. Personal information unrelated to the warranty can be removed.

Transferring the warranty does not restart or extend the original cover. The new

[P5] Fenwick cooker hood warranty
Fenwick cooker hood warranty

Your Halvard Home Fenwick cooker hood comes with a two-year warranty from the date of purchase. Keep your receipt or order confirmation, as you will need it to show when you bought the appliance.

The warranty covers faults caused by defective materials or workmanship during normal domestic use. It does not cover accidental damage, misuse or routine maintenance, such as cleaning grease filters.

If your cooker hood develops a fault during the warranty period, contact Halvard Home customer support. Have your proof of purchase ready and describe what is happening. Do not attempt internal repairs yourself; support can advise you on the next steps.

Your warranty does not affect your statutory rights.

System's answer:
The buyer must transfer the warranty within **39 days of the date of sale** by contacting Halvard Home and providing evidence of the change of ownership. [P3]

---

## 41. IDENT-028

Question: What does error E-6779 mean?

Can the question be answered from the documents: yes

Reference answer: If your Corra induction hob heats slowly or feels weak, E-6779 means restricted cooling airflow has triggered the hob’s protective power limit.

Passages given to the system:
[P1] Tessa dishwasher not switching on
Tessa dishwasher not switching on

On the Halvard Home Tessa dishwasher, E-1736 means the power protection circuit has shut the unit down after detecting an unstable mains supply. The display may briefly show the code before going blank.

To reset the dishwasher:

1. Switch off the wall socket and unplug the dishwasher with dry hands.
2. Leave it disconnected for 10 minutes.
3. Check that the plug and cable have no visible damage.
4. If they look undamaged, reconnect the dishwasher directly to the wall socket, switch the socket on, then press the power button.

Do not use an extension lead. If the dishwasher remains unresponsive or the fault returns, unplug it and contact Halvard Home support. Do not remove any panels or attempt internal repairs.

[P2] Updating your Mira robot vacuum
Updating your Mira robot vacuum

On the Halvard Home Mira robot vacuum, error E-7804 means the firmware download was interrupted before installation could begin. Your vacuum is still using its previous firmware.

To retry the update:

1. Place Mira on its charging dock and leave the dock switched on.
2. Check that your home Wi-Fi is working and that Mira shows as connected in the Halvard Home app.
3. Open Mira’s settings in the app, select ‘Firmware update’, then tap ‘Retry’.
4. Keep the vacuum docked and your router switched on until the app confirms the update is complete.

If the update fails again, close and reopen the app, then retry once. Contact Halvard Home support if the problem continues.

[P3] Saving energy with your Tessa dishwasher
Saving energy with your Tessa dishwasher

The Tessa dishwasher’s Eco programme uses lower wash temperatures and a longer cycle to reduce electricity use. For everyday loads, select Eco and wait until the dishwasher is full before starting, without blocking the spray arms.

Error code E-9544 means the temperature sensor has detected overheating during Eco mode, so the dishwasher has paused the programme to prevent unnecessary energy use.

Switch the dishwasher off at the mains for five minutes, then restore power and select Eco again. If the warning returns, stop using the appliance and contact Halvard Home support to arrange a sensor check. Do not remove any panels or attempt repairs yourself.

For further savings, switch off heated drying if your model offers this option.

[P4] Descaling your Tessa dishwasher
Descaling your Tessa dishwasher

On the Tessa dishwasher, E-6067 means limescale is restricting water flow through the heater, so the water is taking too long to reach the wash temperature.

To descale your dishwasher:

1. Cancel the programme, switch off the dishwasher and let it cool.
2. Remove all dishes and cutlery, then check and clean the filter.
3. Add a dishwasher-safe descaler, following the quantity and placement instructions on its packaging.
4. Switch the dishwasher back on and run an empty programme at 60°C, unless the descaler instructions specify otherwise.

Do not add detergent or mix the descaler with other cleaning products.

If the warning returns after descaling, stop using the dishwasher and contact Halvard Home support. The heater or water pathway may need inspection.

[P5] Tessa dishwasher: delay start fault
Tessa dishwasher: delay start fault

On a Halvard Home Tessa dishwasher, E-9509 means the delay start timer has lost its saved countdown. The dishwasher pauses rather than starting at an unexpected time.

To reset the timer:

1. Press and hold the Start button for three seconds to cancel the delayed programme.
2. Switch the dishwasher off at the wall socket for one minute, then switch it back on.
3. Select your wash programme again.
4. Set the delay you want, press Start and close the door firmly.

The countdown begins only when the door is fully closed. Opening the door pauses it until you close it again.

If the fault returns, cancel delay start and contact Halvard Home support before trying another delayed wash.

System's answer:
The provided passages don’t explain error **E-6779**, so I can’t determine its meaning. Contact Halvard Home support with the error code and your appliance model.

---

## 42. FOLLOW-033

Question: What about the Lumen smart thermostat?

Conversation so far:
User: How far can I tip the Brio kettle while carrying it?
Assistant: Do not tilt the Brio kettle more than 56 degrees when carrying it.

Can the question be answered from the documents: yes

Reference answer: Do not tilt the Lumen smart thermostat more than 29 degrees when carrying it.

Passages given to the system:
[P1] # Installing your Lumen smart thermostat
# Installing your Lumen smart thermostat

Before you begin, check the supplied installation guide to confirm that your Lumen smart thermostat is compatible with your heating system. If you are unsure, ask a qualified heating installer before removing your existing thermostat.

Choose an internal wall around 1.5 metres above the floor, away from radiators, direct sunlight and draughts. This helps the thermostat measure the room temperature accurately.

Switch off the heating system’s electricity supply before any wiring work. Have a qualified installer connect the thermostat according to the supplied wiring instructions; do not guess wire connections from their colours.

Once installation is complete, restore power and follow the on-screen setup instructions. Set your preferred temperature, then check that the heating responds. Keep the installation guide for future reference.

[P2] Safety and recalls
, with care for the electrical supply, the heating system and the people in your home. Follow the installation instructions supplied with the Lumen smart thermostat. If those instructions are missing or unclear, contact Halvard Home before starting work.

Use a qualified installer for work involving fixed wiring or connections to your heating system. Do not attempt electrical work unless you are competent and legally permitted to do it. Your installer should check that the proposed installation is suitable for your home and complies with applicable requirements.

Choose a dry indoor position where the Lumen smart thermostat is protected from splashes, condensation and accidental knocks. Do not install it where steam, grease or damp could reach the casing or electrical connections. Keep the installation area clear so that the device can be accessed safely.

The Lumen smart thermostat must be installed within 263 centimetres of its socket. Position the cable so that it is not stretched, trapped or exposed to damage. The socket must remain accessible so that the electrical supply can be disconnected safely when needed.

Install the Lumen smart thermostat at least 149 centimetres from a gas hob or open flame. Do not choose a position where cooking heat could affect operation. Ask your installer to assess the location if there is uncertainty about heat exposure or the suitability of the

[P3] Safety and recalls
, with care for the electrical supply, the heating system and the people in your home. Follow the installation instructions supplied with the Lumen smart thermostat. If those instructions are missing or unclear, contact Halvard Home before starting work.

Use a qualified installer for work involving fixed wiring or connections to your heating system. Do not attempt electrical work unless you are competent and legally permitted to do it. Your installer should check that the proposed installation is suitable for your home and complies with applicable requirements.

Choose a dry indoor position where the Lumen smart thermostat is protected from splashes, condensation and accidental knocks. Do not install it where steam, grease or damp could reach the casing or electrical connections. Keep the installation area clear so that the device can be accessed safely.

The Lumen smart thermostat must be installed within 263 centimetres of its socket. Position the cable so that it is not stretched, trapped or exposed to damage. The socket must remain accessible so that the electrical supply can be disconnected safely when needed.

Install the Lumen smart thermostat at least 76 centimetres from a gas hob or open flame. Do not choose a position where cooking heat could affect operation. Ask your installer to assess the location if there is uncertainty about heat exposure or the suitability of the

[P4] Lumen thermostat not switching on
Lumen thermostat not switching on

If your Lumen smart thermostat has a blank screen and does not respond, start by checking its power supply.

If there is a clearly labelled wall switch supplying the thermostat, make sure it is on. If it is already on, switch it off, wait 30 seconds, then switch it back on. Do not remove the thermostat cover or touch any wiring.

Check whether other electrical items nearby have also lost power. A wider power cut may explain why the thermostat is not switching on.

If you notice a burning smell, unusual heat or damaged wiring, stop using the unit and contact a qualified electrician.

If the thermostat still does not respond, contact Halvard Home support and describe the checks you have completed.

[P5] Safety and recalls
handle.

Do not tilt the Lumen smart thermostat more than 29 degrees when carrying it. Plan the route before lifting it, and keep it supported as you carry it. Do not lift or pull it by its cable, plug or attached wiring.

Protect the casing and controls from knocks during the move. Use protective packaging that holds the device securely without pressing against its controls. Keep it dry, and do not place objects on top of it while it is packed or awaiting installation.

At the new location, check the device for damage before arranging installation. If it has been dropped, crushed or exposed to water, do not connect it to the electrical supply. Contact Halvard Home and explain what happened so that appropriate safety advice can be provided.

After moving the Lumen smart thermostat, wait 45 hours before switching it on. This requirement does not replace the need for a safe installation or a damage check. Leave the device disconnected if you have concerns about its condition, even when the waiting period has passed.

Have the installer check that the mounting is secure, the wiring is protected and the heating controls respond as intended. Make sure you understand how to disconnect the electrical supply safely. Keep the installation instructions somewhere accessible for maintenance or a future move.

If you notice smoke, a burning smell

System's answer:
Do not tilt the Lumen smart thermostat more than **29 degrees** when carrying it.

---

## 43. POL-TWO-004

Question: How long are repairs to the Brio kettle covered for?

Can the question be answered from the documents: yes

Reference answer: Repairs to the Brio kettle are guaranteed for 122 days.

Passages given to the system:
[P1] Warranty
happened and provide the information we need to identify your Brio kettle. If it appears unsafe, stop using it and unplug it if you can safely do so. Do not attempt a repair yourself.

We assess whether a claim falls within the cover period using the date you report the fault to us. If you report a covered fault before your warranty expires, the claim will not become invalid simply because our assessment or the agreed repair takes place after the cover has ended.

Labour for repairs is free for the first 10 months. This applies to work authorised by Halvard Home to put right a fault covered by the warranty. It does not apply to work that you arrange independently without our agreement, or to work on damage outside the warranty.

After the free labour cover ends, a labour charge may apply even if the fault otherwise qualifies for warranty support. We will explain any proposed charge before asking you to approve the repair. We will not treat your request for help as permission to carry out chargeable work.

Replacement parts fitted to the Brio kettle are covered for a further 138 days. This cover begins on the date the parts are fitted during a repair authorised by Halvard Home. Keep the repair record, as it helps us confirm the fitting date if a replacement part develops a fault

[P2] Warranty
happened and provide the information we need to identify your Brio kettle. If it appears unsafe, stop using it and unplug it if you can safely do so. Do not attempt a repair yourself.

We assess whether a claim falls within the cover period using the date you report the fault to us. If you report a covered fault before your warranty expires, the claim will not become invalid simply because our assessment or the agreed repair takes place after the cover has ended.

Labour for repairs is free for the first 10 months. This applies to work authorised by Halvard Home to put right a fault covered by the warranty. It does not apply to work that you arrange independently without our agreement, or to work on damage outside the warranty.

After the free labour cover ends, a labour charge may apply even if the fault otherwise qualifies for warranty support. We will explain any proposed charge before asking you to approve the repair. We will not treat your request for help as permission to carry out chargeable work.

Replacement parts fitted to the Brio kettle are covered for a further 138 days. This cover begins on the date the parts are fitted during a repair authorised by Halvard Home. Keep the repair record, as it helps us confirm the fitting date if a replacement part develops a fault

[P3] Warranty
contact us before committing to work if you intend to seek reimbursement through the warranty.

These exclusions describe the limits of this warranty, not the limits of your legal rights. Nothing here excludes or restricts rights or remedies available under applicable consumer law, including rights against the retailer. If a warranty exclusion applies, you may still be entitled to assistance or a remedy under that law.

## Brio kettle

### Cover period

The Brio kettle is covered for 47 months from the date of delivery. This is the date the kettle reaches you, rather than the date you place your order or make payment. Your delivery confirmation will normally show the date we use to establish your cover.

Keep your proof of purchase and delivery confirmation somewhere safe. We may ask to see them when you make a claim. If your records are missing or show conflicting information, contact Halvard Home so we can help check the delivery details and confirm when your cover began.

The cover period applies to faults caused by defective materials or workmanship, provided the Brio kettle has been used and cared for as instructed. Being within the cover period does not mean that damage from misuse, accidental damage or normal wear is covered by this warranty.

Tell us about a fault as soon as you notice it. Please explain what has

[P4] Warranty
contact us before committing to work if you intend to seek reimbursement through the warranty.

These exclusions describe the limits of this warranty, not the limits of your legal rights. Nothing here excludes or restricts rights or remedies available under applicable consumer law, including rights against the retailer. If a warranty exclusion applies, you may still be entitled to assistance or a remedy under that law.

## Brio kettle

### Cover period

The Brio kettle is covered for 47 months from the date of delivery. This is the date the kettle reaches you, rather than the date you place your order or make payment. Your delivery confirmation will normally show the date we use to establish your cover.

Keep your proof of purchase and delivery confirmation somewhere safe. We may ask to see them when you make a claim. If your records are missing or show conflicting information, contact Halvard Home so we can help check the delivery details and confirm when your cover began.

The cover period applies to faults caused by defective materials or workmanship, provided the Brio kettle has been used and cared for as instructed. Being within the cover period does not mean that damage from misuse, accidental damage or normal wear is covered by this warranty.

Tell us about a fault as soon as you notice it. Please explain what has

[P5] Warranty
.

The replacement part cover applies to defects in the fitted part, not to unrelated faults elsewhere in the kettle. It does not shorten any cover still available under the original warranty. Where the original warranty provides longer protection for the same fault, we will assess your claim under that cover.

A repair does not restart the warranty for the Brio kettle itself. Unless we confirm otherwise in writing, its cover continues from the original delivery date. The separate protection for fitted replacement parts should not be read as an extension of the warranty for the entire kettle.

If we replace the Brio kettle under the warranty rather than repair it, the replacement carries the cover remaining from the original delivery date. We will provide written confirmation of the applicable end date so that you can keep it with your claim records and proof of purchase.

If the Brio kettle is sold on, the new owner must transfer the warranty within 42 days. The transfer deadline runs from the date of sale to the new owner. The seller should pass on the proof of purchase, delivery details and any repair records needed to support the transfer.

The new owner should contact Halvard Home with those records and evidence of the sale. A transfer does not restart or extend the cover. The warranty remains linked to the original delivery date, and its

System's answer:
Repair labour is free for the first **10 months** for covered repairs authorised by Halvard Home. Replacement parts fitted during an authorised repair are covered for **138 days from the fitting date**. [P1]

---

## 44. IDENT-001

Question: What is part KX-9283 for?

Can the question be answered from the documents: yes

Reference answer: KX-9283 is the part number for the Ashby’s Wi-Fi module, which connects the dryer to the app.

Passages given to the system:
[P1] Updating your Lumen thermostat
Updating your Lumen thermostat

Keep your Lumen smart thermostat connected to power and Wi-Fi throughout a firmware update. In the Halvard Home app, select your thermostat, open Settings, then choose Firmware update. Tap Install if an update is available.

KX-1006 is the part number of the thermostat’s Wi-Fi control module, which downloads the firmware. You do not need to remove or replace this module for a routine update.

An update can freeze at 50% if the module loses its connection to your router. If progress has not changed for 10 minutes, restart your router, wait for the thermostat to reconnect, then tap Retry in the app. Do not disconnect the thermostat’s power during installation.

If the update stalls again, contact Halvard Home support.

[P2] Connecting your Keel washing machine to wi-fi
Connecting your Keel washing machine to wi-fi

Your Halvard Home Keel washing machine connects to a 2.4 GHz home wi-fi network. If your router combines network bands, select its separate 2.4 GHz network during setup.

A connection fault can occur when the machine retains an old network password after you change your router settings. To clear the saved connection, switch the machine on and hold the Wi-Fi button for five seconds, until its light flashes. Then repeat setup in the Halvard Home app using your current password.

KX-7856 is the part number for this product’s internal wi-fi module, not an error message. If the Wi-Fi light remains off after resetting, contact Halvard Home support for assessment. Do not open the machine or replace the module yourself.

[P3] Booking an engineer for your Corra induction hob
Booking an engineer for your Corra induction hob

If your Corra induction hob switches off during cooking and its cooling fan stays silent, the fan may have failed. Stop using the hob and switch it off at the wall before booking an engineer visit.

KX-5646 is the replacement cooling fan for the Corra induction hob, not an error code. An engineer must confirm the fault and fit the part; do not open the hob yourself.

Contact Halvard Home customer support to arrange a visit. Have your hob’s serial number, purchase date and a description of the fault ready. Mention the suspected cooling fan problem so the team can plan the repair. Ask about call-out charges and warranty cover before confirming your appointment.

[P4] Replacing a damaged lint filter
Replacing a damaged lint filter

KX-3639 is the replacement lint filter for the Halvard Home Ashby tumble dryer. If the filter mesh is torn, lint can pass into the dryer’s airflow system. Stop using the dryer until the damaged filter has been replaced.

Switch off the dryer, unplug it and allow it to cool. Open the door and lift the lint filter out of its slot in the door opening. Remove loose lint from the slot with a soft brush, then slide the replacement filter fully into place. Do not force it.

Order the replacement from Halvard Home support, quoting the part number above and your dryer’s model name. Clean the new filter after every drying cycle, and never run the dryer without it fitted.

[P5] Ashby tumble dryer not appearing in the app
Ashby tumble dryer not appearing in the app

If the Halvard Home app cannot find your Ashby tumble dryer, its Wi-Fi module may be stuck in standby. This prevents the dryer from broadcasting its setup signal.

KX-9283 is the part number for the Ashby’s Wi-Fi module, which connects the dryer to the app.

Try these steps:
- Switch the dryer off at the socket for 60 seconds, then switch it back on.
- Connect your phone to your home’s 2.4 GHz Wi-Fi network.
- Hold the dryer’s Wi-Fi button for five seconds, until its light flashes.
- Open the app and select “Add appliance”.

If the dryer still does not appear, contact Halvard Home support and describe the discovery problem. Do not open the casing or replace the module yourself.

System's answer:
KX-9283 is the Wi-Fi module for the Halvard Home Ashby tumble dryer. It connects the dryer to the Halvard Home app.

---

## 45. DELETED-009

Question: What should I do about the batch 2155 detergent pods I use with my Lumen smart thermostat?

Can the question be answered from the documents: no

Reference answer: That notice was withdrawn on 2026-06-19.

Passages given to the system:
[P1] Detergent pod safety notice
Detergent pod safety notice

Stop using detergent pods from batch 2155 with the Lumen smart thermostat, and return them for a refund.

Halvard Home has identified a potential safety issue with these pods. Check the batch details on the packaging and keep affected pods away from children and pets. Do not open, puncture or dispose of them in household waste.

If a pod has been used with your thermostat, stop using the device and contact Halvard Home customer support for guidance. Keep the packaging and proof of purchase if available. Our support team can explain how to return affected pods safely and arrange your refund. We apologise for the inconvenience.

[P2] Detergent pod safety notice
Detergent pod safety notice

Halvard Home is recalling the affected detergent pods as a precaution. Stop using detergent pods from batch 5311 with the Lumen smart thermostat, and return them for a refund.

Keep the pods in their original packaging, away from children, pets and food. Do not open, puncture or dispose of them in household waste. Contact Halvard Home customer support for safe return instructions and help arranging your refund.

If a pod has leaked, avoid touching the contents and seek advice from customer support. We apologise for the inconvenience and appreciate your help in keeping your home safe.

[P3] Cleaning gel pouch safety notice
Cleaning gel pouch safety notice

Stop using cleaning gel pouches from batch 3190 with the Lumen smart thermostat, and return them for a refund.

Halvard Home is recalling these pouches because the gel may damage the thermostat’s casing and affect its controls. Check the batch details printed on the pouch packaging. Keep affected pouches sealed and away from children and pets. Please contact Halvard Home customer support for help arranging your return and refund. If gel has touched your thermostat, avoid applying cleaning products and ask our support team for advice. We are sorry for the inconvenience and appreciate your help in keeping your home safe.

[P4] Cleaning your Lumen smart thermostat
Cleaning your Lumen smart thermostat

Your Lumen smart thermostat does not need descaling. Descaling products are for removing mineral deposits from water-handling equipment, not for cleaning the thermostat.

To clean the outside safely:

- Switch off the thermostat’s power supply before cleaning.
- Gently wipe the display and casing with a soft, dry cloth.
- Do not spray liquid onto the thermostat or use vinegar, descaler, abrasive cleaners or a steam cleaner.
- Do not open the casing to clean inside.

If you suspect limescale is affecting your heating or hot water, the thermostat is not the place to treat it. Check the care instructions for your boiler or water heater, or ask a qualified heating engineer. Do not add descaling chemicals to your heating system without professional guidance.

[P5] Corra hob detergent pod notice
Corra hob detergent pod notice

Stop using detergent pods from batch 6561 with the Corra induction hob, and return them for a refund.

We are sorry for the inconvenience and appreciate your help in keeping your home safe. Please check the batch details on the packaging and keep the affected pods separate from your usual cleaning products, out of reach of children and pets.

Do not use them to clean the hob or transfer them into an unlabelled container. Contact Halvard Home customer support for return instructions and help arranging your refund. If the packaging is missing or unclear, please ask us for advice before using the pods.

System's answer:
Stop using **batch 2155 detergent pods** and return them for a refund.

- Since you’ve used them with your Lumen smart thermostat, **stop using the thermostat** and contact Halvard Home customer support for guidance.
- Keep the affected pods away from children and pets. Do not open, puncture or put them in household waste.
- Keep the packaging and proof of purchase, if available. Customer support will explain how to return the pods safely and arrange your refund.

---

## 46. PARA-018

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

## 47. BRIDGE-008

Question: Within what timeframe are urgent safety visits made where I live, in postcode area PH?

Can the question be answered from the documents: yes

Reference answer: The Scotland North service team covers postcode areas AB, IV, KW, PH and DD. Urgent safety visits in Scotland North are made within 35 hours.

Passages given to the system:
[P1] Safety and recalls
our customer support channels. Tell us what happened, where the item is located and whether anyone has been hurt. We will not ask you to recreate a fault or demonstrate unsafe behaviour.

Our safety team reviews the information you provide and decides what action is needed. We may ask for photographs if these can be taken safely. You do not need to handle the affected item to support your report.

Urgent safety visits in North of England are made within 63 hours.

This commitment runs from when we receive your report and establish that an urgent safety visit is needed. We will explain that decision clearly and confirm the arrangements with you. Safety advice applies while you await the visit.

We arrange access with you rather than arriving without agreement. Please tell us about entry restrictions, shared entrances or anything that could prevent our representative from reaching the affected item safely. We will discuss a suitable approach.

Tell us if you need accessible communication, an interpreter or support from someone you trust. You can also explain circumstances that may make a visit difficult. We will consider reasonable adjustments without asking for unnecessary personal details.

Before the visit, we explain how to recognise our representative and check their identity. If you are unsure who is at your door, keep it closed and contact us through a channel you already trust.

Our

[P2] Safety and recalls
our customer support channels. Tell us what happened, where the item is located and whether anyone has been hurt. We will not ask you to recreate a fault or demonstrate unsafe behaviour.

Our safety team reviews the information you provide and decides what action is needed. We may ask for photographs if these can be taken safely. You do not need to handle the affected item to support your report.

Urgent safety visits in North of England are made within 63 hours.

This commitment runs from when we receive your report and establish that an urgent safety visit is needed. We will explain that decision clearly and confirm the arrangements with you. Safety advice applies while you await the visit.

We arrange access with you rather than arriving without agreement. Please tell us about entry restrictions, shared entrances or anything that could prevent our representative from reaching the affected item safely. We will discuss a suitable approach.

Tell us if you need accessible communication, an interpreter or support from someone you trust. You can also explain circumstances that may make a visit difficult. We will consider reasonable adjustments without asking for unnecessary personal details.

Before the visit, we explain how to recognise our representative and check their identity. If you are unsure who is at your door, keep it closed and contact us through a channel you already trust.

Our

[P3] Safety and recalls
was damaged. We may ask for photographs if these would help our assessment, but you should not handle an unsafe item or return to an unsafe area to take them.

We will explain whether your report needs an urgent safety visit, a recall collection or another response. An urgent safety visit is intended to assess and address a reported risk at your home. A recall collection removes an affected item under the arrangements set out in the relevant recall notice.

Urgent safety visits in Scotland South are made within 66 hours.

We will confirm that your case has been accepted for an urgent safety visit and explain the arrangements. Please tell us about access restrictions, shared entrances, parking difficulties or circumstances that could affect a safe visit. If access cannot be arranged, we will discuss how to keep you safe and agree how to proceed.

Recall collections in Scotland South are made within 45 working days.

If your item is included in a recall, follow the recall notice rather than relying on general advice about ordinary faults. We will explain how to arrange collection and what preparation is safe. Do not move, dismantle, package or dispose of an affected item unless we have confirmed that you should.

You can tell us about communication preferences, disability access needs or support you would like during the visit. We will discuss

[P4] Safety and recalls
was damaged. We may ask for photographs if these would help our assessment, but you should not handle an unsafe item or return to an unsafe area to take them.

We will explain whether your report needs an urgent safety visit, a recall collection or another response. An urgent safety visit is intended to assess and address a reported risk at your home. A recall collection removes an affected item under the arrangements set out in the relevant recall notice.

Urgent safety visits in Scotland South are made within 66 hours.

We will confirm that your case has been accepted for an urgent safety visit and explain the arrangements. Please tell us about access restrictions, shared entrances, parking difficulties or circumstances that could affect a safe visit. If access cannot be arranged, we will discuss how to keep you safe and agree how to proceed.

Recall collections in Scotland South are made within 45 working days.

If your item is included in a recall, follow the recall notice rather than relying on general advice about ordinary faults. We will explain how to arrange collection and what preparation is safe. Do not move, dismantle, package or dispose of an affected item unless we have confirmed that you should.

You can tell us about communication preferences, disability access needs or support you would like during the visit. We will discuss

[P5] Safety and recalls
access as agreed, contact us so that we can review the arrangements. If the condition of the item worsens, tell us and follow the safety advice already provided. Use the emergency services rather than waiting for our visit if there is an immediate danger.

We will keep a record of the concern, our assessment and the action agreed with you. Information needed to arrange the visit or collection may be shared with the service provider acting on our behalf. If you disagree with how your case is being handled, ask for it to be reviewed by our safety team.

## North of England

### Safety visits in this region

Halvard Home arranges safety visits across the North of England when an issue needs to be checked at your home. We explain what the visit is for, what you should do beforehand and how we will support you through the process.

If you think an item is unsafe, stop using it and keep people away from it. Disconnect it only if you can do so safely. Do not touch damaged parts or try to investigate the fault yourself.

If there is smoke, fire or an immediate threat to anyone’s safety, leave the affected area and contact the emergency services. Do not put yourself at risk to protect property or gather information for us.

You can report a safety concern through

System's answer:
Urgent safety visits in postcode area PH (Scotland South) are made within **66 hours**. [P3]

---

## 48. RESTRICT-PUBLIC-031

Question: How much can engineers spend on parts for the Keel washing machine before they need permission?

Can the question be answered from the documents: no

Reference answer: Only staff documents give this.

Passages given to the system:
[P1] Engineer service manual (extract)
combined value of the parts proposed for the repair, using the current internal parts prices. Include parts already fitted during the same repair when checking the total. Do not divide the work between service records to avoid approval.

If the proposed parts exceed the limit, stop and request approval through the service approval process. Provide the fault findings, proposed parts, current prices and the reason replacement is necessary. Keep the approval with the service record before fitting the additional parts.

The spending limit does not authorise work outside your training or the approved repair procedures. Escalate structural damage, suspected contamination, extensive corrosion or faults that cannot be safely diagnosed. Do not improvise repairs to safety devices or fit unapproved substitutes.

The internal diagnostic test on the Keel washing machine runs for 22 minutes.

Use the approved diagnostic procedure and record the result. Run powered checks only with the appliance in the safe condition specified by that procedure. Never bypass an interlock or leave live components accessible to the customer.

After fitting approved parts, check that connections, hoses, seals and protective covers are correctly secured. Complete the prescribed functional and safety checks. Investigate any leakage, abnormal noise or unresolved fault rather than treating a completed programme as proof of a successful repair.

Leave the work area safe and explain the repair status

[P2] Warranty
check clearly. If you cannot carry it out safely, let us know so we can arrange suitable help.

A warranty repair to the Keel washing machine is completed within 24 working days of the fault being confirmed. We will tell you when the fault has been confirmed and explain what the repair involves. We will also tell you how to contact us for an update.

Where the fault is covered, Halvard Home pays for the work and parts needed to put it right, including the engineer’s visit. We will not ask you to pay for covered repair work. If our assessment finds something outside the warranty, we will explain the reason before asking you to approve any chargeable work.

An engineer visit for the Keel washing machine after the warranty has ended costs £61.00. This charge is for the visit, rather than an agreement to carry out whatever repair may be needed. We will explain any proposed repair charges and ask for your agreement before proceeding.

We will agree access arrangements with you when booking a repair. Please make sure the engineer can reach the machine safely and can access its water and electricity connections. Tell us about restricted access, stairs or any other conditions that could affect the work.

Please empty the drum and remove belongings from around the machine before the engineer attends. Keep

[P3] Warranty
check clearly. If you cannot carry it out safely, let us know so we can arrange suitable help.

A warranty repair to the Keel washing machine is completed within 24 working days of the fault being confirmed. We will tell you when the fault has been confirmed and explain what the repair involves. We will also tell you how to contact us for an update.

Where the fault is covered, Halvard Home pays for the work and parts needed to put it right, including the engineer’s visit. We will not ask you to pay for covered repair work. If our assessment finds something outside the warranty, we will explain the reason before asking you to approve any chargeable work.

An engineer visit for the Keel washing machine after the warranty has ended costs £119.00. This charge is for the visit, rather than an agreement to carry out whatever repair may be needed. We will explain any proposed repair charges and ask for your agreement before proceeding.

We will agree access arrangements with you when booking a repair. Please make sure the engineer can reach the machine safely and can access its water and electricity connections. Tell us about restricted access, stairs or any other conditions that could affect the work.

Please empty the drum and remove belongings from around the machine before the engineer attends. Keep

[P4] Servicing and engineer visits
close the appliance’s water supply valve if it is safe and accessible, and contact us for advice.

A routine service of the Keel washing machine takes about 122 minutes. This is an estimate of the engineer’s working time, rather than a guaranteed appointment length. Access difficulties, the condition of the appliance or faults discovered during the visit may affect how the appointment proceeds. The engineer will explain any change to the planned work.

A routine service of the Keel washing machine costs £168.00. This price covers the routine service work described when you book. Repairs, replacement parts and work outside that scope require your agreement. If the engineer recommends additional work, we will explain what is needed and confirm the price before you decide whether to proceed.

When booking, tell us about any faults, warning messages or recent changes in performance. Mention any previous repairs or alterations that may be relevant. This helps us arrange suitable support and distinguish routine servicing from a repair visit. Have your appliance details and any available service records ready when you contact us.

Please also tell us about access restrictions, parking arrangements or anything that could affect the engineer’s ability to work safely. Let us know if the appliance is fitted into cabinetry or located where moving it may be difficult. We will discuss any preparation

[P5] Servicing and engineer visits
close the appliance’s water supply valve if it is safe and accessible, and contact us for advice.

A routine service of the Keel washing machine takes about 122 minutes. This is an estimate of the engineer’s working time, rather than a guaranteed appointment length. Access difficulties, the condition of the appliance or faults discovered during the visit may affect how the appointment proceeds. The engineer will explain any change to the planned work.

A routine service of the Keel washing machine costs £168.00. This price covers the routine service work described when you book. Repairs, replacement parts and work outside that scope require your agreement. If the engineer recommends additional work, we will explain what is needed and confirm the price before you decide whether to proceed.

When booking, tell us about any faults, warning messages or recent changes in performance. Mention any previous repairs or alterations that may be relevant. This helps us arrange suitable support and distinguish routine servicing from a repair visit. Have your appliance details and any available service records ready when you contact us.

Please also tell us about access restrictions, parking arrangements or anything that could affect the engineer’s ability to work safely. Let us know if the appliance is fitted into cabinetry or located where moving it may be difficult. We will discuss any preparation

System's answer:
The passages do not specify the spending limit. P1 says engineers must request approval if the combined cost of parts exceeds the limit, including parts already fitted during the same repair.

---

## 49. RESTRICT-STAFF-041

Question: What’s the highest amount of compensation a team leader can offer for the Brio kettle?

Can the question be answered from the documents: yes

Reference answer: The most a team leader may offer in compensation for the Brio kettle is £199.00.

Passages given to the system:
[P1] Servicing and engineer visits
of the Brio kettle takes about 135 minutes. This is a guide rather than a guarantee. The engineer will explain if the condition of your kettle affects the planned work or if a fault means that a separate repair appointment is needed.

A routine service of the Brio kettle costs £78.00. This price includes the engineer’s routine inspection, standard service checks and assessment of the kettle’s condition. Repairs, replacement parts and work outside the routine service are not included unless we expressly confirm otherwise when you book.

We will explain any proposed additional work and its price before asking for your agreement. You do not have to accept a repair simply because an engineer recommends it. If you decline work needed for safe operation, the engineer will explain why the kettle should not be used.

To arrange a service, contact Halvard Home through our usual customer support channels. Have your purchase details available if you can, and describe any changes in how the kettle works. Tell us about leaking, unusual smells, unexpected switching behaviour or visible damage rather than leaving these concerns until the visit.

A service appointment is not a substitute for reporting a suspected safety fault. If the kettle appears unsafe, stop using it and disconnect it from the electricity supply if you can do so safely. Contact Halvard Home for

[P2] Servicing and engineer visits
of the Brio kettle takes about 135 minutes. This is a guide rather than a guarantee. The engineer will explain if the condition of your kettle affects the planned work or if a fault means that a separate repair appointment is needed.

A routine service of the Brio kettle costs £78.00. This price includes the engineer’s routine inspection, standard service checks and assessment of the kettle’s condition. Repairs, replacement parts and work outside the routine service are not included unless we expressly confirm otherwise when you book.

We will explain any proposed additional work and its price before asking for your agreement. You do not have to accept a repair simply because an engineer recommends it. If you decline work needed for safe operation, the engineer will explain why the kettle should not be used.

To arrange a service, contact Halvard Home through our usual customer support channels. Have your purchase details available if you can, and describe any changes in how the kettle works. Tell us about leaking, unusual smells, unexpected switching behaviour or visible damage rather than leaving these concerns until the visit.

A service appointment is not a substitute for reporting a suspected safety fault. If the kettle appears unsafe, stop using it and disconnect it from the electricity supply if you can do so safely. Contact Halvard Home for

[P3] Goodwill and pricing rules
# Goodwill and pricing rules

## Brio kettle

### Goodwill and discounts

Use goodwill to put a customer’s experience right when something has gone wrong with their Brio kettle purchase or with the service they received. Listen to the concern, check the relevant order and service notes, and establish what outcome the customer is seeking before discussing a concession.

Staff may waive charges on the Brio kettle of up to £67.00 as goodwill. Check the charges actually due and explain clearly which charge you propose to waive. Do not describe a waived charge as a refund if the customer has not paid it. If payment has already been taken, check the refund process before making a commitment.

The largest discount staff may offer on the Brio kettle is 32%. Confirm the applicable selling price and check whether a promotion or an existing concession affects the proposed discount. Use the approved pricing process rather than working out an alternative arrangement outside the sales system.

Do not combine a goodwill waiver with a discount to get around these limits. Check the customer’s record for concessions already agreed on the same purchase. If the combined effect is unclear, or the requested outcome falls outside your authority, refer the case to your manager before promising anything.

Keep the reason for the decision factual and relevant. Record the

[P4] Engineer service manual (extract)
# Engineer service manual (extract)

## Brio kettle

### Internal repair limits

Only engineers authorised for kettle repairs may open the Brio kettle or replace internal parts. Confirm the reported fault and check the service history before starting work. Inspect the casing, lid, handle, base and supply lead for damage. Record any signs of overheating, water ingress or previous unauthorised work.

Disconnect the Brio kettle from the mains and allow it to cool before inspection or dismantling. Empty any remaining water and keep the work area dry. Follow the approved isolation procedure. Do not bypass protective devices, defeat interlocks or improvise connections to investigate a fault.

Engineers may fit parts to the Brio kettle worth up to £342.00 without approval. Check the combined value of the proposed parts against the current approved pricing record before fitting them. Include parts already fitted during the same repair when checking the allowance. Do not split the repair into separate jobs to avoid obtaining approval.

If the proposed parts exceed the allowance, stop and request approval through the service supervisor. Describe the fault, the work proposed and why the parts are needed. Record the decision in the job record before proceeding. Approval of parts expenditure does not authorise work outside your training or the approved repair procedure.

[P5] Escalation playbook
complaint. Keep customer details within approved systems and avoid copying sensitive information into informal messages. If supporting photographs or documents are relevant, explain how the customer can provide them through an approved channel.

The most a team leader may offer in compensation for the Brio kettle is £199.00. Do not promise compensation before it has been authorised. If the requested remedy falls outside the team leader’s authority, ask them to arrange further review rather than suggesting an exception is guaranteed.

Tell the customer who will review the complaint and how they will hear back. Avoid unsupported promises about the outcome or when a decision will be made. Keep responsibility for the handover until the receiving colleague confirms acceptance.

Record the decision, the reasons given and any agreed action. Explain the outcome plainly to the customer, including what happens next if they remain dissatisfied. Close the complaint only when the agreed actions are complete and the record reflects the outcome.

## Tessa dishwasher

### Escalating a complaint

When a customer complains about the Tessa dishwasher, listen carefully and confirm what has gone wrong, how it has affected them and what outcome they are seeking. Use clear, calm language. Acknowledge the inconvenience without guessing at the cause or promising an outcome that has not been approved.

Check the complaint record before taking

System's answer:
The highest compensation a team leader can offer for the Brio kettle is **£199.00**. [P5]

---

## 50. POL-SINGLE-006

Question: How much does Halvard Home charge per hour for work after the first hour?

Can the question be answered from the documents: yes

Reference answer: Labour after the first hour is charged at £55.00 an hour.

Passages given to the system:
[P1] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P2] Servicing and engineer visits
need your engineer visit, please let Halvard Home know so that we can cancel the booking and release the appointment. Please contact us directly rather than relying on a message passed through someone who is not acting on our behalf.

Cancel a visit at least 56 hours before it is due to avoid a charge. A visit cancelled later than that is charged at £47.00.

The cancellation deadline is based on the scheduled start of your visit, as shown in your booking confirmation. If your confirmation does not make this clear, please contact us so that we can explain which appointment details apply to your booking.

Use the contact details in your booking confirmation to request a cancellation. If you cannot find that confirmation, use the customer service contact details on the Halvard Home website. Please make clear that you want to cancel an engineer visit.

Give us the name on the booking, the address the engineer is due to attend and suitable contact details. Include any booking reference available to you. We may ask for further information if we cannot confidently identify the visit you want to cancel.

Please do not send payment card details or sensitive personal information with your cancellation request. We only need enough information to locate the booking, check that you are entitled to change it and confirm what you have asked us to do.

[P3] Warranty
controls. Let us know about access restrictions, pets or accessibility needs so that we can make suitable arrangements for the visit.

If a repair to the Orrin heat pump takes longer than 17 working days, Halvard Home lends a replacement. There is no loan charge. We will discuss delivery and setup with you, explain how to use the replacement safely and arrange its collection when it is no longer needed.

Please take reasonable care of the loaned replacement and use it in line with the instructions supplied. Tell us if it develops a fault or is damaged. Do not attempt to repair or alter it yourself. We will explain what happens next and make suitable arrangements.

Warranty repairs are carried out by engineers appointed by Halvard Home. The engineer will assess the fault, explain the work required and use suitable parts. We remain responsible for arranging the covered repair, including sourcing parts and coordinating the work, so you do not need to contact suppliers yourself.

If the engineer finds damage or work that falls outside the warranty, we will explain what has been found and why it is not covered. We will provide a clear quotation for any chargeable work and ask for your agreement before proceeding. You can decline that work.

Please do not arrange independent repairs on our behalf without our agreement. We cannot

[P4] Warranty
controls. Let us know about access restrictions, pets or accessibility needs so that we can make suitable arrangements for the visit.

If a repair to the Orrin heat pump takes longer than 3 working days, Halvard Home lends a replacement. There is no loan charge. We will discuss delivery and setup with you, explain how to use the replacement safely and arrange its collection when it is no longer needed.

Please take reasonable care of the loaned replacement and use it in line with the instructions supplied. Tell us if it develops a fault or is damaged. Do not attempt to repair or alter it yourself. We will explain what happens next and make suitable arrangements.

Warranty repairs are carried out by engineers appointed by Halvard Home. The engineer will assess the fault, explain the work required and use suitable parts. We remain responsible for arranging the covered repair, including sourcing parts and coordinating the work, so you do not need to contact suppliers yourself.

If the engineer finds damage or work that falls outside the warranty, we will explain what has been found and why it is not covered. We will provide a clear quotation for any chargeable work and ask for your agreement before proceeding. You can decline that work.

Please do not arrange independent repairs on our behalf without our agreement. We cannot

[P5] Servicing and engineer visits
behalf of Halvard Home, keep your door closed and contact customer support using details you already trust. Do not allow access simply because a visitor says a repair has been arranged.

The engineer will assess the reported issue and explain their findings in plain language. They may need to carry out checks before deciding what work is suitable. A visit does not guarantee that a repair can be completed, particularly where parts, specialist support or safer access are required.

If the engineer recommends work that is not covered by your existing agreement or applicable guarantee, they will explain the charges before seeking your consent. You may decline the proposed work. We will explain whether the call-out charge remains payable under the terms agreed when you booked.

We expect customers and engineers to treat each other respectfully. An engineer may stop work or leave if they encounter threatening behaviour, unsafe conditions or circumstances that prevent a proper assessment. Customer support will discuss what happened and whether a visit can be arranged under suitable conditions.

Please contact us if your circumstances change or you no longer need the appointment. Tell us if the fault changes, access becomes difficult or nobody will be available to admit the engineer. We will explain the options available and any relevant booking terms before making changes.

After the visit, we will provide a record of the assessment and any work

System's answer:
The passages do not state Halvard Home’s hourly charge for work after the first hour.
