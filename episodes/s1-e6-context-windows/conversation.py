"""The fixed conversation for Demonstration 2: one instruction, twenty-four earlier exchanges,
and a final question.

The text is committed, not generated, so every run sends the same words. It is in English on
purpose. The instruction asks for French, and the earlier assistant turns do not follow it, so
a reply in French can only come from the model still holding the instruction, never from copying
the language of its own earlier answers.
"""

INSTRUCTION = "Reply only in French."
FINAL_QUESTION = (
    "What is the single most useful tip for a complete beginner? Two sentences at most."
)

EARLIER_EXCHANGES = [
    (
        "I have never grown anything. Where should I start?",
        "Start small. A couple of raised beds or a few large pots is plenty for a first season, "
        "because a small plot is easier to water, weed and watch. Pick a spot that gets at least "
        "six hours of sun a day, sheltered from strong wind and close to a tap. Choose forgiving "
        "crops such as lettuce, radishes, courgettes and runner beans. Keep a notebook of what "
        "you sow and when. Most beginners fail by planting too much too early, not by lacking "
        "skill.",
    ),
    (
        "How do I know what kind of soil I have?",
        "Pick up a handful of damp soil and squeeze it. If it forms a sticky ball that stays "
        "shiny when rubbed, it is mostly clay. If it feels gritty and falls apart at once, it is "
        "sandy. Soil that holds together loosely and feels crumbly is loam, which is the easiest "
        "to work with. You can also dig a hole and fill it with water: if it drains within an "
        "hour the drainage is good. Whatever you find, adding compost every year improves it.",
    ),
    (
        "What is compost, and do I really need it?",
        "Compost is plant waste that has broken down into a dark, crumbly material full of "
        "nutrients and tiny organisms. You do not strictly need it, but it is the cheapest way "
        "to feed the soil and to help it hold water. Kitchen peelings, grass clippings, shredded "
        "cardboard and fallen leaves all work. Aim for roughly equal parts green and brown "
        "material, keep the heap damp, and turn it now and then. In about a year you will have "
        "something you can spread over your beds.",
    ),
    (
        "Should I start from seeds or buy young plants?",
        "Both are fine, and many gardeners mix them. Seeds are cheap and give you a wide choice "
        "of varieties, and crops like carrots, radishes and beans do best sown straight into the "
        "ground. Young plants save weeks of work and suit slow starters such as tomatoes, "
        "peppers and celery. If you buy plants, choose ones with green leaves and a sturdy stem, "
        "and harden them off for a week outdoors before you put them in the ground.",
    ),
    (
        "How often should I water?",
        "It is better to water deeply and less often than to sprinkle a little every day. A "
        "good soaking encourages roots to grow downwards, which makes plants tougher in dry "
        "spells. Push a finger two centimetres into the soil: if it is dry, water. Early "
        "morning is best, because less is lost to the sun and the leaves dry before night, "
        "which discourages disease. Pots dry out much faster than beds, so check them daily "
        "in summer.",
    ),
    (
        "What are the most common pests?",
        "Slugs and snails are the usual culprits in damp climates, along with aphids, "
        "caterpillars and the odd rabbit. Check leaves, including the undersides, every few "
        "days so you catch trouble early. Picking pests off by hand, using copper tape round "
        "pots, and covering brassicas with fine netting all work without chemicals. Encourage "
        "ladybirds, hoverflies and birds, which eat many pests for you. A tidy garden helps, "
        "because slugs shelter under old leaves and planks.",
    ),
    (
        "What is crop rotation?",
        "Crop rotation means growing different families of vegetables in a different part of "
        "the garden each year. Pests and diseases that target one family build up in the soil "
        "if you plant it in the same place, and each family takes different nutrients. A simple "
        "plan uses three groups: roots such as carrots and beetroot, legumes and onions, and "
        "brassicas such as cabbage and kale. Move each group along one bed every year and the "
        "cycle repeats every three years.",
    ),
    (
        "Can I grow vegetables in containers?",
        "Yes, and many do well. Use pots with drainage holes and a good multipurpose compost, "
        "and give each plant enough room: a tomato wants a pot at least thirty centimetres "
        "across, while lettuces and herbs are happy in a window box. Containers need more "
        "frequent watering and feeding than beds, because nutrients wash out. Put them where "
        "they get plenty of light, and group them together so they shelter each other from the "
        "wind.",
    ),
    (
        "When is the last frost, and why does it matter?",
        "The last frost is the final night of spring when the temperature drops below freezing, "
        "and it varies with where you live. Tender plants such as tomatoes, courgettes and "
        "beans are killed or badly damaged by it, so they should only go outside after it has "
        "passed. Ask a neighbour or check local records to find your average date. Hardy "
        "crops like peas, broad beans and onions can be planted earlier. A sheet of fleece "
        "will protect young plants on a cold night.",
    ),
    (
        "How do I know when to harvest?",
        "Each crop gives its own signs. Courgettes are best small, at about fifteen "
        "centimetres, and keep producing if you pick them often. Tomatoes should be fully "
        "coloured and slightly soft. Lettuce can be picked leaf by leaf from the outside, "
        "which lets the plant keep growing. Carrots and beetroot show their shoulders above "
        "the soil when they are ready. Harvest in the morning when plants are cool and full of "
        "water, and pick regularly, since leaving fruit on the plant slows new growth.",
    ),
    (
        "What does mulching do?",
        "Mulch is a layer of material spread over the soil, such as compost, bark, straw or "
        "grass clippings. It keeps moisture in, stops many weeds from sprouting, protects roots "
        "from temperature swings and slowly feeds the soil as it rots. Apply it about five "
        "centimetres deep in spring, once the soil has warmed and been watered, and keep it "
        "clear of plant stems so they do not rot. Top it up every year as it breaks down.",
    ),
    (
        "Which tools do I actually need?",
        "You can manage with very few. A spade and a fork for digging and turning compost, a "
        "hand trowel for planting, a rake for levelling the soil, a pair of secateurs and a "
        "watering can with a fine rose are enough for a first year. Buy the best you can "
        "afford, because cheap tools bend and break. Clean them after use and keep them dry, "
        "and a sharp edge on your spade makes digging far easier. Borrow anything else, such as "
        "a wheelbarrow, until you know you need it.",
    ),
    (
        "How do I deal with weeds?",
        "Pull weeds when they are small, before they flower and drop seed, and the job stays "
        "manageable. A hoe slid just under the surface on a dry day cuts off young weeds "
        "quickly. Perennial weeds with deep roots, such as dock and bindweed, need digging out "
        "with as much root as you can lift, because any piece left behind will regrow. Mulch "
        "and close planting both shade the soil and reduce weeds. Little and often beats one "
        "big clear-out.",
    ),
    (
        "Are herbs easy to grow?",
        "Many are among the easiest plants there are. Mint, chives, parsley and thyme thrive "
        "in pots and forgive missed waterings. Mint spreads aggressively, so always keep it in "
        "its own container. Basil likes warmth and sun and does best indoors or in a sheltered "
        "spot. Pick often, since regular cutting keeps herbs bushy and stops them flowering "
        "too soon. A few pots by the kitchen door mean you will actually use them when you cook.",
    ),
    (
        "Are raised beds worth the trouble?",
        "For most beginners, yes. Raised beds warm up sooner in spring, drain better in wet "
        "weather, and let you fill them with good soil whatever lies underneath. Because you "
        "never walk on the soil it stays loose and easy to work. A bed about a metre and a "
        "quarter wide lets you reach the middle from either side. Timber, sleepers or even "
        "old scaffold boards will do for the sides. They cost more to set up, so start with "
        "one and see how you get on.",
    ),
    (
        "How should I plan the year?",
        "Work backwards from the seasons. In late winter, decide what you want to eat and order "
        "seeds. In spring, sow hardy crops first and tender ones after the last frost. In "
        "summer, water, feed, weed and harvest steadily, and sow a few quick crops like "
        "radishes every fortnight so there is always something ready. In autumn, clear beds, "
        "add compost and plant garlic and broad beans. Write down what worked so next year "
        "starts from experience.",
    ),
    (
        "What should I feed my plants?",
        "Rich soil does most of the work, so start by adding compost or well-rotted manure "
        "before planting. Hungry crops such as tomatoes, squashes and potatoes benefit from a "
        "liquid feed every week or two once they flower or fruit. Leafy crops like spinach "
        "and kale appreciate extra nitrogen early on. Follow the instructions on the pack, "
        "because too much feed gives soft, leafy growth that pests love and can burn roots. "
        "Container plants need feeding more often than plants in the ground.",
    ),
    (
        "Can I grow fruit in a small garden?",
        "Yes. Strawberries thrive in pots and hanging baskets, and a single fruit bush such as "
        "a blackcurrant or gooseberry will crop for many years in a corner. Apples and pears "
        "can be trained flat against a fence as cordons or espaliers, which uses very little "
        "space. Raspberries are easy but spread, so give them their own bed. Choose "
        "self-fertile varieties if you only have room for one tree, and water fruit well while "
        "it is swelling.",
    ),
    (
        "What about growing potatoes?",
        "Potatoes are a rewarding first crop and grow well in large bags or a deep bed. Buy "
        "certified seed potatoes and let them sprout on a bright windowsill for a few weeks, "
        "which is called chitting. Plant them about fifteen centimetres deep in spring, and "
        "draw soil up around the shoots as they grow so the tubers stay covered and do not "
        "turn green. Early varieties are ready in about ten weeks; maincrops take longer but "
        "store better.",
    ),
    (
        "Can I save my own seed?",
        "You can, and beans, peas and lettuce are the easiest to begin with. Let a few of the "
        "healthiest plants go to seed instead of eating them, and wait until the pods or heads "
        "are dry and brown before collecting. Spread the seed out to dry fully indoors, then "
        "store it in labelled paper envelopes somewhere cool and dark. Seed saved from hybrid "
        "varieties, marked F1 on the packet, will not come true, so use open-pollinated types "
        "instead.",
    ),
    (
        "Do I have to thin out seedlings?",
        "Yes, and it feels ruthless but it works. Seedlings that are too close compete for "
        "light, water and nutrients, so none of them grow well. Thin in stages, removing the "
        "weakest first, until the plants are at the spacing shown on the seed packet. Snip "
        "them with scissors rather than pulling, so you do not disturb the roots of the ones "
        "you keep. Thin carrots in the evening, because the smell of bruised leaves attracts "
        "carrot fly.",
    ),
    (
        "How can I attract pollinators?",
        "Plant flowers alongside your vegetables. Open, simple blooms such as marigolds, "
        "borage, calendula and cosmos are loved by bees and hoverflies, and they bring "
        "beneficial insects that eat aphids too. Let a few herbs flower, and avoid spraying "
        "insecticides, which harm the good insects as well as the bad. A shallow dish of "
        "water with stones for perching helps in hot weather, and a small pile of logs gives "
        "solitary bees somewhere to nest.",
    ),
    (
        "What should I do in winter?",
        "Winter is a quieter season, but not idle. Clear spent plants, spread compost or "
        "manure over the beds and leave worms to draw it down. Clean and oil your tools, wash "
        "pots to remove disease, and check stored produce for rot. Hardy crops such as kale, "
        "leeks and winter lettuce can keep cropping under a cloche or fleece. Use the time "
        "to plan next year, order seeds and mend fences and raised beds before spring arrives.",
    ),
    (
        "How much time does a small garden take?",
        "A small plot needs about two to three hours a week in the busy months, spread across "
        "a few short visits. Spring is the heaviest, with sowing, planting and preparing beds. "
        "Summer is mostly watering, weeding and picking. Autumn and winter ask for very "
        "little. Watering by hand can be the biggest chore, so mulching, a water butt and "
        "sensible plant spacing all save time. Little and often suits most people better than "
        "a long session once a week.",
    ),
]


def messages() -> list[dict[str, str]]:
    """The whole conversation, oldest first: the instruction, the exchanges, the question."""
    turns = [{"role": "system", "content": INSTRUCTION}]
    for question, answer in EARLIER_EXCHANGES:
        turns.append({"role": "user", "content": question})
        turns.append({"role": "assistant", "content": answer})
    turns.append({"role": "user", "content": FINAL_QUESTION})
    return turns
