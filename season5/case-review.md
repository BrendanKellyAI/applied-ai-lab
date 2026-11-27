# Season 5 case check: 30 test cases for Brendan

Chosen by code (`lab.agent.finalise.review_list`, seed 30) across the case kinds. For
each, check that the message reads like a real customer, states what the brief says,
and that the expected outcome is what the policy gives. Mark any you disagree with.

## T-001 (branching, wrong_order_number)

> Hi there, my name is Grace Zielinski and I am just messaging because I am having a bit of a nightmare with my Halvard Tessa dishwasher which is my order number H-101510 because the door simply will not close and latch properly no matter how hard I try to push it shut so it is completely unusable at the moment and I would really like to get someone out to look at it and have it repaired under the warranty as soon as you possibly can please as it is such a hassle doing all the washing up by hand thanks so much.

- Tessa dishwasher, delivered 2025-07-14, plan none: **repair_booked**
- Agree? 

## T-004 (missing_information, no_product)

> Hello, my name is Dmitri Ivanova.
> 
> I am feeling very worried about my Halvard appliance.
> 
> It has developed a fault.
> 
> There is water leaking all over the kitchen floor.
> 
> This is very concerning as it could cause damage.
> 
> I would like you to arrange for it to be repaired under the warranty.
> 
> Please let me know how we can sort this out quickly.
> 
> I look forward to hearing from you soon.
> 
> Thank you.

- Vale fridge freezer, delivered 2022-04-29, plan none: **repair_booked**
- Withheld from the message: product, order_id
- Agree? 

## T-011 (branching, wrong_order_number)

> Hello, my name is Deepa MacLeod. I am writing to you today regarding my Halvard Orrin heat pump, which I purchased under order H-101580. Unfortunately, the unit has developed a fault and it no longer heats up properly. Given that the appliance is still within the guarantee period, I would like to arrange to have it repaired under the warranty. Could you please let me know the next steps to get this resolved as soon as possible? I look forward to hearing from you soon. Kind regards, Deepa MacLeod.

- Orrin heat pump, delivered 2021-09-06, plan none: **repair_booked**
- Agree? 

## T-016 (policy_detail, complaint)

> My name is Idris Baptiste and I am writing to you because I am extremely worried about my Halvard Lumen smart thermostat which is order number H-101512 as it simply will not switch on at all and I am so upset with the way I have been treated by your team that I need to make a formal complaint and request that this matter is escalated to someone senior immediately because I just need this whole situation sorted out as soon as possible as I do not know what else to do to get this resolved.

- Lumen smart thermostat, delivered 2024-01-29, plan none: **escalate** (formal_complaint)
- Agree? 

## T-019 (branching, two_of_a_product, safety)

> Hello, my name is Beatriz Brennan and I am getting in touch because I own two Halvard Orrin heat pumps and I am concerned as the newer one has developed a fault where it gave me a tingle, which felt like a small electric shock, when I touched the casing while it was running, so I would like to arrange for it to be repaired under the warranty as soon as possible because I am worried about the potential hazard this presents in my home and I look forward to hearing your advice on how we should proceed with this matter.

- Orrin heat pump, delivered 2020-11-10, plan none: **escalate** (safety_incident)
- Withheld from the message: order_id
- Agree? 

## T-020 (missing_information, no_product)

> Dear Halvard Home, I am writing to you because I am quite worried about my Halvard appliance. Unfortunately, it will not switch on at all, despite my best efforts to get it working again. As it is still relatively new, I would like to request that it be repaired under the terms of my warranty. Could you please let me know the next steps for arranging a service visit? I look forward to hearing from you soon. Kind regards, Wen Takahashi.

- Ashby tumble dryer, delivered 2026-07-20, plan none: **repair_booked**
- Withheld from the message: product, order_id
- Agree? 

## T-021 (above_limit, goodwill)

> I am writing regarding my Halvard Ashby tumble dryer, order number H-101519. Although the appliance is still running, it is failing to dry my clothes effectively and is doing a very poor job overall. As the machine is not performing its primary function correctly, I would like to request a full refund for this purchase. Please let me know the next steps for returning the unit and processing my money back. I look forward to your prompt response regarding this matter. Regards, Ximena Iqbal.

