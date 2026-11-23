# Task A test items for hand checking

Read each message and its label. Reply with the numbers of any items whose label is wrong, and what is wrong (for example: 12 route should be warranty_claim). Every wrong label is reported in the dataset README.

## 1. A-test-00009 (safety)

> I am writing to formally complain about my Halvard Keel washing machine. It recently emitted smoke and sparks, posing a serious safety risk. I am very dissatisfied and request that this matter be escalated immediately.

**Label:** route `complaint`, safety `true`, product `Keel washing machine`, fault `burning_or_smoke`

## 2. A-test-00010 (played_down_safety)

> Hello, I'm a bit worried about my Halvard Lumen smart thermostat. Earlier today, it started smoking and there were a few sparks coming from the unit. I'm sure it's probably just a minor glitch, but it’s definitely not working anymore. Could you please arrange for a repair or send a replacement under the warranty? I’m quite anxious about leaving it on the wall if it's going to act up like that again. Thanks, Niamh.

**Label:** route `warranty_claim`, safety `true`, product `Lumen smart thermostat`, fault `burning_or_smoke`

## 3. A-test-00037 (two_products)

> hi i need a new door seal for my halvard vale fridge freezer as it just wont close properly anymore by the way my halvard lumen smart thermostat is working perfectly cheers dev

**Label:** route `spare_part`, safety `false`, product `Vale fridge freezer`, fault `door_or_lid`

## 4. A-test-00039 (plain)

> Hello, I am a bit worried about my new Halvard Fenwick cooker hood. I have read the manual but still find it a bit confusing to understand how to change the grease filters properly without damging them. Could you please send me some simple instructions on how to clean them safely? I really dont want to break anything as it looks so lovely in my kitchen. Many thanks, Morag.

**Label:** route `how_to_use`, safety `false`, product `Fenwick cooker hood`, fault `None`

## 5. A-test-00063 (plain)

> I regret to inform you that my Halvard Brio kettle is producing a most unusual vibrating noise. Consequently, I must formally request to return the item and obtain a full refund immediately.

**Label:** route `return_refund`, safety `false`, product `Brio kettle`, fault `noise`

## 6. A-test-00102 (plain)

> hi my halvard brio kettle is working perfectly fine but it is due for a routine service so could i please book a time for someone to come out and take a look leon

**Label:** route `servicing_booking`, safety `false`, product `Brio kettle`, fault `None`

## 7. A-test-00120 (plain)

> Dear Halvard Home, I am writing to formally report that my Halvard Tessa dishwasher is failing to cool. I request that this appliance be either repaired or replaced under the terms of my warranty.

**Label:** route `warranty_claim`, safety `false`, product `Tessa dishwasher`, fault `not_cooling`

## 8. A-test-00134 (plain)

> Hi, my Halvard Lumen smart thermostat is just flashing an error code at me. It’s still under warranty, so could you please fix it or just send a replacement out? Thanks, Ruth.

**Label:** route `warranty_claim`, safety `false`, product `Lumen smart thermostat`, fault `error_code`

## 9. A-test-00144 (plain)

> Hello, I am writing to formally complain about the service I have received regarding my Halvard Keel washing machine. I am deeply dissapointed with the lack of help provided so far. My machine has been leaking water onto my utility room floor for the past week, causing significant distress and damage to my flooring. Despite my previous calls to your support team, nothing has been resolved. I feel my concerns have been dismissed entirely, which is quite upsetting. I would like to formally escalate this matter to a manager immediately, as the current situation is completely unaceptable for such an expensive appliance. Please confirm when I can expect a senior member of your team to contact me regarding a full repair or a replacement unit. I look forward to your prompt reply. Kind regards, Grace.

**Label:** route `complaint`, safety `false`, product `Keel washing machine`, fault `leak`

## 10. A-test-00151 (plain)

> hi, i need to book a routine service for my halvard fenwick cooker hood. there are no faults, just standard maintenance. please let me know when you can send someone out. thanks, ruth.

**Label:** route `servicing_booking`, safety `false`, product `Fenwick cooker hood`, fault `None`

## 11. A-test-00153 (two_products)

> hi my halvard orrin heat pump is leaking water everywhere i would like a repair or a replacement under the warranty thanks also my halvard corra induction hob is working fine regards hamza

