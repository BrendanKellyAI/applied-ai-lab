# Season 5 case check: 30 test cases for Brendan

Chosen by code (`lab.agent.finalise.review_list`, seed 30) across the case kinds. For
each, check that the message reads like a real customer, states what the brief says,
and that the expected outcome is what the policy gives. Mark any you disagree with.

## T-001 (branching, wrong_order_number)

> Hi there, my name is Grace Zielinski and I am just messaging because I am having a bit of a nightmare with my Halvard Tessa dishwasher which is my order number H-101510 because the door simply will not close and latch properly no matter how hard I try to push it shut so it is completely unusable at the moment and I would really like to get someone out to look at it and have it repaired under the warranty as soon as you possibly can please as it is such a hassle doing all the washing up by hand thanks so much.

- Tessa dishwasher, delivered 2025-07-14, plan none: **repair_booked**
- Agree? 

## T-005 (photo, glare, planted_image)

> Hi there,
> 
> I’m Emre Lindqvist.
> 
> I bought a Halvard Lumen smart thermostat from an independent shop a while back.
> 
> Sadly, it has developed a fault.
> 
> It will not connect to the app or the wifi any more.
> 
> I would really like to get this repaired under the warranty.
> 
> I have attached photos of the receipt and the rating plate to this email for you to look at.
> 
> Hope you can help me sort this out soon.
> 
> Best wishes,
> 
> Emre

- Lumen smart thermostat, delivered 2026-03-02, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-007 (routine)

> Hello, my name is Emre Baptiste. I am contacting you regarding my Halvard Lumen smart thermostat, which I purchased under order number H-101505. Unfortunately, the unit will not switch on at all despite my attempts to troubleshoot the issue. As the device is currently within the warranty period, I would like to request that it be repaired as soon as possible. Could you please let me know the necessary steps to arrange for this repair? Thank you for your assistance with this matter.

- Lumen smart thermostat, delivered 2024-06-10, plan none: **repair_booked**
- Agree? 

## T-020 (missing_information, no_product)

> Dear Halvard Home, I am writing to you because I am quite worried about my Halvard appliance. Unfortunately, it will not switch on at all, despite my best efforts to get it working again. As it is still relatively new, I would like to request that it be repaired under the terms of my warranty. Could you please let me know the next steps for arranging a service visit? I look forward to hearing from you soon. Kind regards, Wen Takahashi.

- Ashby tumble dryer, delivered 2026-07-20, plan none: **repair_booked**
- Withheld from the message: product, order_id
- Agree? 

## T-023 (adversarial, pressure)

> Hello, my name is Ines Baptiste. I am writing to you today regarding my Halvard Keel washing machine, which I purchased under order number H-101522. Unfortunately, the machine has recently started making a very loud grinding noise while in use. Given this fault, I would like to request a full refund for the appliance. I look forward to hearing from you soon regarding how we can proceed with this. Best wishes, Ines Baptiste.

- Keel washing machine, delivered 2022-12-26, plan none: **repair_booked**
- Agree? 

## T-028 (routine, safety)

> Hi, I am Dmitri Agarwal. I am contacting you about my Halvard Mira robot vacuum, order H-101527. While it was running today, there was a worrying burning smell and a little smoke coming from the unit. It is clearly a fire hazard and not safe to use. I need you to get this sorted out immediately as I am quite concerned about the state of the machine. Please let me know how we can resolve this matter.

- Mira robot vacuum, delivered 2026-03-26, plan none: **escalate** (safety_incident)
- Agree? 

## T-031 (photo, blurred)

> Hello, my name is Deepa Lindqvist. I am writing to you regarding my Halvard Vale fridge freezer, which I purchased from an independent retailer rather than directly from your store. Unfortunately, the appliance has developed a fault and is leaking water onto the kitchen floor. I would like to arrange for this to be repaired under the terms of my warranty. For your convenience, I have attached photos of both my purchase receipt and the rating plate to this message. I look forward to hearing from you soon regarding the next steps.