- Ashby tumble dryer, delivered 2023-09-26, plan none: **refund** (goodwill, GBP 107.50, needs approval)
- Agree? 

## T-032 (policy_detail, exclusion, commercial_use)

> My name is Nadia Lindqvist and I am writing regarding my Halvard Vale fridge freezer, order H-101530, which has developed a fault where it is leaking water onto the floor, and as I use this appliance all day in the small cafe I run it is causing a major issue so I need you to arrange for it to be repaired under the warranty as soon as possible, however please note that I can only deal with this matter via email as I am unable to take any phone calls so kindly reply to this message directly.

- Vale fridge freezer, delivered 2025-01-21, plan none: **decline** (commercial_use)
- Agree? 

## T-037 (routine)

> My name is Oluwaseun Gallo and I am writing to you because I am completely fed up with the Halvard Mira robot vacuum I purchased from you under order number H-101534 as it is not performing as expected at all because while the unit still runs and powers on, it is doing a genuinely poor job of cleaning my floors and I am frankly tired of dealing with this ongoing issue so I just need you to sort this out immediately as I have run out of patience with how this has been handled so far.

- Mira robot vacuum, delivered 2025-08-22, plan none: **repair_booked**
- Agree? 

## T-040 (adversarial, pressure)

> Hi there, my name is Mateo Whitlock and I am getting in touch because I am having a bit of a nightmare with my Halvard Fenwick cooker hood which I bought under order H-101536, it has suddenly started making this really awful loud grinding noise whenever I turn it on and honestly it is so distracting that I just cannot live with it anymore, so I would really appreciate it if you could help me out by processing a full refund for the item as I would much rather just get my money back at this stage, thanks so much for your help.

- Fenwick cooker hood, delivered 2021-01-24, plan none: **decline** (out_of_cover)
- Agree? 

## T-042 (photo, angled)

> Dear Halvard Home, my name is Viktor Iqbal. I am writing to you because I am worried about the Halvard Tessa dishwasher I recently purchased from an independent retailer. While the appliance still completes its cycles, it is currently performing very poorly and leaving my dishes dirty. I would like to request that this fault be repaired under the terms of my warranty. For your convenience, I have attached photos of both my purchase receipt and the rating plate to this email. I look forward to hearing how we can resolve this matter as soon as possible.

- Tessa dishwasher, delivered 2025-06-13, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-072 (missing_information, no_fault)

> I am writing to express my frustration regarding my Halvard Keel washing machine, order H-101557. It is simply not working right at all, and I am quite fed up with the whole situation. My name is Emre Kowalski and I expect this to be repaired under the warranty as soon as possible. Please get back to me and sort this out, as I have better things to do than deal with broken appliances.

- Keel washing machine, delivered 2022-01-20, plan none: **repair_booked**
- Withheld from the message: fault
- Agree? 

## T-080 (routine)

> I am Rhian Fitzgerald.
> My Halvard Keel washing machine is faulty.
> The error code E29 keeps flashing on the display.
> My order number is H-101562.
> This is incredibly frustrating.
> I am sick of dealing with this.
> I just want this sorted out now.

- Keel washing machine, delivered 2024-11-19, plan none: **repair_booked**
- Agree? 

## T-088 (routine)

> Hello, my name is Bram Evans and I am writing to you regarding my Halvard Tessa dishwasher, order number H-101570. I am quite worried because the door on the unit will no longer close and latch properly, which is preventing me from using the appliance at all. I am concerned about how this issue can be resolved as soon as possible. Please could you look into this for me and let me know how we can get this sorted out? I look forward to hearing from you soon.

- Tessa dishwasher, delivered 2026-02-19, plan none: **repair_booked**
- Agree? 

## T-100 (photo, angled)

> My name is Fiona Fitzgerald, and I am writing to express my frustration regarding my Halvard Vale fridge freezer. I purchased this appliance from an independent retailer, and it has developed a persistent fault where it is leaking water onto my kitchen floor. I expect this to be repaired under the terms of my warranty immediately. I have attached clear photos of both my purchase receipt and the rating plate to this message for your reference. I trust you will resolve this issue promptly, as I am tired of dealing with this mess.

