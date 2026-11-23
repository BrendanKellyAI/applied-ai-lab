# Task A test items for hand checking

Read each message and its label. Reply with the numbers of any items whose label is wrong, and what is wrong (for example: 12 route should be warranty_claim). Every wrong label is reported in the dataset README.

## 1. A-test-00008 (harmless_safety_word)

> hi, i'm zak. my new halvard vale fridge freezer arrived yesterday with a large dent in the side. it looks hot enough to set the world on fire, but i need a refund instead.

**Label:** route `return_refund`, safety `false`, product `Vale fridge freezer`, fault `damaged_on_arrival`

## 2. A-test-00009 (angry_not_complaint)

> I bought the Halvard Orrin heat pump last week and frankly it is rubbish. The machine runs but it leaves my clothes completely soaking wet even after a three hour cycle. It is utterly useless for its main job. I am done trying to get this thing to work properly. I want to return the unit immediately and need a full refund for this waste of money. Please let me know how to arrange the collection.

**Label:** route `return_refund`, safety `false`, product `Orrin heat pump`, fault `poor_performance`

## 3. A-test-00038 (safety)

> Dear Halvard Home support, I am writing to you because I am extremly worried about my Halvard Fenwick cooker hood. Last night, when I reached up to adjust the settings, I recieved a sharp electric shock from the metal casing. It was a proper tingle that ran right up my arm and it has left me quite shaken. This simply isn't acceptable for a kitchen appliance and I am terrified to even go near it now. As the unit is still well within its warranty period, I am formally requesting that you send an engineer out to repair the fault immediately or, if that is not possible, please arrange for a full replacement. I need this sorted urgently as it is a serious safety hazard in my home. Look forward to hearing from you soon, Wes.

**Label:** route `warranty_claim`, safety `true`, product `Fenwick cooker hood`, fault `electric_shock`

## 4. A-test-00040 (plain)

> Dear Halvard Home, my new Vale fridge freezer arrived today with a large dent in the side. I am very disapointed with this service and would like to escalate my complaint immediately. Thanks, Aileen.

**Label:** route `complaint`, safety `false`, product `Vale fridge freezer`, fault `damaged_on_arrival`

## 5. A-test-00061 (safe_use_question)

> hi, i’m isla. i just bought the halvard brio kettle and i'm really loving it so far. i’m just a bit worried about the outside getting quite hot when the water boils. is it normal for the exterior to feel so warm to the touch, or should i be concerned about it overheating? i just want to make sure it’s safe for my kitchen worktop. thanks for your help with this.

**Label:** route `how_to_use`, safety `false`, product `Brio kettle`, fault `None`

## 6. A-test-00104 (two_requests)

> Hi there, I’m writing to you regarding my Halvard Ashby tumble dryer. Firstly, could you please advise on the best way to clean the lint filter to ensure I’m keeping the machine in top condition? On a much more serious note, I am incredibly frustrated with the service I have received so far. My dryer is running, but it consistently leaves my clothes soaking wet even after a three-hour cycle. I have contacted your support team twice now, and the lack of urgency is simply unacceptable. I am fed up with being passed around without any real solution. I would like to formally complain about the poor level of care I have been shown. Please escalate this issue to a manager immediately, as I expect a prompt and professional resolution to this ongoing problem.

**Label:** route `complaint`, safety `false`, product `Ashby tumble dryer`, fault `poor_performance`

## 7. A-test-00121 (plain)

> I am writing to formally complain regarding the poor level of service I have received from your team. While my Halvard Tessa dishwasher is working perfectly, the way I have been treated during recent correspondence is unacceptable. I am dissatisfied with the current resolution and would like to request that this matter be escalated to a senior manager immediately. I look forward to your prompt response regarding how you intend to address these service failures.

**Label:** route `complaint`, safety `false`, product `Tessa dishwasher`, fault `None`

## 8. A-test-00134 (negated_cue)

> i need a replacement cutlery basket for my halvard tessa dishwasher. i am not asking for a warranty repair or a replacement unit, just the part number so i can fit it myself.

**Label:** route `spare_part`, safety `false`, product `Tessa dishwasher`, fault `None`