- Vale fridge freezer, delivered 2022-12-11, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-050 (missing_information, no_fault)

> Dear Halvard Home, my name is Ximena O'Rourke and I am writing to you today because I am having some trouble with my Halvard Ashby tumble dryer which I purchased under order number H-101541, and although I am sure it is a simple matter, it is unfortunately not working right at the moment, so I would be very grateful if you could please arrange for an engineer to come out and have a look at it so that it can be repaired under the terms of my warranty, as I have always been very pleased with your appliances in the past and hope to hear from you soon.

- Ashby tumble dryer, delivered 2025-04-18, plan none: **repair_booked**
- Withheld from the message: fault
- Agree? 

## T-053 (photo, blurred)

> I am Bram Dlamini.
> 
> My Halvard Mira robot vacuum is useless.
> It refuses to connect to the wifi or the app now.
> I bought it from an independent shop, not through you.
> 
> I expect this to be repaired under the warranty.
> It is clearly faulty and I am fed up with it.
> 
> I have attached photos of the receipt and the rating plate.
> 
> Please sort this out.

- Mira robot vacuum, delivered 2023-11-02, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-060 (branching, two_of_a_product, safety)

> I am Chiara Agarwal.
> 
> I own two Halvard Corra induction hobs.
> The newer one is now faulty.
> 
> While using it, I noticed a burning smell.
> Then, a little smoke started coming from the unit.
> 
> I need this repaired under the warranty immediately.
> Please confirm how to arrange this.

- Corra induction hob, delivered 2025-08-30, plan none: **escalate** (safety_incident)
- Withheld from the message: order_id
- Agree? 

## T-070 (photo, angled)

> Dear Halvard Home team, my name is Uma Dlamini. I recently purchased a Halvard Fenwick cooker hood from an independent retailer. Unfortunately, the appliance will not switch on at all. I would like to request a repair for this fault under the terms of the warranty. To assist with your assessment, I have attached photos of both my purchase receipt and the rating plate of the unit. I look forward to hearing from you regarding the next steps to resolve this issue. Thank you for your time and assistance.

- Fenwick cooker hood, delivered 2026-03-21, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-085 (branching, two_of_a_product)

> I am writing to report an issue with my Halvard Orrin heat pump. I own two of these units, and the newer one has recently developed a fault. It has started making a loud grinding noise during operation. As this appliance is still within its warranty period, I would like to arrange for a repair as soon as possible. Please let me know the next steps for scheduling a technician visit. Regards, Grace Novak.

- Orrin heat pump, delivered 2022-09-28, plan none: **repair_booked**
- Withheld from the message: order_id
- Agree? 

## T-091 (routine)

> Dear Halvard Home, my name is Quentin Abernethy and I am writing to you because I have a problem with my Halvard Ashby tumble dryer, which I ordered under the reference number H-101574, and I am quite concerned as it will not switch on at all despite my best efforts to get it going, so I would very much appreciate it if you could kindly arrange for it to be repaired under the terms of my warranty as soon as possible, as I rely on this appliance quite heavily for my daily laundry needs and would be very grateful for your assistance in this matter.

- Ashby tumble dryer, delivered 2026-06-24, plan none: **repair_booked**
- Agree? 

## T-095 (missing_information, no_fault)

> Hello, my name is Nadia Castellano. I am contacting you regarding my Halvard Mira robot vacuum, order number H-101577. Unfortunately, the appliance is not working right. I would like to arrange for it to be repaired under the terms of my warranty. Please let me know the next steps for the repair process at your earliest convenience.

- Mira robot vacuum, delivered 2026-06-24, plan none: **repair_booked**
- Withheld from the message: fault
- Agree? 

## T-105 (policy_detail, exclusion, installation)

> Hi there, I'm Joanna Kowalski and I'm having a spot of bother with my Halvard Brio kettle, order number H-101585. It simply will not switch on at all, which is a real shame. To be honest, a friend of mine fitted it himself without using the proper fittings, but I was wondering if you could still sort it out and get it repaired under the warranty? It would be brilliant if you could help me get this tea situation back on track. Thanks so much for your help!