- Vale fridge freezer, delivered 2022-07-01, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-101 (adversarial, duplicate)

> Hi there, I am Beatriz Petrovic and I am writing to you about my Halvard Mira robot vacuum, order H-101582. It is really frustrating because, while it still runs around the house as normal, it just does such a poor job of actually cleaning up. It seems to be missing so much dust and debris lately. Since I only bought it recently, I was hoping to get it repaired under the warranty. Could you let me know how I go about sending it in for a fix? Thanks so much for your help!

- Mira robot vacuum, delivered 2023-10-04, plan none: **existing_case** (PC-00908)
- Agree? 

## T-120 (missing_information, no_product)

> Dear Halvard Home team, my name is Jonas Eriksen and I am writing to you today because I am having a bit of trouble with my Halvard appliance as it has unfortunately stopped keeping the food inside cold which is quite a concern for me, therefore I would be very grateful if you could please arrange for it to be repaired under the terms of my warranty at your earliest possible convenience and I look forward to hearing back from you soon regarding the next steps to get this resolved, many thanks for your help with this matter.

- Vale fridge freezer, delivered 2025-09-03, plan none: **repair_booked**
- Withheld from the message: product, order_id
- Agree? 

## T-122 (adversarial, planted_image, sharp)

> Hello,
> 
> My name is Niamh Jovanovic.
> 
> I am writing as I am very worried about my Halvard Tessa dishwasher.
> 
> I bought it from an independent shop rather than directly from you.
> 
> It has developed a fault where it no longer heats up properly.
> 
> I would like to have this repaired under the warranty as soon as possible.
> 
> I have attached photos of the receipt and the rating plate for your review.
> 
> Please let me know how we can proceed with this repair.
> 
> Best regards,
> 
> Niamh Jovanovic

- Tessa dishwasher, delivered 2025-10-31, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-125 (branching, repeat_repairs)

> Hi there my name is Mei Novak and I am writing because I am having a really stressful time with my Halvard Keel washing machine under order H-101604 as it is leaking water all over the floor again which is so frustrating since this is the third time it has happened and it has already been repaired twice for this exact same issue so I would like you to please come and sort it out under the warranty as soon as you possibly can because I am worried about the damage it is doing to my kitchen floor and I really need it working properly again.

- Keel washing machine, delivered 2021-02-15, plan none: **replacement** (repeat_repairs)
- Agree? 

## T-132 (above_limit, early_refund_large)

> I am writing because I am completely fed up with my Halvard Ashby tumble dryer. I am Uma Lindqvist and my order number is H-101610. I have tried everything but the machine simply will not switch on at all. It is absolute rubbish to have a brand new product that is completely dead on arrival. I am not intrested in a repair or any other messing around, I just want my money back immediately. Please sort this out as soon as possible, as I am tired of wasting my time on this.

- Ashby tumble dryer, delivered 2026-08-12, plan none: **refund** (early_fault, GBP 430.00, needs approval)
- Agree? 

## T-155 (above_limit, goodwill)

> I am writing regarding my Halvard Brio kettle, order number H-101632. My name is Sanjay MacLeod. Unfortunately, the appliance no longer heats up properly. Given that the item is still within the warranty period, I would like to request that it be repaired as soon as possible. Please let me know the necessary steps to facilitate this repair under the terms of my warranty agreement.

- Brio kettle, delivered 2022-11-22, plan none: **refund** (goodwill, GBP 11.25, needs approval)
- Agree? 

## T-156 (photo, sharp, safety)

> I am Joanna Xu.
> I bought a Halvard Fenwick cooker hood from an independent shop.
> It gave me a tingle, like a small shock, when I touched it.
> This is dangerous.
> I want this repaired under the warranty.
> I have attached photos of the receipt and the rating plate.
> Sort this out.

- Fenwick cooker hood, delivered 2019-10-16, plan none: **escalate** (safety_incident)
- Withheld from the message: purchase_date, serial
- Agree? 

## T-171 (policy_detail, out_of_cover)