**Label:** route `warranty_claim`, safety `false`, product `Orrin heat pump`, fault `leak`

## 12. A-test-00164 (plain)

> Hi there, I was wondering if you could help me find the right replacment lint filter for my Halvard Keel washing machine? It is still runing perfectly, but I've noticed the mesh on the current one is getting a bit frayed after all these years. I would realy like to order a new one to fit myself if you have them in stock? Many thanks, Gareth.

**Label:** route `spare_part`, safety `false`, product `Keel washing machine`, fault `None`

## 13. A-test-00167 (plain)

> hi there, i hope you are having a nice day. i am writing to ask for some help with my halvard brio kettle. it has started showing an error code on the display, but i am not sure what this means or how to resolve it as the kettle seems to be working otherwise. could you please advise on how i should proceed to clear this? thanks for your time, oisin.

**Label:** route `how_to_use`, safety `false`, product `Brio kettle`, fault `error_code`

## 14. A-test-00180 (two_products)

> My Halvard Vale fridge freezer has no power and simply will not switch on. I want to return it for a full refund. My Halvard Mira robot vacuum works fine, but this unit is useless.

**Label:** route `return_refund`, safety `false`, product `Vale fridge freezer`, fault `no_power`

## 15. A-test-00205 (played_down_safety)

> my halvard mira robot vacuum started smoking and throwing sparks today just a little bit of fire really i want a full refund and to return this item immediately please sort it

**Label:** route `return_refund`, safety `true`, product `Mira robot vacuum`, fault `burning_or_smoke`

## 16. A-test-00216 (plain)

> I am writing to formally request assistance regarding my Halvard Fenwick cooker hood. Regrettably, the front glass panel has developed a mechanical fault and will no longer latch securely into the closed position. As this appliance remains under your manufacturer's warranty, I kindly request that you arrange for a professional repair or, should that prove insufficient, a full replacement of the unit. I look forward to your prompt confirmation regarding the next steps in this matter.

**Label:** route `warranty_claim`, safety `false`, product `Fenwick cooker hood`, fault `door_or_lid`

## 17. A-test-00219 (safety)

> Hi there, I’m getting in touch because I’m really worried about my Halvard Tessa dishwasher. I was running a cycle earlier and it started smoking, plus there were sparks flying out from behind the control panel. It also smells strongly of burning plastic now, which is terrifying. As it's still under warranty, could you please arrange for a repair or send out a replacement unit as soon as possible? I obviously can’t use it safely anymore. Thanks, Lowri.

**Label:** route `warranty_claim`, safety `true`, product `Tessa dishwasher`, fault `burning_or_smoke`

## 18. A-test-00228 (plain)

> Dear Halvard Home, I am writing to enquire regarding the delivery status of my Halvard Tessa dishwasher. My order has yet to arrive, and I would be grateful for an update on the scheduled delivery time.

**Label:** route `delivery`, safety `false`, product `Tessa dishwasher`, fault `None`

## 19. A-test-00234 (two_products)

> Dear Halvard Home, I am writing regarding my Mira robot vacuum, which has unfortunately stopped working. It refuses to switch on and appears to have no power at all. As it is still within the warranty period, I would appreciate it if you could arrange for a repair or a replacement. I have been very pleased with my Halvard Vale fridge freezer, so I hope you can resolve this vacuum issue quickly. I look forward to hearing from you soon, Fraser.

**Label:** route `warranty_claim`, safety `false`, product `Mira robot vacuum`, fault `no_power`

## 20. A-test-00264 (plain)

> Hello, I am writting because I need to get a replacment lint filter for my Halvard Ashby tumble dryer. I am worried about ordering the wrong part online and damaging the unit. Could you please confirm the exact part number I need to buy so I can fit it myself safely? Everything else is working perfecly, I just want to keep it well maintained. Many thanks, Lowri.

**Label:** route `spare_part`, safety `false`, product `Ashby tumble dryer`, fault `None`

## 21. A-test-00273 (played_down_safety)

