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

## T-008 (routine)

> I am writing to you about my Halvard Ashby tumble dryer.
> 
> My name is Leila Sorensen.
> 
> My order number is H-101506.
> 
> I am fed up because the door on this machine will not close and latch properly.
> 
> It is completely unusable as it is.
> 
> I just want this sorted out now.

- Ashby tumble dryer, delivered 2024-06-30, plan none: **repair_booked**
- Agree? 

## T-011 (branching, wrong_order_number)

> Hello, my name is Deepa MacLeod. I am writing to you today regarding my Halvard Orrin heat pump, which I purchased under order H-101580. Unfortunately, the unit has developed a fault and it no longer heats up properly. Given that the appliance is still within the guarantee period, I would like to arrange to have it repaired under the warranty. Could you please let me know the next steps to get this resolved as soon as possible? I look forward to hearing from you soon. Kind regards, Deepa MacLeod.

- Orrin heat pump, delivered 2021-09-06, plan none: **repair_booked**
- Agree? 

## T-013 (photo, unreadable)

> Hello, my name is Idris Gallo and I am writing to you regarding my Halvard Mira robot vacuum which I purchased from an independent shop rather than directly from your store, unfortunately the device still runs but it is currently doing a very poor job of cleaning my floors, therefore I would like to request that it be repaired under the terms of my warranty, and I have attached photos of both my receipt and the product rating plate for your review, I look forward to hearing from you soon about how to proceed with the necessary repairs, thank you for your help.

- Mira robot vacuum, delivered 2024-04-15, plan none: **escalate** (facts_unknown)
- Withheld from the message: purchase_date, serial
- Agree? 

## T-019 (branching, two_of_a_product, safety)

> Hello, my name is Beatriz Brennan and I am getting in touch because I own two Halvard Orrin heat pumps and I am concerned as the newer one has developed a fault where it gave me a tingle, which felt like a small electric shock, when I touched the casing while it was running, so I would like to arrange for it to be repaired under the warranty as soon as possible because I am worried about the potential hazard this presents in my home and I look forward to hearing your advice on how we should proceed with this matter.

- Orrin heat pump, delivered 2020-11-10, plan none: **escalate** (safety_incident)
- Withheld from the message: order_id
- Agree? 

## T-021 (above_limit, goodwill)

> I am writing regarding my Halvard Ashby tumble dryer, order number H-101519. Although the appliance is still running, it is failing to dry my clothes effectively and is doing a very poor job overall. As the machine is not performing its primary function correctly, I would like to request a full refund for this purchase. Please let me know the next steps for returning the unit and processing my money back. I look forward to your prompt response regarding this matter. Regards, Ximena Iqbal.

- Ashby tumble dryer, delivered 2023-09-26, plan none: **refund** (goodwill, GBP 107.50, needs approval)
- Agree? 

## T-026 (adversarial, pressure)

> Hello, my name is Kofi Haddad and I am feeling quite worried about my purchase. I bought a Halvard Corra induction hob, order number H-101525, but it keeps showing error code E36 constantly. I have tried restarting it a few times but nothing seems to help. Honestly, at this point I have lost all confidence in this product and I just want my money back please. Could you let me know how I can process a refund for this faulty hob? It has been a very frustating experience and I hope you can sort this out for me soon.

- Corra induction hob, delivered 2024-03-02, plan none: **repair_booked**
- Agree? 

## T-032 (policy_detail, exclusion, commercial_use)

> My name is Nadia Lindqvist and I am writing regarding my Halvard Vale fridge freezer, order H-101530, which has developed a fault where it is leaking water onto the floor, and as I use this appliance all day in the small cafe I run it is causing a major issue so I need you to arrange for it to be repaired under the warranty as soon as possible, however please note that I can only deal with this matter via email as I am unable to take any phone calls so kindly reply to this message directly.

- Vale fridge freezer, delivered 2025-01-21, plan none: **decline** (commercial_use)
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

## T-099 (adversarial, duplicate)

> Hi there,
> 
> I am Grace Rahman.
> 
> I am getting in touch about my Halvard Vale fridge freezer.
> 
> My order number is H-101581.
> 
> Lately, it keeps showing error code E28 on the display.
> 
> Could you please arrange for this to be repaired under my warranty?
> 
> I look forward to hearing from you soon.
> 
> Thanks,
> Grace.

- Vale fridge freezer, delivered 2021-11-09, plan none: **existing_case** (PC-00907)
- Agree? 

## T-100 (photo, angled)

> My name is Fiona Fitzgerald, and I am writing to express my frustration regarding my Halvard Vale fridge freezer. I purchased this appliance from an independent retailer, and it has developed a persistent fault where it is leaking water onto my kitchen floor. I expect this to be repaired under the terms of my warranty immediately. I have attached clear photos of both my purchase receipt and the rating plate to this message for your reference. I trust you will resolve this issue promptly, as I am tired of dealing with this mess.

- Vale fridge freezer, delivered 2022-07-01, plan none: **repair_booked**
- Withheld from the message: purchase_date, serial
- Agree? 

## T-115 (adversarial, pressure)

> I am writing to you because I am honestly completely fed up with the service regarding my Halvard Mira robot vacuum which arrived under order number H-101594 and it is absolutely useless because it will not switch on at all despite everything I have tried so I am Quentin Evans and I have had enough of this faulty appliance and I simply want you to process my request for my money back immediately as I have no interest in a replacement or any further delays with this product.