## 9. A-test-00145 (harmless_safety_word)

> Dear Halvard Home Customer Service Team, I am writing to formally report an ongoing operational issue with my Halvard Corra induction hob. Whilst the unit performs perfectly well in terms of heat regulation, it reaches the necessary temperature to get red hot quite efficiently, I am encountering a persistent difficulty with the touch-sensitive control interface. The responsiveness of the induction zones is significantly impaired, as the surface frequently fails to register my commands unless pressed with excessive force. As this appliance is still covered under the terms of your comprehensive manufacturer warranty, I kindly request that you arrange for a professional engineer to conduct the necessary repairs. Alternatively, should a resolution not be feasible on-site, I would appreciate a direct replacement of the unit. I look forward to your prompt response regarding the next steps for my claim. Yours sincerely, Owen.

**Label:** route `warranty_claim`, safety `false`, product `Corra induction hob`, fault `poor_performance`

## 10. A-test-00151 (plain)

> dear halvard home team i hope you are having a pleasant week so far my name is declan and i have been enjoying using my recent purchase from your company immensely everything is working exactly as it should and the design is truly wonderful i am writing to you today because i was wondering if you might be able to provide any advice regarding kitchen interior design styles that would best complement your current product range i am planning a complete renovation of my home and would love to hear your professional opinion on which colour palettes or materials you think would create a cohesive aesthetic alongside your items i realise this is perhaps outside your usual scope of support but any guidance would be greatly appreciated as i really value your brand style warm regards declan

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 11. A-test-00153 (plain)

> i need to return my halvard brio kettle as it arrived with a large dent in the side i want a full refund for this damaged item please sort it out arjun

**Label:** route `return_refund`, safety `false`, product `Brio kettle`, fault `damaged_on_arrival`

## 12. A-test-00163 (plain)

> Hi there! I'm Imran, and I absolutely love my Halvard Brio kettle, it's a staple in my kitchen. I've noticed the little mesh filter inside is looking a bit worse for wear after all the hard water we have here. Are you able to point me in the right direction to order a replacement filter so I can swap it out myself? Thanks so much for your help with this!

**Label:** route `spare_part`, safety `false`, product `Brio kettle`, fault `None`

## 13. A-test-00166 (two_requests)

> dear halvard home, i am writing to enquire how i should best clean the aluminium grease filters on my halvard fenwick cooker hood. furthermore, i must lodge a formal complaint regarding the unit's poor suction performance, which has left my kitchen smelling of smoke. i am very disappointed with the service received so far and would like this matter escalated to a senior manager for immediate review. sincerely, oisin.

**Label:** route `complaint`, safety `false`, product `Fenwick cooker hood`, fault `poor_performance`

## 14. A-test-00180 (two_products)

> I am writing to formally request a refund for my Halvard Lumen smart thermostat, as it emits an unsettling vibration. I trust this matter will be resolved promptly, unlike my experience with the Halvard Tessa dishwasher.

**Label:** route `return_refund`, safety `false`, product `Lumen smart thermostat`, fault `noise`

## 15. A-test-00203 (plain)

> I am getting increasingly frustrated with this Halvard Ashby tumble dryer. I bought it only a few months ago, and it has already started flashing an error code on the display panel every single time I try to run a cycle. I have checked the manual, but it says absolutely nothing about what this specific code means or how I am supposed to clear it to get the machine working again. It is incredibly inconvenient to have a brand-new appliance just sitting here doing nothing because of some cryptic light sequence. I am at my wits' end trying to figure this out on my own. Can someone please tell me what this error means and how to resolve it immediately? I honestly expected much better quality and support from a brand like Halvard Home.

**Label:** route `how_to_use`, safety `false`, product `Ashby tumble dryer`, fault `error_code`

## 16. A-test-00216 (plain)

> Dear Halvard Home, I am writing to enquire whether your company might be interested in sponsoring my local village fête this coming August. I look forward to hearing from you regarding this matter.

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 17. A-test-00220 (safe_use_question)