> Dear Halvard Home, I am writing to you regarding the Halvard Fenwick cooker hood that I purchased from your store recently. I wanted to report a minor incident that happened while I was cleaning the unit earlier today. When I touched the metal casing, it gave me a little tingle. It was likely nothing, perhaps just a static discharge, but I must admit it was a bit unexpected. Given this experience, I would feel much more comfortable if I could arrange to return the item and have my order cancelled for a full refund. I have been very impressed with your brand otherwise, but I would prefer to err on the side of caution here. Please could you let me know the process for sending the hood back? I look forward to hearing from you soon. Best regards, Hamza.

**Label:** route `return_refund`, safety `true`, product `Fenwick cooker hood`, fault `electric_shock`

## 22. A-test-00279 (two_products)

> I am writing to formally complain about my Halvard Corra induction hob, which arrived with significant dents. After my positive experience with the Orrin heat pump, this is unacceptable. Please escalate this issue immediately.

**Label:** route `complaint`, safety `false`, product `Corra induction hob`, fault `damaged_on_arrival`

## 23. A-test-00289 (plain)

> hi, i would like to book a routine service for my halvard lumen smart thermostat please. there are no faults with it at all, it is working perfectly fine, but i would just like to get it checked over for maintenance as it has been a couple of years since the last inspection. could you let me know what dates you have available next month for a technician to visit? thanks, hamza.

**Label:** route `servicing_booking`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 24. A-test-00293 (plain)

> To whom it may concern, I am writing to request the comprehensive operating instructions for my recently acquired Halvard Vale fridge freezer. Specifically, I require formal guidance regarding the optimal temperature settings and the recommended protocol for performing the internal sanitisation of the unit. I trust that you shall provide the relevant documentation at your earliest convenience. I await your prompt response regarding this matter. Yours faithfully, Aileen.

**Label:** route `how_to_use`, safety `false`, product `Vale fridge freezer`, fault `None`

## 25. A-test-00336 (plain)

> I’m getting frustrated because my Halvard Lumen smart thermostat still hasn't arrived. It was due yesterday, but I’ve had no delivery updates or tracking info. Can you please tell me where it is?

**Label:** route `delivery`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 26. A-test-00337 (plain)

> I ordered my Halvard Brio kettle over a week ago and it still hasnt turned up. I paid for next day delivery but the tracking link isnt working and I havent recieved any updates. My order number is HH9982. Can you please let me know when this is actualy going to be delivered? I need to know if someone needs to be home to sign for it.

**Label:** route `delivery`, safety `false`, product `Brio kettle`, fault `None`

## 27. A-test-00369 (plain)

> Dear Halvard Home, I recently purchased the Halvard Tessa dishwasher and I am delighted with it so far. Would you be able to provide some guidance on the best settings to use for delicate glassware? I am also keen to know your recommended frequency for cleaning the internal filters to ensure it stays in top condition. Thank you for your time and help with these questions. Best wishes, Lowri.

**Label:** route `how_to_use`, safety `false`, product `Tessa dishwasher`, fault `None`

## 28. A-test-00391 (plain)

> hi i am getting quite worried as my halvard tessa dishwasher still has not arrived today despite being promised a delivery slot for this morning i have checked the tracking link but it is not showing any updates at all and i am concerned the driver cannot find my house please let me know what is happening as i have been waiting in all day for it kofi

**Label:** route `delivery`, safety `false`, product `Tessa dishwasher`, fault `None`

## 29. A-test-00407 (plain)

> Dear Halvard Home, I am writing to enquire regarding the delivery status of my Halvard Vale fridge freezer. I have yet to receive a confirmed arrival date or tracking information. May I please have an update?

**Label:** route `delivery`, safety `false`, product `Vale fridge freezer`, fault `None`

## 30. A-test-00412 (plain)

> Hi, my Halvard Mira robot vacuum has started leaking liquid from the base. It is still under warranty, so could you please arrange for a repair or a replacement unit for me?

**Label:** route `warranty_claim`, safety `false`, product `Mira robot vacuum`, fault `leak`

## 31. A-test-00420 (plain)

> Hi there! I'm having a bit of a nightmare with my Halvard Keel washing machine. It’s just not heating the water up at all during the cycle, so my clothes are coming out cold and not getting properly clean. It’s still under warranty, so could you sort out a repair or get me a replacement unit sorted as soon as possible? Cheers, Owen.

**Label:** route `warranty_claim`, safety `false`, product `Keel washing machine`, fault `not_heating`