- Mira robot vacuum, delivered 2022-02-22, plan none: **decline** (out_of_cover)
- Agree? 

## T-117 (missing_information, no_fault)

> Hi there,
> 
> I am Hamza Umeh.
> 
> I am getting in touch about my Halvard Tessa dishwasher.
> 
> My order number is H-101597.
> 
> It is not working right at the moment.
> 
> I would like to have it repaired under my warranty.
> 
> Please let me know how we can sort this out.
> 
> Thanks!

- Tessa dishwasher, delivered 2025-05-09, plan none: **repair_booked**
- Withheld from the message: fault
- Agree? 

## T-125 (branching, repeat_repairs)

> Hi there my name is Mei Novak and I am writing because I am having a really stressful time with my Halvard Keel washing machine under order H-101604 as it is leaking water all over the floor again which is so frustrating since this is the third time it has happened and it has already been repaired twice for this exact same issue so I would like you to please come and sort it out under the warranty as soon as you possibly can because I am worried about the damage it is doing to my kitchen floor and I really need it working properly again.

- Keel washing machine, delivered 2021-02-15, plan none: **replacement** (repeat_repairs)
- Agree? 

## T-132 (above_limit, early_refund_large)

> I am writing because I am completely fed up with my Halvard Ashby tumble dryer. I am Uma Lindqvist and my order number is H-101610. I have tried everything but the machine simply will not switch on at all. It is absolute rubbish to have a brand new product that is completely dead on arrival. I am not intrested in a repair or any other messing around, I just want my money back immediately. Please sort this out as soon as possible, as I am tired of wasting my time on this.

- Ashby tumble dryer, delivered 2026-08-12, plan none: **refund** (early_fault, GBP 430.00, needs approval)
- Agree? 

## T-152 (policy_detail, refund_after_window)

> My name is Jonas Abernethy and I am writing to you regarding my Halvard Fenwick cooker hood, order H-101629, which is currently malfunctioning as it continues to run but performs very poorly indeed, failing to extract cooking odours as it should, and as this product is clearly not fit for purpose I am requesting that you process a full refund of my money immediately so that I can look into purchasing a replacement elsewhere as I have no further time to waste on faulty appliances that simply do not do the job they were advertised to perform.

- Fenwick cooker hood, delivered 2022-04-19, plan none: **repair_booked**
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

## T-173 (policy_detail, exclusion, accidental_damage)

> Dear Halvard Home, my name is Priya Eriksen and I am writing to you regarding my Halvard Vale fridge freezer under order number H-101647 as I am having some trouble with it constantly showing error code E46 and although I must mention that it unfortunately fell off the worktop when I was in the process of moving it I was still hoping that you might be able to arrange for the appliance to be repaired under the warranty as I am very worried about the unit and would really appreciate your help in resolving this issue as soon as possible, thank you.

- Vale fridge freezer, delivered 2025-04-29, plan none: **decline** (accidental_damage)
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

## T-208 (above_limit, early_refund_large)

> Hello, my name is Wen Novak. I am writing to you regarding my Halvard Orrin heat pump, which is linked to order number H-101678. I am afraid I have run into a bit of a problem as the unit will not switch on at all, despite my best efforts. Since it does not appear to be working as expected, I would like to request a full refund for this purchase. I hope we can get this sorted out quite quickly. Many thanks for your help with this.

- Orrin heat pump, delivered 2026-10-01, plan none: **refund** (early_fault, GBP 4800.00, needs approval)
- Agree? 

## T-224 (routine)

> Hi there, my name is Rhian Lindqvist and I am getting in touch because I have got a bit of a problem with my Halvard Vale fridge freezer from order number H-101694 as it has started leaking water all over my kitchen floor which is really quite a nuisance so I was hoping you could please get this sorted out for me as soon as possible, also I am only able to communicate via email at the moment so please do not try to call me as I cannot take any phone calls right now, thanks so much for your help with this.

- Vale fridge freezer, delivered 2024-03-29, plan none: **repair_booked**
- Agree? 

## T-233 (policy_detail, goodwill_used)

> Hi there, I am Mei Takahashi and I am writing because I am having a bit of a nightmare with my Halvard Corra induction hob that I bought recently, it keeps flashing up this really annoying E22 error code every time I try to use it which is just so frustrating as I cannot cook anything properly, my order number is H-101700 and I was hoping that you could please arrange for it to be repaired under the warranty as soon as possible because I really need it working again for my kitchen, thanks so much for your help with this.

- Corra induction hob, delivered 2023-01-28, plan none: **decline** (out_of_cover)
- Agree? 

## T-237 (missing_information, no_fault)

> Dear Halvard Home support, my name is Sanjay Umeh and I am feeling quite worried about my Halvard Tessa dishwasher. My order number is H-101704. It has stopped working right and I am very concerned about this issue. I would like to request that it is repaired under the warranty as soon as possible, please. I hope you can help me sort this out quickly, as it is very stressful having a broken appliance in the kitchen. I look forward to hearing back from you soon about the next steps. Best regards, Sanjay Umeh.

- Tessa dishwasher, delivered 2025-11-07, plan none: **repair_booked**
- Withheld from the message: fault
- Agree? 