> hi i have a new halvard vale fridge freezer and i need to understand the operation better as the manual is not clear i want to know if it is safe to leave the appliance running constantly overnight when i am asleep and if it is normal for the side panels to feel quite warm to the touch when the unit is cycling i have noticed the heat build up but there is no fault with the cooling performance it is working fine otherwise i just want to be sure about the safety aspect before i continue using it in this manner please let me know if this heat is expected or if i should move the unit further away from the wall to help with the airflow thanks tomasz

**Label:** route `how_to_use`, safety `false`, product `Vale fridge freezer`, fault `None`

## 18. A-test-00229 (negated_cue)

> Hello, I am writing regarding my Halvard Fenwick cooker hood. I am experiencing a persistent issue with the smart connectivity features. Specifically, the appliance will not connect to the official app, my home Wi-Fi network, or any other mobile device I have attempted to link it with. I have tried several times to resolve this following the manual, but it simply refuses to pair. I would like to arrange for the fault to be repaired or for the unit to be replaced under the terms of my current warranty. Please note that I am perfectly happy with the hood itself and I am not asking for a refund or looking to cancel my order; I just want the promised smart functionality to work correctly. I look forward to hearing how we can get this resolved.

**Label:** route `warranty_claim`, safety `false`, product `Fenwick cooker hood`, fault `connectivity`

## 19. A-test-00235 (harmless_safety_word)

> I am writing to express my frustration with my Halvard Mira robot vacuum. It simply will not switch on and seems to have absolutely no power, despite being fully charged. It is under warranty, so I expect you to either repair it immediately or provide a replacement unit. My previous experience with your products has been smoking hot, but this vacuum is currently useless. Please let me know how we can resolve this quickly. Regards, Beth.

**Label:** route `warranty_claim`, safety `false`, product `Mira robot vacuum`, fault `no_power`

## 20. A-test-00262 (mixed_request)

> I am writing regarding my Halvard Lumen smart thermostat which arrived yesterday. It does not switch on at all and has absolutely no power. At first, I was hoping you could either send a replacement unit or repair this one so I could actually use the device. However, after further consideration, I have decided that I do not want to deal with a faulty product any longer. I would now prefer to simply cancel my order and get my money back instead of going through a repair process. Could you please process a full refund for this purchase as soon as possible? I would appreciate it if you could confirm that you have received this request and let me know the next steps for returning the item to you. I look forward to your prompt response regarding this matter.

**Label:** route `return_refund`, safety `false`, product `Lumen smart thermostat`, fault `no_power`

## 21. A-test-00268 (plain)

> Hi, I just installed my Halvard Lumen smart thermostat but am feeling a bit lost. Could you please send over a guide on how to program the weekly heating schedule? Im worried I will mess it up.

**Label:** route `how_to_use`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 22. A-test-00276 (safety)

> My Halvard Ashby tumble dryer is smoking and sparking from the back, which is terrifying. I need this repaired or replaced immediately under warranty before it causes a fire in my house.

**Label:** route `warranty_claim`, safety `true`, product `Ashby tumble dryer`, fault `burning_or_smoke`

## 23. A-test-00285 (plain)

> Good morning to you. I trust this message finds you in excellent spirits today. I am writing to you as a loyal patron of your esteemed establishment, having recently acquired one of your latest models. Whilst I am entirely satisfied with the performance of the item, I find myself in a rather curious position regarding a personal endeavour. I am currently curating a decorative display for my kitchen and was wondering if your design team might be willing to share the specific Pantone colour codes used for the exterior finish of your current range. I have searched your literature extensively but have been unable to locate this information. Would it be at all possible for you to assist me with this aesthetic inquiry? I should be most grateful for any guidance you might kindly provide regarding this matter. Many thanks.

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 24. A-test-00290 (two_requests)

> I require information regarding the purchase of a replacement charcoal filter for my Halvard Fenwick cooker hood. Furthermore, the unit's lower access panel fails to close securely; please arrange a warranty repair or replacement.

**Label:** route `warranty_claim`, safety `false`, product `Fenwick cooker hood`, fault `door_or_lid`

## 25. A-test-00333 (two_requests)

> hi could you tell me how to properly clean the filter on my halvard tessa dishwasher also i am writing to make a formal complaint as my unit arrived with several large dents on the front panel and is clearly damaged i am not happy with the service so far and i would like this matter escalated to a manager immediately please let me know how you intend to fix this niamh

