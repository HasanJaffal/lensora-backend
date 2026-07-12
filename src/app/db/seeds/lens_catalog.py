from decimal import Decimal

from app.db.seeds.types import LensOptionSeed

LENS_TYPES: tuple[LensOptionSeed, ...] = (
    LensOptionSeed(
        name_en="Single Vision",
        name_ar="رؤية أحادية",
        description_en="One corrective power across the whole lens for distance or near.",
        description_ar="قوة تصحيح واحدة عبر العدسة بالكامل للرؤية البعيدة أو القريبة.",
        price=Decimal("40.00"),
    ),
    LensOptionSeed(
        name_en="Bifocal Flat-Top",
        name_ar="ثنائية البؤرة بقمة مسطحة",
        description_en="Distance and near zones split by a visible flat-top segment.",
        description_ar="منطقتا الرؤية البعيدة والقريبة مفصولتان بجزء ذي قمة مسطحة مرئية.",
        price=Decimal("70.00"),
    ),
    LensOptionSeed(
        name_en="Progressive / Varilux",
        name_ar="متدرجة / فاريلوكس",
        description_en="Seamless distance-to-near transition with no visible line.",
        description_ar="انتقال سلس من البعيد إلى القريب دون خط مرئي.",
        price=Decimal("120.00"),
    ),
    LensOptionSeed(
        name_en="Office / Computer",
        name_ar="مكتبية / كمبيوتر",
        description_en="Extended intermediate zone tuned for screen and desk work.",
        description_ar="منطقة وسطى موسّعة مهيأة للعمل على الشاشة والمكتب.",
        price=Decimal("90.00"),
    ),
)

LENS_MATERIALS: tuple[LensOptionSeed, ...] = (
    LensOptionSeed(
        name_en="Standard 1.50",
        name_ar="قياسية 1.50",
        description_en="Standard-thickness plastic lens, included at no extra cost.",
        description_ar="عدسة بلاستيكية بسماكة قياسية، مشمولة دون تكلفة إضافية.",
        price=Decimal("0.00"),
    ),
    LensOptionSeed(
        name_en="Thin 1.60",
        name_ar="رقيقة 1.60",
        description_en="Thinner and lighter than standard, good for moderate powers.",
        description_ar="أرق وأخف من القياسية، مناسبة للقوى المتوسطة.",
        price=Decimal("25.00"),
    ),
    LensOptionSeed(
        name_en="Ultra-thin 1.67",
        name_ar="فائقة الرقة 1.67",
        description_en="Noticeably slimmer profile for stronger prescriptions.",
        description_ar="سماكة أقل بوضوح للوصفات الأقوى.",
        price=Decimal("55.00"),
    ),
    LensOptionSeed(
        name_en="High-index 1.74",
        name_ar="معامل انكسار عالٍ 1.74",
        description_en="Thinnest available option for the strongest prescriptions.",
        description_ar="الخيار الأنحف المتاح لأقوى الوصفات.",
        price=Decimal("90.00"),
    ),
)

LENS_COATINGS: tuple[LensOptionSeed, ...] = (
    LensOptionSeed(
        name_en="Anti-Reflective",
        name_ar="مضاد للانعكاس",
        description_en="Cuts glare and reflections for clearer vision and night driving.",
        description_ar="يقلل الوهج والانعكاسات لرؤية أوضح وقيادة ليلية أفضل.",
        price=Decimal("20.00"),
    ),
    LensOptionSeed(
        name_en="Anti-Blue",
        name_ar="مضاد للضوء الأزرق",
        description_en="Filters blue light from screens to ease digital eye strain.",
        description_ar="يرشّح الضوء الأزرق من الشاشات لتخفيف إجهاد العين الرقمي.",
        price=Decimal("30.00"),
    ),
    LensOptionSeed(
        name_en="Scratch-resistant",
        name_ar="مقاوم للخدش",
        description_en="Hardened surface that better withstands daily wear.",
        description_ar="سطح مقوّى يتحمل الاستخدام اليومي بشكل أفضل.",
        price=Decimal("15.00"),
    ),
    LensOptionSeed(
        name_en="UV Protection",
        name_ar="حماية من الأشعة فوق البنفسجية",
        description_en="Blocks harmful UV rays to protect long-term eye health.",
        description_ar="يحجب الأشعة فوق البنفسجية الضارة لحماية صحة العين على المدى الطويل.",
        price=Decimal("10.00"),
    ),
    LensOptionSeed(
        name_en="Photochromic",
        name_ar="متلون ضوئياً",
        description_en="Darkens in sunlight and clears indoors automatically.",
        description_ar="يعتم تحت أشعة الشمس ويصفو في الداخل تلقائياً.",
        price=Decimal("60.00"),
    ),
)

LENS_TINTS: tuple[LensOptionSeed, ...] = (
    LensOptionSeed(
        name_en="Clear",
        name_ar="شفاف",
        description_en="No tint, included at no extra cost.",
        description_ar="بدون صبغة، مشمول دون تكلفة إضافية.",
        price=Decimal("0.00"),
    ),
    LensOptionSeed(
        name_en="Photo Gray",
        name_ar="رمادي ضوئي",
        description_en="Light-reactive gray tint, included at no extra cost.",
        description_ar="صبغة رمادية تتفاعل مع الضوء، مشمولة دون تكلفة إضافية.",
        price=Decimal("0.00"),
    ),
    LensOptionSeed(
        name_en="Solid Gray",
        name_ar="رمادي ثابت",
        description_en="Fixed gray tint for consistent sun protection.",
        description_ar="صبغة رمادية ثابتة لحماية شمسية متسقة.",
        price=Decimal("15.00"),
    ),
    LensOptionSeed(
        name_en="Brown",
        name_ar="بني",
        description_en="Warm brown tint that enhances contrast.",
        description_ar="صبغة بنية دافئة تعزز التباين.",
        price=Decimal("15.00"),
    ),
    LensOptionSeed(
        name_en="G-15 Green",
        name_ar="أخضر جي-15",
        description_en="Classic green tint that preserves natural color.",
        description_ar="صبغة خضراء كلاسيكية تحافظ على الألوان الطبيعية.",
        price=Decimal("15.00"),
    ),
)
