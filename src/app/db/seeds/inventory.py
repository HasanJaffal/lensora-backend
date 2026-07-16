from decimal import Decimal

from app.db.seeds.types import InventorySeed

# qty vs threshold is tuned to exercise every derived state (FR-STK-3):
# In stock (qty > threshold), Low (0 < qty <= threshold), Out (qty = 0).
INVENTORY_ITEMS: tuple[InventorySeed, ...] = (
    # Eyeglass frames
    InventorySeed(
        category="frame", name="Wayfarer Classic", brand="Ray-Ban", spec="52-18-145",
        shape="wayfarer", color="Black", sku="FRM-RB-WAY-BLK",
        qty=6, threshold=2, price=Decimal("145.00"),
    ),
    InventorySeed(
        category="frame", name="Holbrook", brand="Oakley", spec="55-17-137",
        shape="rectangular", color="Gunmetal", sku="FRM-OAK-RCT-GRY",
        qty=4, threshold=2, price=Decimal("130.00"),
    ),
    InventorySeed(
        category="frame", name="Butterfly", brand="Vogue", spec="53-16-140",
        shape="cat-eye", color="Tortoise", sku="FRM-VOG-CAT-TRT",
        qty=3, threshold=3, price=Decimal("95.00"),
    ),
    InventorySeed(
        category="frame", name="Round Metal", brand="Persol", spec="49-20-145",
        shape="round", color="Gold", sku="FRM-PRS-RND-GLD",
        qty=5, threshold=2, price=Decimal("160.00"),
    ),
    InventorySeed(
        category="frame", name="Clubmaster Optical", brand="Tom Ford", spec="51-21-145",
        shape="clubmaster", color="Brown", sku="FRM-TOM-CLB-BRN",
        qty=0, threshold=2, price=Decimal("210.00"),
    ),
    InventorySeed(
        category="frame", name="Sport Wrap", brand="Nike", spec="57-16-140",
        shape="sport", color="Blue", sku="FRM-NIK-SPT-BLU",
        qty=7, threshold=3, price=Decimal("120.00"),
    ),
    InventorySeed(
        category="frame", name="Rectangular Acetate", brand="Gucci", spec="54-18-145",
        shape="rectangular", color="Black", sku="FRM-GUC-RCT-BLK",
        qty=2, threshold=2, price=Decimal("240.00"),
    ),
    InventorySeed(
        category="frame", name="Round Slim", brand="Emporio Armani", spec="50-19-140",
        shape="round", color="Silver", sku="FRM-EMP-RND-SLV",
        qty=8, threshold=3, price=Decimal("135.00"),
    ),
    # Sunglasses
    InventorySeed(
        category="sun", name="Aviator", brand="Ray-Ban", spec="58-14-135",
        shape="aviator", color="Gold", sku="SUN-RB-AVI-GLD",
        qty=5, threshold=2, price=Decimal("165.00"),
    ),
    InventorySeed(
        category="sun", name="Radar EV", brand="Oakley", spec="59-13-130",
        shape="sport", color="Black", sku="SUN-OAK-SPT-BLK",
        qty=4, threshold=2, price=Decimal("175.00"),
    ),
    InventorySeed(
        category="sun", name="Steve", brand="Persol", spec="54-18-145",
        shape="wayfarer", color="Brown", sku="SUN-PRS-WAY-BRN",
        qty=0, threshold=2, price=Decimal("190.00"),
    ),
    InventorySeed(
        category="sun", name="Cat-Eye Sun", brand="Vogue", spec="55-17-140",
        shape="cat-eye", color="Black", sku="SUN-VOG-CAT-BLK",
        qty=3, threshold=2, price=Decimal("110.00"),
    ),
    InventorySeed(
        category="sun", name="Clubmaster Sun", brand="Ray-Ban", spec="51-21-145",
        shape="clubmaster", color="Tortoise", sku="SUN-RB-CLB-TRT",
        qty=1, threshold=3, price=Decimal("155.00"),
    ),
    # Ophthalmic stock lenses / coating treatments
    InventorySeed(
        category="lens", name="Single Vision 1.50 Clear", brand="Essilor",
        spec="SV 1.50", sku="LNS-SV-150-CLR",
        qty=20, threshold=8, price=Decimal("40.00"),
    ),
    InventorySeed(
        category="lens", name="Single Vision 1.60 AR", brand="Essilor",
        spec="SV 1.60 + AR", sku="LNS-SV-160-AR",
        qty=12, threshold=6, price=Decimal("85.00"),
    ),
    InventorySeed(
        category="lens", name="Progressive 1.67", brand="Varilux",
        spec="Progressive 1.67", sku="LNS-PROG-167",
        qty=6, threshold=6, price=Decimal("175.00"),
    ),
    InventorySeed(
        category="lens", name="Anti-Blue 1.50", brand="Hoya",
        spec="SV 1.50 + Blue", sku="LNS-BLUE-150",
        qty=15, threshold=8, price=Decimal("70.00"),
    ),
    InventorySeed(
        category="lens", name="Photochromic 1.60", brand="Transitions",
        spec="SV 1.60 Photo", sku="LNS-PHOTO-160",
        qty=0, threshold=4, price=Decimal("110.00"),
    ),
    # Contact lenses
    InventorySeed(
        category="contact", name="Moist Daily 30pk", brand="Acuvue",
        spec="Daily disposable", sku="CON-ACV-MOIST-30",
        qty=25, threshold=10, price=Decimal("28.00"),
    ),
    InventorySeed(
        category="contact", name="Monthly 6pk", brand="Biofinity",
        spec="Monthly", sku="CON-BIOF-MONTH-6",
        qty=14, threshold=6, price=Decimal("35.00"),
    ),
    InventorySeed(
        category="contact", name="Toric Daily 30pk", brand="Dailies",
        spec="Astigmatism daily", sku="CON-DAI-TOR-30",
        qty=4, threshold=5, price=Decimal("42.00"),
    ),
    InventorySeed(
        category="contact", name="Night & Day 6pk", brand="Air Optix",
        spec="Extended wear", sku="CON-AIR-NIGHT-6",
        qty=0, threshold=4, price=Decimal("48.00"),
    ),
    # Solutions & drops
    InventorySeed(
        category="solution", name="Multi-Purpose 360ml", brand="Opti-Free",
        spec="360ml", sku="SOL-OPTI-360",
        qty=18, threshold=8, price=Decimal("12.00"),
    ),
    InventorySeed(
        category="solution", name="Multi-Purpose 240ml", brand="Renu",
        spec="240ml", sku="SOL-RENU-240",
        qty=9, threshold=6, price=Decimal("9.00"),
    ),
    InventorySeed(
        category="solution", name="Lubricant Drops 10ml", brand="Systane",
        spec="10ml", sku="SOL-SYS-DROP-10",
        qty=3, threshold=5, price=Decimal("8.00"),
    ),
    # Care accessories
    InventorySeed(
        category="care", name="Microfiber Cloth", brand="Lensora",
        spec="Cleaning cloth", sku="CAR-CLOTH-MF",
        qty=40, threshold=15, price=Decimal("3.00"),
    ),
    InventorySeed(
        category="care", name="Lens Cleaning Spray 50ml", brand="Lensora",
        spec="50ml spray", sku="CAR-SPRAY-50",
        qty=22, threshold=10, price=Decimal("6.00"),
    ),
    InventorySeed(
        category="care", name="Hard Glasses Case", brand="Lensora",
        spec="Protective case", sku="CAR-CASE-HRD",
        qty=0, threshold=6, price=Decimal("5.00"),
    ),
)