**Label:** route `complaint`, safety `false`, product `Tessa dishwasher`, fault `damaged_on_arrival`

## 26. A-test-00334 (plain)

> To the Halvard Home Customer Support Team, I am writing to express my profound dissatisfaction regarding the documentation provided with my Halvard Fenwick cooker hood. Despite my best efforts, I find the instructions concerning the initial setup and the routine maintenance protocols to be remarkably obtuse and inadequately detailed. I require explicit, step-by-step guidance on how to properly calibrate the extraction levels and, more importantly, the correct method for sanitising the grease filters without causing damage to the unit’s finish. It is frankly unacceptable that a premium appliance should be accompanied by such rudimentary guidance. I trust that you will rectify this deficiency by providing a comprehensive manual or a detailed explanation at your earliest convenience. I await your prompt response on this matter. Yours sincerely, Owen.

**Label:** route `how_to_use`, safety `false`, product `Fenwick cooker hood`, fault `None`

## 27. A-test-00365 (mixed_request)

> hi my halvard lumen smart thermostat will not switch on at all and has no power i initially thought about a repair or a replacement but honestly i have changed my mind about it now i just want to cancel this order and get my money back please let me know how i go about returning this unit for a full refund thanks callum

**Label:** route `return_refund`, safety `false`, product `Lumen smart thermostat`, fault `no_power`

## 28. A-test-00388 (mixed_request)

> I am concerned that my Halvard Brio kettle frequently leaves a metallic residue in my water. I initially requested a replacement, but I have decided I would prefer a full refund instead, please.

**Label:** route `return_refund`, safety `false`, product `Brio kettle`, fault `poor_performance`

## 29. A-test-00404 (two_requests)

> can i buy a replacement filter for my halvard keel washing machine? also, it refuses to connect to the app or wifi. please arrange a repair or replacement under warranty.

**Label:** route `warranty_claim`, safety `false`, product `Keel washing machine`, fault `connectivity`

## 30. A-test-00410 (safe_use_question)

> Hello, I have just bought a Halvard Brio kettle. Is it normal for the stainless steel body to get very hot to the touch while it is boiling? Many thanks, Aled.

**Label:** route `how_to_use`, safety `false`, product `Brio kettle`, fault `None`

## 31. A-test-00418 (safe_use_question)

> Hi, I have a Halvard Lumen smart thermostat installed in my hallway and I was wondering about the safety of leaving the backlight setting on permanently during the night. I like to keep the display lit up so I can see the temp when I walk past, but I am worried about the unit overheating or posing any sort of fire risk if it is constantly illuminated like that. Is it actually safe to run the device on its brightest setting 24/7 or should I be using the auto-dim feature instead? I want to make sure I am not pushing the hardware too hard and causing an unnecessary hazard. Please let me know if this is okay or if I need to change my settings. Thanks, Bronwen.

**Label:** route `how_to_use`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 32. A-test-00452 (safety)

> I am writing to express my profound dissatisfaction regarding the recent experience with my Halvard Ashby tumble dryer. During its standard operation this morning, the appliance began emitting a pungent odour of burning, followed immediately by the alarming discharge of thick smoke and visible electrical sparks from the rear control panel. This is an egregious safety failure that has left my laundry room in a perilous state. Despite my previous attempts to resolve this through your standard support channels, the response has been woefully inadequate. Given the severity of this hazard, I must insist that this matter be escalated to a senior member of your management team immediately. I expect a formal acknowledgment of this complaint and a definitive resolution strategy by the end of the business day. The current level of service provided by Halvard Home is entirely unacceptable.

**Label:** route `complaint`, safety `true`, product `Ashby tumble dryer`, fault `burning_or_smoke`

## 33. A-test-00463 (played_down_safety)

> I am writing to formalise a complaint regarding my Halvard Corra induction hob. It emitted some sparks and smoke, which was a bit of a nuicance. Please escalate this matter as I am concerned.

**Label:** route `complaint`, safety `true`, product `Corra induction hob`, fault `burning_or_smoke`

## 34. A-test-00516 (two_requests)