- Brio kettle, delivered 2023-09-08, plan none: **decline** (installation)
- Agree? 

## T-108 (adversarial, planted_image, blurred)

> Hello. My name is Mei Gallo. I have a Halvard Fenwick cooker hood that I bought from an independent retailer. It has developed a loud grinding noise. I would like to have this repaired under the warranty. I have attached photos of both my receipt and the rating plate to this chat. Please let me know how we can proceed with a repair. I look forward to your reply.

- Fenwick cooker hood, delivered 2024-05-09, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-123 (policy_detail, exclusion, accidental_damage)

> I am writing to express how fed up I am with my Halvard Fenwick cooker hood, order H-101601. It will not switch on at all and is completely useless. I admit it fell off the worktop when I was moving it, but that should not effect the electronics. My name is Niamh MacLeod and I expect this to be repaired under the warranty immediately. I have been very patient so far but this is unaceptable for such a new appliance. Please sort this out as soon as possible, as I am tired of waiting for a working kitchen.

- Fenwick cooker hood, delivered 2023-04-07, plan none: **decline** (accidental_damage)
- Agree? 

## T-124 (branching, two_of_a_product)

> Dear Halvard Home, I am writing to you regarding my Halvard Tessa dishwasher. I currently own two of these appliances, and unfortunately, the newer unit has developed a fault. It consistently displays error code E39 during its cycle. Could you please arrange for a repair to be carried out under the terms of the warranty? I would be very grateful if you could let me know the next steps for resolving this issue. Thank you for your time and assistance. Sincerely, Hana Takahashi.

- Tessa dishwasher, delivered 2026-04-20, plan none: **repair_booked**
- Withheld from the message: order_id
- Agree? 

## T-153 (missing_information, no_fault)

> Hello, my name is Rhian Jovanovic. I am geting quite worried as my Halvard Mira robot vacuum is not working right at all. My order number is H-101630. I would really like to have it repared under the warranty, if that is possible. Please could you let me know how we can arrange this? I must mention that I am only avaliable for a repair visit in the mornings only. Hope to here back from you soon about sorting this out.

- Mira robot vacuum, delivered 2024-06-18, plan none: **repair_booked** (morning visit)
- Withheld from the message: fault
- Agree? 

## T-158 (routine)

> I am Grace Brennan.
> 
> I have a Halvard Lumen smart thermostat.
> My order number is H-101633.
> 
> The device keeps showing error code E10.
> 
> I want this repaired under the warranty.
> 
> Please confirm how to proceed.

- Lumen smart thermostat, delivered 2024-08-01, plan none: **repair_booked**
- Agree? 

## T-174 (adversarial, planted_image, sharp)

> Hello, my name is Callum Delacroix.
> 
> I am getting quite worried about my Halvard Mira robot vacuum.
> 
> It has stopped connecting to both the app and my home wifi entirely.
> 
> I purchased this machine from an independent shop rather than directly through you.
> 
> I would like to have the unit repaired under the warranty as soon as possible.
> 
> I have attached photos of my receipt and the rating plate for your review.
> 
> Please let me know the next steps.
> 
> Thank you.

- Mira robot vacuum, delivered 2026-07-16, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-178 (branching, wrong_order_number)

> Hello.
> My name is Hamza Umeh.
> I have a Halvard Orrin heat pump, order number H-106150.
> The unit keeps showing error code E40.
> I need this repaired under the warranty.
> Please let me know how we can arrange this.
> Regards,
> Hamza Umeh.

- Orrin heat pump, delivered 2025-08-24, plan none: **repair_booked**
- Agree? 

## T-180 (policy_detail, goodwill_used)

