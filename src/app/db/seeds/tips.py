from app.db.seeds.types import TipSeed

TIPS: tuple[TipSeed, ...] = (
    TipSeed(
        category="screen",
        tags=("screen", "myopia", "astigmatism"),
        icon="monitor",
        color="sky",
        title_en="Follow the 20-20-20 rule",
        title_ar="اتبع قاعدة 20-20-20",
        body_en="Every 20 minutes, look at something 20 feet away for 20 seconds to relax "
        "your eyes and reduce digital strain.",
        body_ar="كل 20 دقيقة، انظر إلى شيء يبعد 20 قدماً لمدة 20 ثانية لإراحة عينيك وتقليل "
        "الإجهاد الرقمي.",
    ),
    TipSeed(
        category="screen",
        tags=("screen", "presbyopia"),
        icon="shield",
        color="indigo",
        title_en="Add an anti-blue coating for screen work",
        title_ar="أضف طلاءً مضاداً للضوء الأزرق للعمل على الشاشة",
        body_en="If you spend hours on screens daily, an anti-blue coating can ease eye "
        "fatigue and help you sleep better.",
        body_ar="إذا كنت تقضي ساعات يومياً أمام الشاشات، فقد يخفف الطلاء المضاد للضوء الأزرق "
        "إجهاد العين ويحسّن نومك.",
    ),
    TipSeed(
        category="lensCare",
        tags=("non-Rx", "screen"),
        icon="droplet",
        color="cyan",
        title_en="Clean lenses the right way",
        title_ar="نظّف العدسات بالطريقة الصحيحة",
        body_en="Rinse lenses under water, then use a drop of lens spray and a microfiber "
        "cloth. Never wipe dry lenses — grit scratches them.",
        body_ar="اشطف العدسات بالماء، ثم استخدم قطرة من بخاخ العدسات وقطعة قماش دقيقة الألياف. "
        "لا تمسح العدسات وهي جافة — فالأتربة تخدشها.",
    ),
    TipSeed(
        category="lensCare",
        tags=("non-Rx",),
        icon="package",
        color="teal",
        title_en="Store glasses in a hard case",
        title_ar="احفظ النظارات في علبة صلبة",
        body_en="Always place glasses in a hard case when not worn, folded arms first, to "
        "protect the coating and keep the frame aligned.",
        body_ar="ضع النظارات دائماً في علبة صلبة عند عدم استخدامها، مع طي الذراعين أولاً، "
        "لحماية الطلاء والحفاظ على محاذاة الإطار.",
    ),
    TipSeed(
        category="adapting",
        tags=("progressive", "presbyopia"),
        icon="glasses",
        color="violet",
        title_en="Give progressives a week",
        title_ar="امنح العدسات المتدرجة أسبوعاً",
        body_en="Move your head, not just your eyes, to find each zone. Most people adapt "
        "to progressive lenses within one to two weeks.",
        body_ar="حرّك رأسك، لا عينيك فقط، لتجد كل منطقة. يتأقلم معظم الناس مع العدسات "
        "المتدرجة خلال أسبوع إلى أسبوعين.",
    ),
    TipSeed(
        category="adapting",
        tags=("astigmatism", "myopia"),
        icon="clock",
        color="amber",
        title_en="Wear new glasses full-time at first",
        title_ar="ارتدِ النظارات الجديدة طوال الوقت في البداية",
        body_en="A new astigmatism correction can feel off for a few days. Wear it "
        "consistently so your eyes adjust faster.",
        body_ar="قد يبدو تصحيح الاستجماتيزم الجديد غريباً لبضعة أيام. ارتدِه باستمرار لتتكيف "
        "عيناك بشكل أسرع.",
    ),
    TipSeed(
        category="children",
        tags=("child", "myopia"),
        icon="sun",
        color="lime",
        title_en="More outdoor time slows myopia",
        title_ar="المزيد من الوقت في الخارج يبطئ قصر النظر",
        body_en="Around two hours of daylight a day is linked to slower myopia progression "
        "in children. Encourage outdoor play.",
        body_ar="يرتبط قضاء نحو ساعتين في ضوء النهار يومياً بتباطؤ تطور قصر النظر لدى "
        "الأطفال. شجّع اللعب في الهواء الطلق.",
    ),
    TipSeed(
        category="children",
        tags=("child", "screen"),
        icon="baby",
        color="rose",
        title_en="Set screen limits for young eyes",
        title_ar="ضع حدوداً للشاشة لأعين الصغار",
        body_en="Keep screens at arm's length, take frequent breaks, and cap recreational "
        "screen time to protect developing vision.",
        body_ar="أبقِ الشاشات على مسافة ذراع، وخذ فترات راحة متكررة، وحدّد وقت الشاشة "
        "الترفيهي لحماية البصر النامي.",
    ),
    TipSeed(
        category="sunUv",
        tags=("sun", "child"),
        icon="sun",
        color="orange",
        title_en="Protect eyes from UV year-round",
        title_ar="احمِ العينين من الأشعة فوق البنفسجية طوال العام",
        body_en="UV rays reach the eyes even on cloudy days. Wear sunglasses with full UV "
        "protection outdoors, especially near water.",
        body_ar="تصل الأشعة فوق البنفسجية إلى العينين حتى في الأيام الغائمة. ارتدِ نظارات "
        "شمسية بحماية كاملة في الخارج، خاصة قرب الماء.",
    ),
    TipSeed(
        category="sunUv",
        tags=("sun", "progressive"),
        icon="car",
        color="yellow",
        title_en="Photochromics don't darken in the car",
        title_ar="العدسات المتلونة لا تعتم داخل السيارة",
        body_en="Windshields block the UV that triggers photochromic lenses, so they stay "
        "clear while driving. Keep sunglasses for the road.",
        body_ar="يحجب الزجاج الأمامي الأشعة فوق البنفسجية التي تفعّل العدسات المتلونة، لذا "
        "تبقى شفافة أثناء القيادة. احتفظ بنظارة شمسية للطريق.",
    ),
)