> Hello, I am looking to purchase a replacement cutlery basket for my Halvard Tessa dishwasher. Could you let me know which part number I need to order? Also, I would like to arrange a return and refund for the unit itself. While the machine runs, it simply doesn't clean the dishes properly, leaving food residue on everything after every cycle. It is just not performing as expected, so I would prefer to send it back.

**Label:** route `return_refund`, safety `false`, product `Tessa dishwasher`, fault `poor_performance`

## 35. A-test-00520 (plain)

> Dear Halvard Home team, I hope you are having a pleasant week. I am currently redecorating my kitchen and I was wondering if you could recommend any specific paint colours or interior design styles that complement the aesthetic of your products? I really admire the look of your range and would love to match my walls accordingly. Thank you so much for your time and I look forward to hearing your suggestions. Best wishes, Lowri.

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 36. A-test-00533 (negated_cue)

> hi there, just wanted to check in on my halvard mira robot vacuum. i ordered it a while back and the delivery date has actually come and gone now, but i've not seen hide nor hair of it. i checked the tracking link i was sent but it just seems to be stuck in limbo and hasn't updated since tuesday. i'm just really excited to get it running as my floors are in a bit of a state! also, just to be clear, i definitely don't want to cancel the order or get a refund or anything like that, i'm not asking for that at all, i just really want the vacuum to arrive. could you have a quick look and let me know when it might turn up? thanks so much, niamh.

**Label:** route `delivery`, safety `false`, product `Mira robot vacuum`, fault `None`

## 37. A-test-00543 (plain)

> Hi there, I’m hoping you can help me out. I’ve got a Halvard Lumen smart thermostat, but it’s started leaking liquid from the base unit recently, which is really strange. It’s still under warranty, so I’d love to get this sorted as soon as possible. Could you arrange for a repair or perhaps send out a replacement unit? It’s a bit of a nuisance, so let me know what the next steps are, Callum.

**Label:** route `warranty_claim`, safety `false`, product `Lumen smart thermostat`, fault `leak`

## 38. A-test-00556 (plain)

> Dear Sir or Madam, I regret to inform you that my Halvard Orrin heat pump arrived with significant denting to the casing. Consequently, I should like to request a full refund and return.

**Label:** route `return_refund`, safety `false`, product `Orrin heat pump`, fault `damaged_on_arrival`

## 39. A-test-00557 (two_requests)

> hi, i recently bought a halvard lumen smart thermostat from your website and it is working perfectly fine. i was wondering if you sell a replacement trim plate or a decorative mounting ring that would fit this model? i am hoping to tidy up the wall space behind the unit myself. aside from that, i have actually decided that this particular system does not quite suit my requirements after all. as i have not installed it yet, i would like to go ahead and cancel my order or arrange for a return to get my money back. could you please let me know the process for sending this back to you for a refund? thanks for your help with these queries, declan.

**Label:** route `return_refund`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 40. A-test-00565 (harmless_safety_word)

> hi i was just wondering if you guys sell any matching kitchen curtains as my new unit looks absolutely on fire in my kitchen and i would love to complete the look dev

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 41. A-test-00573 (plain)

> hi im isla my halvard keel washing machine is driving me mad because it just isnt spinning the clothes properly so they come out absolutely soaking wet every single time i use it this is completely unacceptable for a machine this new and i need you to either send someone round to fix it or just give me a full replacement under the warranty immediately as i am sick of hand wringing my laundry every day

**Label:** route `warranty_claim`, safety `false`, product `Keel washing machine`, fault `poor_performance`

## 42. A-test-00580 (plain)

> Good morning. I am writing to formally report an issue regarding my Halvard Ashby tumble dryer. Recently, the appliance has begun displaying an error code upon activation. As the unit remains under your manufacturer's warranty, I kindly request that you arrange for a professional repair or, alternatively, provide a replacement unit at your earliest convenience. I trust this matter will be resolved promptly and await your professional guidance on the necessary next steps. Thank you for your assistance.

**Label:** route `warranty_claim`, safety `false`, product `Ashby tumble dryer`, fault `error_code`

## 43. A-test-00590 (plain)