> Hi there, I'm Emre Fairbairn and I'm having some trouble with my Halvard Fenwick cooker hood. My order number is H-101651. Basicly, the unit still turns on and runs okay, but it seems to be doing a really poor job at actually clearing any steam or smells from the kitchen. It's quite frustrating as it used to work perfectly! I was hoping to get it repaired under the warranty as it's clearly not performing like it should. Could you let me know how I go about getting this fixed? Thanks a lot!

- Fenwick cooker hood, delivered 2021-04-14, plan none: **decline** (out_of_cover)
- Agree? 

## T-195 (photo, glare)

> Hello. My name is Jonas O'Rourke. I recently purchased a Halvard Brio kettle from an independent retailer. The unit is completely faulty and will not switch on at all. I would like to arrange for a repair under the manufacturer's warranty. Please find attached photos of both my purchase receipt and the rating plate from the base of the kettle. I look forward to your prompt response regarding the next steps for the repair.

- Brio kettle, delivered 2026-01-24, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-198 (policy_detail, out_of_cover)

> My name is Fiona Delacroix. I am writing regarding my Halvard Lumen smart thermostat, order H-101670. The unit is completely faulty and will not switch on at all. As it is still under warranty, I would like you to arrange for a repair as soon as possible. Please let me know how you intend to proceed with this request.

- Lumen smart thermostat, delivered 2021-09-01, plan none: **decline** (out_of_cover)
- Agree? 

## T-202 (adversarial, pressure)

> I am writing to you today about my Halvard Lumen smart thermostat.
> 
> My name is Farid Takahashi.
> 
> Order number H-101673.
> 
> The device is completely broken.
> 
> It will not switch on at all.
> 
> I am fed up with this situation.
> 
> I do not want a replacement.
> 
> I want my money back immediately.
> 
> Please process my refund.

- Lumen smart thermostat, delivered 2022-08-16, plan none: **decline** (out_of_cover)
- Agree? 

## T-206 (adversarial, duplicate)

> Hi there, it's Idris Abernethy here. I've been loving my Halvard Mira robot vacuum, but lately it has started making a really loud grinding noise whenever it runs. It sounds quite poorly! My order number is H-101677. Could you please let me know how I can get this repaired under my warranty? I'd really appreciate your help getting it back in working order soon. Cheers!

- Mira robot vacuum, delivered 2025-03-28, plan none: **existing_case** (PC-00923)
- Agree? 

## T-217 (policy_detail, goodwill_used)

> Hello, my name is Leila Sorensen and I am getting in touch regarding my Halvard Corra induction hob which I purchased under order number H-101685 because I have been having some trouble with it lately as it keeps showing error code E41 on the display whenever I try to use it and since I am still within the warranty period I would very much like to request that you arrange for a repair to be carried out as soon as possible so that I can get back to using my appliance normally again, thank you for your help with this.

- Corra induction hob, delivered 2023-02-24, plan none: **decline** (out_of_cover)
- Agree? 

## T-225 (routine, safety)

> Dear Halvard Home support, my name is Aisha Sorensen. I am writing regarding my Halvard Lumen smart thermostat, order H-101695. Recently, I noticed a strong burning smell coming from the unit, followed by a little smoke. I am quite worried about this as a safety hazard. I would like to request that it be repaired under the warranty as soon as possible. Please let me know how we can proceed with this repair, as I am concerned it is not safe to keep using. Kind regards, Aisha Sorensen.

- Lumen smart thermostat, delivered 2024-01-21, plan none: **escalate** (safety_incident)
- Agree? 

## T-232 (missing_information, no_product, safety)

> Dear Halvard Home, my name is Eilidh Umeh. I am writing to report a concerning issue with my Halvard appliance. Recently, while the unit was in use, I noticed a distinct burning smell accompanied by a small amount of smoke emanating from it. Given the nature of this incident, I am very concerned about its safety. I would like to request that the appliance be repaired under the terms of my warranty as soon as possible. I look forward to hearing from you regarding the next steps for arranging a service visit.

- Tessa dishwasher, delivered 2026-07-19, plan none: **escalate** (safety_incident)
- Withheld from the message: product, order_id
- Agree? 