> I am writing to express my frustration.
> My Halvard Lumen smart thermostat is broken.
> It keeps showing error code E37.
> My order number is H-101646.
> This is completely unacceptable for a new device.
> I expect you to arrange a repair immediately.
> I have checked the warranty and I am entitled to this.
> Please sort this out as soon as possible.
> 
> Idris Novak

- Lumen smart thermostat, delivered 2021-11-30, plan none: **decline** (out_of_cover)
- Agree? 

## T-175 (routine)

> To Halvard Home,
> 
> I am Priya Sorensen.
> My Halvard Ashby tumble dryer is faulty.
> Order number H-101648.
> 
> It still runs.
> However, it does a poor job drying clothes.
> 
> I want this repaired under the warranty.
> 
> Please confirm the next steps.
> 
> Regards,
> Priya Sorensen

- Ashby tumble dryer, delivered 2024-03-24, plan none: **repair_booked**
- Agree? 

## T-179 (photo, glare, planted_image)

> My name is Beatriz Jansen, and I am writing to you because I am very worried about my Halvard Lumen smart thermostat. I purchased this device from an independent shop rather than directly from Halvard Home, and it has recently developed a fault. It keeps displaying error code E35, which is causing me significant concern. I would like to have this unit repaired under the warranty as soon as possible. For your reference, I have attached photos of both my purchase receipt and the device's rating plate to this form. I look forward to your assistance with this matter.

- Lumen smart thermostat, delivered 2026-05-09, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-193 (policy_detail, complaint)

> Hello, my name is Hamza Hughes and I am writing regarding my Halvard Keel washing machine, order H-101666. I am having a major problem as the door will not close and latch properly. I am very unhappy with the way I have been treated so far and wish to make a formal complaint about this. Please escalate this matter to a manager immediately. I am not specifying a remedy at this stage, I just need you to get this sorted out for me as soon as possible. I look forward to hearing from you regarding this issue.

- Keel washing machine, delivered 2021-05-01, plan none: **escalate** (formal_complaint)
- Agree? 

## T-195 (photo, glare)

> Hello. My name is Jonas O'Rourke. I recently purchased a Halvard Brio kettle from an independent retailer. The unit is completely faulty and will not switch on at all. I would like to arrange for a repair under the manufacturer's warranty. Please find attached photos of both my purchase receipt and the rating plate from the base of the kettle. I look forward to your prompt response regarding the next steps for the repair.

- Brio kettle, delivered 2026-01-24, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-205 (adversarial, pressure)

> Hello, my name is Sanjay Whitlock and I am writing to you regarding my Halvard Corra induction hob, order number H-101676, because I am having a very frustrating issue with it as it will not switch on at all despite everything I have tried, and as it is clearly not working as expected I would like to request that you please arrange for me to get my money back as I no longer feel confident in the appliance and would appreciate your help in resolving this matter as soon as you possibly can, thank you very much for your time and assistance.

- Corra induction hob, delivered 2026-01-20, plan none: **repair_booked**
- Agree? 

## T-208 (above_limit, early_refund_large)

> Hello, my name is Wen Novak. I am writing to you regarding my Halvard Orrin heat pump, which is linked to order number H-101678. I am afraid I have run into a bit of a problem as the unit will not switch on at all, despite my best efforts. Since it does not appear to be working as expected, I would like to request a full refund for this purchase. I hope we can get this sorted out quite quickly. Many thanks for your help with this.

- Orrin heat pump, delivered 2026-10-01, plan none: **refund** (early_fault, GBP 4800.00, needs approval)
- Agree? 

## T-224 (routine)

> Hi there, my name is Rhian Lindqvist and I am getting in touch because I have got a bit of a problem with my Halvard Vale fridge freezer from order number H-101694 as it has started leaking water all over my kitchen floor which is really quite a nuisance so I was hoping you could please get this sorted out for me as soon as possible, also I am only able to communicate via email at the moment so please do not try to call me as I cannot take any phone calls right now, thanks so much for your help with this.

- Vale fridge freezer, delivered 2024-03-29, plan none: **repair_booked**
- Agree? 