> hi there i need to book a routine service for my halvard ashby tumble dryer please there is nothing wrong with it at all just needs a quick check up thanks beth

**Label:** route `servicing_booking`, safety `false`, product `Ashby tumble dryer`, fault `None`

## 44. A-test-00593 (safe_use_question)

> Hi there, I’ve just recently picked up the Halvard Mira robot vacuum and I’m absolutely loving how it keeps the living room floor spotless! It’s honestly been a total game changer for me. I just had a quick question regarding its daily routine. I was thinking of scheduling it to do a full circuit of the house while I’m fast asleep so I can wake up to clean floors every single morning. Is it perfectly safe to leave the Halvard Mira running overnight like that, or does the battery or the motor need supervision while it’s in operation? I just want to make sure I’m not risking anything silly by letting it roam around while I'm tucked up in bed. Thanks so much for your help with this, really appreciate it!

**Label:** route `how_to_use`, safety `false`, product `Mira robot vacuum`, fault `None`

## 45. A-test-00617 (negated_cue)

> Hi, I need to reschedule my routine service for the Halvard Lumen smart thermostat. The app isnt letting me pick a new date. Just to be clear, there is absolutely nothing wrong with the unit so I am not asking for a repair or a warranty replacement. I just need a standard maintenance check-up booked as soon as possible. Can you sort this out for me? Its getting a bit frustratin trying to navigate the website.

**Label:** route `servicing_booking`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 46. A-test-00626 (angry_not_complaint)

> i'm absolutely fuming about this. my new halvard orrin heat pump is completely dead and does not switch on at all. there is no power whatsoever. i don't want a repair or any technical advice, i just want to send this rubbish back immediately. please process a full refund for this order right now as it's not fit for purpose. let me know how to arrange the return asap. regards, bronwen.

**Label:** route `return_refund`, safety `false`, product `Orrin heat pump`, fault `no_power`

## 47. A-test-00637 (negated_cue)

> Dear Halvard Home, I am writing to you regarding my Halvard Fenwick cooker hood, which I purchased recently and is currently under warranty. Unfortunately, the appliance has developed a fault and will not switch on at all. It appears to have no power whatsoever, despite my checking the fuse and the connection to the mains. I would be very grateful if you could arrange for a repair or, if that is not possible, a replacement unit to be sent out as soon as possible. I would like to clarify that I am not looking to return the item or request a refund at this stage, as I am very happy with the model itself and would prefer to have a working one. I look forward to hearing from you soon regarding the next steps for resolving this issue. Kind regards, Leon.

**Label:** route `warranty_claim`, safety `false`, product `Fenwick cooker hood`, fault `no_power`

## 48. A-test-00638 (played_down_safety)

> I am writing to formally complain regarding my Halvard Mira robot vacuum. It emitted a small puff of smoke and a faint burning smell, which was rather unpleasant. Please escalate this matter for further investigation.

**Label:** route `complaint`, safety `true`, product `Mira robot vacuum`, fault `burning_or_smoke`

## 49. A-test-00642 (two_requests)

> I would appreciate some guidance regarding the optimal procedure for descaling my Halvard Brio kettle to ensure its longevity. Furthermore, I must formally express my dissatisfaction regarding the initial condition of the appliance, which arrived with significant dents to the exterior casing. Given the unsatisfactory nature of my previous correspondence with your support team, I kindly request that this matter be escalated to a senior manager for a more thorough review and prompt resolution.

**Label:** route `complaint`, safety `false`, product `Brio kettle`, fault `damaged_on_arrival`

## 50. A-test-00643 (harmless_safety_word)

> hi there, i'm hoping to arrange a routine service for my halvard keel washing machine. there are absolutely no faults with it at all and it is running perfectly, but i’ve had it for a couple of years now and just want to keep everything in top condition with a professional check-up. honestly, the way this machine handles a spin cycle is fire, it really is the best appliance i have ever owned. i was wondering if you could help me book a visit from one of your technicians sometime in the next few weeks? please let me know what dates or times might be available for someone to pop round to my place. thanks for your help with this request, dev.

**Label:** route `servicing_booking`, safety `false`, product `Keel washing machine`, fault `None`