## 32. A-test-00457 (harmless_safety_word)

> Hi, I have just instaled my new Halvard Corra induction hob. It gets red hot instantly which is brilliant, but could you please send over some tips on the best way to clean the glass surface?

**Label:** route `how_to_use`, safety `false`, product `Corra induction hob`, fault `None`

## 33. A-test-00466 (angry_not_complaint)

> my halvard corra induction hob is leaking liquid everywhere i am sick of this rubbish so just take it back and give me my money back immediately grace

**Label:** route `return_refund`, safety `false`, product `Corra induction hob`, fault `leak`

## 34. A-test-00520 (angry_not_complaint)

> I am writing to express my profound dissatisfaction regarding the delivery of my order, reference number 88291, which was scheduled to arrive between 08:00 and 12:00 today. It is now well past the appointed time, yet no delivery vehicle has appeared, nor have I received any notification regarding a delay. Furthermore, the tracking link provided remains entirely inactive, rendering it impossible for me to monitor the shipment's progress. I have remained at the property specifically to grant access for this delivery, and this lack of reliability is frankly unacceptable. I require you to contact the courier immediately and provide me with an accurate update regarding the status of my order and a confirmed arrival time without further prevarication. I expect a prompt response regarding this matter, as my time is of significant value.

**Label:** route `delivery`, safety `false`, product `None`, fault `None`

## 35. A-test-00523 (plain)

> Hello, I am writing to check on the status of my recent order for a Halvard Brio kettle, which I purchased through your website last week. According to the confirmation email, it was due to arrive yesterday, but I have yet to receive a delivery notification or an updated tracking link. I have been waiting in all morning, but unfortunately, no courier has appeared, and I haven't received any missed delivery slips either. Could you please check the tracking information for me and confirm if there is an issue with the courier or if the delivery slot has simply been rescheduled? I am very much looking forward to using my new kettle, so I would appreciate any help you can provide in locating my parcel. Thank you for your time and assistance with this matter. Best regards, Gareth.

**Label:** route `delivery`, safety `false`, product `Brio kettle`, fault `None`

## 36. A-test-00538 (plain)

> Hi there! I'm just checking in on my order for the Halvard Lumen smart thermostat. It was supposed to arrive today, but I haven't heard a peep from the courier and there's no update on the tracking link. I'm going to be in all afternoon, so I really hope I haven't missed the delivery slot! Could you please have a look and see where it’s got to? Thanks so much, Jude.

**Label:** route `delivery`, safety `false`, product `Lumen smart thermostat`, fault `None`

## 37. A-test-00548 (plain)

> I am writing to formally express my dissatisfaction regarding my Halvard Fenwick cooker hood. Recently, the appliance has begun to emit an incessant, unusual vibration during operation, which is entirely unacceptable for a product of this calibre. As the unit remains under warranty, I trust you will arrange for a prompt repair or, should that prove insufficient, a complete replacement. I anticipate your immediate attention to this matter and look forward to your swift resolution.

**Label:** route `warranty_claim`, safety `false`, product `Fenwick cooker hood`, fault `noise`

## 38. A-test-00561 (plain)

> I am writing to formally complain regarding my recent delivery of a Halvard Tessa dishwasher. Upon unboxing the unit, I discovered that it arrived significantly dented on the front panel and several internal tray components are missing entirely. I am very disappointed with the level of service provided thus far. Given the state of this appliance, I would like to escalate this matter to a manager immediately to discuss a replacement or a full refund. I look forward to your prompt response.

**Label:** route `complaint`, safety `false`, product `Tessa dishwasher`, fault `damaged_on_arrival`

## 39. A-test-00562 (plain)

> Hi, I just installed my new Halvard Fenwick cooker hood but the manual is really unclear. Could you please send me some simple instructions on how to clean the grease filters propery? Thanks, Isla.

**Label:** route `how_to_use`, safety `false`, product `Fenwick cooker hood`, fault `None`

## 40. A-test-00570 (played_down_safety)

> hi, i’m writing because my halvard mira robot vacuum started smoking while it was charging earlier. it let out a bit of a burnt plastic smell and there were some small sparks, though it was probably just a minor glitch. honestly, i don't feel comfortable using it anymore. i’d like to send it back and get a full refund for this order as soon as possible. let me know how to proceed with the return, aileen.

**Label:** route `return_refund`, safety `true`, product `Mira robot vacuum`, fault `burning_or_smoke`

## 41. A-test-00579 (plain)

> hi im priya and need to buy a replacement cutlery basket for my halvard tessa dishwasher as mine is cracked can you let me know which part number i need to order please

**Label:** route `spare_part`, safety `false`, product `Tessa dishwasher`, fault `None`

## 42. A-test-00584 (plain)

> i have a halvard mira robot vacuum that is displaying an error code on the screen. it is still within the warranty period, so i expect you to fix it or send a replacement unit immediately. please let me know how we can proceed with this repair or exchange as soon as possible. regards, callum.

**Label:** route `warranty_claim`, safety `false`, product `Mira robot vacuum`, fault `error_code`

## 43. A-test-00593 (plain)

> Dear Sir or Madam, I am writing to you this morning as I find myself in a state of considerable concern regarding the environmental impact of your manufacturing facilities. Could you please provide me with a detailed breakdown of your current carbon neutrality strategy and waste management policies? I am deeply anxious to ensure that my recent purchase aligns with my personal ethical standards. I await your formal clarification on these matters with great anticipation, as this information is quite vital to me.

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 44. A-test-00596 (two_products)

> Dear Halvard Home, I am writing regarding my Corra induction hob. Recently, it has stopped heating properly and is barely warming my pans at all. As it is still under warranty, could you please arrange for a repair or a replacement? I also have your Lumen smart thermostat installed and love the brand, so I am hoping to get this sorted quickly. Thank you for your help, Yasmin.

**Label:** route `warranty_claim`, safety `false`, product `Corra induction hob`, fault `not_heating`

## 45. A-test-00623 (unknown_product)

> hi there, i hope you are having a good week. i am writing to you today because i am a big fan of my halvard air fryer and have been very impressed with how well it performs. i was wondering if you might be able to help me with a query regarding a different appliance entirely. i am looking to purchase a new robotic lawnmower for my back garden and wanted to know if halvard home has any plans to release a model like that in the near future? i have searched your website but could not find any mention of outdoor maintenance equipment, so i thought i would ask you directly. i would love to stick with your brand if possible as the quality of your kitchenware is excellent. thanks in advance for any information you can provide regarding this, grace.

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 46. A-test-00632 (plain)

> hi, i am looking for the contact details for the local council recycling centre to dispose of some old cardboard packaging. can you please provide the address or a phone number for me?

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 47. A-test-00643 (unknown_product)

> Hi, I’m Imran. I’m feeling a bit worried as I’ve just moved house and can’t find the manual for my Halvard ice cream maker. More importantly, could you please tell me how to safely dispose of the old gas boiler left behind by the previous owners? I’m concerned about it being a safety risk in the kitchen near my appliances. Do you have a contact or a service that handles this kind of removal for me?

**Label:** route `other`, safety `false`, product `None`, fault `None`

## 48. A-test-00644 (angry_not_complaint)

> I am writing to express my profound dissatisfaction regarding my recent order. It is now well past the scheduled delivery window, and I have yet to receive any correspondence concerning its whereabouts. The tracking link provided remains entirely non-functional. I find this lack of professional reliability unacceptable. Could you please investigate the current location of my shipment and provide an immediate update on precisely when I may expect delivery? I trust you will resolve this oversight without further delay.

**Label:** route `delivery`, safety `false`, product `None`, fault `None`

## 49. A-test-00649 (plain)

> Dear Customer Service Team, I am writing to formally request a routine service appointment for my Halvard Orrin heat pump. Whilst the appliance is currently functioning to my entire satisfaction and exhibits no faults, I am anxious to ensure it remains in optimal condition through regular professional maintenance. Could you please advise on the earliest available date for a technician to attend? I look forward to your prompt response regarding this matter. Yours sincerely, Lowri.

**Label:** route `servicing_booking`, safety `false`, product `Orrin heat pump`, fault `None`

## 50. A-test-00650 (plain)

> hi, my halvard vale fridge freezer has stopped cooling properly and everything is going off. could you please get this repaired or replaced under the warranty? thanks, hana.

**Label:** route `warranty_claim`, safety `false`, product `Vale fridge freezer`, fault `not_cooling`
