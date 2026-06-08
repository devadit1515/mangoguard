# Mango Farm Monitoring Landscape (Konkan Alphonso, 2024-2026)

A primary-source brief for the CREST project. Audience: a Grade 11 student designing an AI orchard-management tool for a "rich mid-sized" Konkan Alphonso grower (~10 acres, partially absentee, smartphone user, no current IoT). Focus: what monitoring data is actually obtainable today, at what cost, and how much accuracy the cheapest realistic setup gives up versus a full commercial service.

---

## A1. Commercial Agri-IoT Services in Indian Orchards

**Fyllo (AgriHawk Technologies, Bengaluru)** is the most relevant commercial player because (a) it cut hardware prices into a range a "rich mid-sized" Konkan farmer can absorb in 2024, and (b) it already has a strong vineyard/horticulture footprint in western Maharashtra. Fyllo launched single-sensor devices at INR 6,000 and dual-sensor versions at INR 8,000 in April 2024, after its imported moisture sensors had previously sold for around INR 22,000; the price cut drove bookings from 200-300 a month to roughly 8,000 in a single month [Inc42, "How Fyllo Firms Up Farm Decisions Using IoT And Precision Weather Forecasts" — https://inc42.com/startups/how-fyllo-firms-up-farm-decisions-using-iot-and-precision-weather-forecasts/]. Its higher-end "Nero" multi-depth soil probe is INR 16,000, and the full weather + canopy "Kairo" station is INR 45,000 [Inc42, ibid]. As of mid-2024 Fyllo had "onboarded more than 7,000 farmers and deployed 6,000 devices across 13 states... for 22 crops" and raised USD 4M led by India Quotient and SIDBI [Entrackr, May 2024 — https://entrackr.com/2024/05/fyllo-raises-4-mn-led-by-india-quotient-and-sidbi-ventures/]. Fyllo originally built its disease-risk models on Nashik table-grape farms — "Team Fyllo shifted base to Nashik to develop the product with farmers" — and a documented success was Roshan Zalte's 15-acre vineyard, where Fyllo's downy-mildew alert was delivered through the mobile app [The Better India — https://thebetterindia.com/247857/agritech-sumit-sheoran-sudhanshu-rai-startup-fyllo-bengaluru-agriculture-farming-water-conservation-success-story-him16/]. Crops officially supported are "grapes, capsicum, tomato, potato and pomegranate," with mango not on the published list [ibid]; this is important — Fyllo's disease engines for anthracnose/powdery mildew of mango are not advertised as production-grade.

**Fasal (Wolkus Technology, Bengaluru)** is the other serious option. Its plug-and-play device "is equipped with over 12 sensors that monitor a range of climatic and soil parameters" and pushes pest/disease and irrigation advisories [The Better India — https://thebetterindia.com/changemakers/fasal-kranti-iot-ai-transforming-indian-farming-uttar-pradesh-10627593]. Fasal does not publish open pricing; it is sold as an annual subscription bundle (typically ~INR 25,000-40,000 for the first year per node based on reseller listings; this is not on the official site and should be treated as indicative).

**CropIn** is a SaaS layer rather than a hardware vendor — it "digitized a total of 16 million acres of farmland globally" and partners with FPOs and exporters [AWS-CropIn case study — https://pages.awscloud.com/rs/112-TZM-766/images/aws-cropin-case-study-with-Intel.pdf]. Relevant to the Konkan use case via processors and aggregators, not direct-to-farmer sales.

**BharatRohan** sells drone-flight-as-a-service (hyperspectral imagery) rather than fixed sensors: it "empowers over 50,000 farmers across seven states... reducing pesticide use" [The Better India — https://thebetterindia.com/441296/two-engineers-amandeep-panwar-rishabh-choudhary-drone-technology-agriculture-india-crop-protection], with NITI Aayog explicitly highlighting its hyperspectral mango/orchard use case [NITI Frontier Tech — https://frontiertech.niti.gov.in/story/drone-based-hyperspectral-imaging-transforming-indian-agriculture-for-sustainable-growth/].

**Konkan-specific evidence:** the largest documented sustainable-mango program in Ratnagiri is IDH's Project Farm Gate 2.0 with Riedel and Foods & Inns, targeting "100+ smallholder Alphonso mango farmers in the region of Ratnagiri in Konkan India" for FSA Silver verification [IDH — https://www.idhsustainabletrade.com/project/farm-gate-2-0-sustainable-mango-farming-in-india/]. The publicly visible project documents emphasize agronomist visits, pesticide management and traceability rather than blanket IoT deployment — i.e., even the well-funded sustainability programs in Ratnagiri are not yet putting a Fyllo/Fasal node on every farm.

---

## A2. Government, KVK and ICAR Monitoring Programmes

**IMD's Gramin Krishi Mausam Sewa (GKMS)** runs about 130 Agro-Meteorological Field Units (AMFUs) plus a sub-network of District Agro-Met Units (DAMUs). They "make Agro-AWS data available for block-level agromet advisory services bulletin preparation" and issue advisories twice a week [IMD GKMS SOP — https://mausam.imd.gov.in/imd_latest/contents/pdf/gkms_sop.pdf; IMD Agromet Advisory portal — https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php]. The CSE assessment notes that AMFUs "employ meteorologists and crop experts to generate agromet advisories" [CSE — https://cdn.cseindia.org/attachments/0.65638100_1587639351_agromet.pdf].

**Meghdoot app (IMD + IITM + ICAR)** is the consumer-facing front-end and is the single most useful free tool for a Konkan farmer: "the app seamlessly aggregates contextualised district and crop wise advisories issued by Agro Met Field Units (AMFU) every Tuesday and Friday with the forecast and historic weather information" [PIB — https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1739245]. Maharashtra received 30,938 advisories through Meghdoot by July 2021 — the second-highest of any state [Academia.edu mirror of the published Meghdoot paper — https://www.academia.edu/80091536/Meghdoot_A_Mobile_App_to_Access_Location_Specific_Weather_Based_Agro_Advisories_Pan_India].

**Dr Balasaheb Sawant Konkan Krishi Vidyapeeth (DBSKKV), Dapoli** is the AMFU for Konkan and the agronomic authority on Alphonso. It hosts a public weather-forecast page for the Farmers' Corner [DBSKKV — https://www.dbskkv.org/farmers-corner/weather-forecast]. DBSKKV is the same institute that bred the Alphonso-alternative variety 'Sindhu' over 15+ years [The Better India — https://thebetterindia.com/farming/sindhu-mango-konkan-farmers-alphonso-alternative-dapoli-dbskkv-maharashtra-hapus-11799197], so its district-level advisories are calibrated for Konkan mango phenology.

**ICAR-CISH (Central Institute for Subtropical Horticulture), Lucknow** publishes the technical IPM bulletins that any disease-risk engine should be aligned with — see, for example, the public IPM page for mango hopper and inflorescence midge [CISH — https://cish.icar.gov.in/ipm_MangoHopper.php; https://cish.icar.gov.in/ipm_InflorescenceMidge.php]. CISH has explicitly developed "smart orchards for mango and guava... integrat[ing] sensor technology, weather monitoring, the Internet of Things (IoT), automation, decision-support tools, and traceability" [Indian Horticulture (ICAR e-pub) — https://epubs.icar.org.in/index.php/IndHort/article/view/177199].

**Maharashtra-specific government monitoring — CROPSAP.** The Maharashtra Department of Agriculture has run an "e-pest surveillance" programme (CROPSAP) "since 2009, involving extension functionaries and farmers... currently being implemented in about 170 lakh hectare in Maharashtra" with mango pests including "hoppers, thrips, powdery mildew and anthracnose" explicitly named [CROPSAP portal — https://cropsap.maharashtra.gov.in/; NCIPM CROPSAP report — https://ncipm.icar.gov.in/NCIPMPDFs/FOLDERS/CROPSAPBookforWEB_.pdf]. There is a paired M-Cropsap Android app [https://cropsap.maharashtra.gov.in/Mcropsap/]. For a student tool, CROPSAP is a free authoritative ground-truth feed worth integrating.

**NABARD / APEDA subsidy:** there is no dedicated APEDA-NABARD scheme for farm sensors. The relevant umbrella is the Agriculture Infrastructure Fund (3% interest subvention, up to INR 2 crore loan cap), under which "smart-precision-agriculture equipment is included among community-farming assets that can be financed" — i.e., at the FPO/cooperative scale, not the individual mid-sized farmer [agri.bot AIF summary — https://agri.bot/aif; NABARD schemes list — https://www.nabard.org/content1.aspx?id=23].

---

## A3. Realistic Sensor Hardware in the INR 5k-30k Window

What an Indian farmer (or a CREST student) can actually buy off-the-shelf in 2025-26:

- **ESP32 dev board:** "ESP32 development boards typically range between INR 300-600 in India" [ThinkRobotics guide — https://thinkrobotics.com/blogs/learn/esp32-development-board-projects-a-beginner-s-guide-for-indian-makers].
- **Capacitive soil-moisture sensor (corrosion-resistant):** TechnoSam capacitive V2.0 on Amazon.in, ~INR 200-300 each [https://www.amazon.in/TechnoSam-Capacitive-Anti-Corrosion-Compatible-Development/dp/B0B21LRMZK]. DFRobot IP65 waterproof gravity version (rated for "long-term outdoor gardening") for ~INR 1,200-1,800 [DFRobot — https://www.dfrobot.com/product-2054.html].
- **Leaf-wetness sensor (Renke RS-485, -40 to +60 C, IP67, "measures wetness through changes in leaf surface dielectric constant... can detect trace water or ice residues"):** sold on Robu.in [https://robu.in/product/leaf-wetness-sensor-type-rs485/]. Street price typically INR 4,500-6,500. This is the single most useful sensor for mango anthracnose/powdery-mildew risk modelling.
- **Tipping-bucket rain gauge:** FirstRate FST100-2008 (RS-485, 0.2 mm resolution) on Robu.in [https://robu.in/product/firstrate-fst100-2008-tipping-bucket-rain-gauge/]; DFRobot Gravity I2C/UART tipping bucket [https://robu.in/product/dfrobot-gravity-tipping-bucket-rainfall-sensor-i2c-uart/]; Renke RS-YL-PL-2-02-EX ABS bucket [https://robu.in/product/renke-rs-yl-pl-2-02-ex-tipping-bucket-rain-gauge/]. Indian indiamart listings start at "INR 10,000/piece" for industrial-grade units [https://www.indiamart.com/proddetail/tipping-bucket-rain-gauge-sensor-23562191630.html]; hobby-grade DFRobot units land closer to INR 3,000-4,500.
- **Air temp + humidity:** DHT22 (~INR 300) or SHT31 (~INR 700) on Robu.in. BMP280 barometric pressure ~INR 200.
- **Reference all-in-one station for context:** DFRobot Lark portable weather station (wind, direction, T, RH, pressure, ESP32-compatible) — listed on Robu.in [https://robu.in/product/dfrobot-lark-weather-station-portable-educational-weather-device-compatible-with-arduino-microbit-esp32/], typically INR 12,000-15,000.
- **Pessl iMETOS commercial-grade station:** Metos Instruments India Pvt Ltd, Delhi (est. 1993) is the official reseller [https://www.indiamart.com/metos-instruments-india-pvt-ltd/]; the iMETOS 3.3 is "a durable and flexible data logger... powered by rechargeable battery and a solar panel" with FieldClimate platform + built-in disease models [Pessl — https://metos.global/en/imetos33/]. List price is undisclosed but enterprise — well above the brief's INR 30k ceiling (typically INR 1.5-3 lakh installed). Same applies to HOBO / Tinytag.

Bottom line: a DIY ESP32 + DHT22 + BMP280 + capacitive soil moisture + Renke leaf-wetness + tipping-bucket rain gauge comes to **INR 7,000-12,000 in parts**.

---

## A4. DIY and Farmer-Led Setups in Konkan

Documentary evidence of pure DIY IoT on Konkan Alphonso farms is sparse — most published Devgad/Ratnagiri grower content is on harvest, grading and direct-to-consumer logistics (e.g., Ratnagiri Hapus uses "IoT-enabled temperature loggers to track shipments from Mumbai to destination" [https://ratnagirihapus.store/why-some-alphonso-mango-shipments-are-being-rejected-and-how-ratnagiri-hapus-ensures-100-compliance/]) rather than in-orchard sensing. The most cited Indian mango precision-farming case is Suraj Panigraphy's "MangoMaze" in Odisha, where drones, drip and sensors are credited with a 7x yield improvement [The Better India — https://thebetterindia.com/451505/suraj-panigraphy-mangomaze-quantum-density-farming-boost-mango-yield-using-technology/]. In Konkan itself, drip irrigation is mainstream (reported to "reduce water use by 70 percent" on Ratnagiri Alphonso farms [https://thebetterindia.com/farming/sindhu-mango-konkan-farmers-alphonso-alternative-dapoli-dbskkv-maharashtra-hapus-11799197]), but in-orchard sensor logging is still rare enough that any properly instrumented Konkan farm would itself be a publishable case.

---

## A5. Phone-Based Apps Actually Used

**Plantix** is the only image-diagnosis app with serious mango footprint. It has "been downloaded by over 7 million users in India with a database of more than 10.5 million pictures," has expanded "from an initial 30 crop pests and disease combinations to nearly 800 now," and explicitly diagnoses mango anthracnose and dieback [Plantix blog — https://plantix.net/en/blog/plantix-networked-india/; CGIAR Big Data — https://bigdata.cgiar.org/digital-intervention/plant-disease-diagnosis-using-artificial-intelligence-a-case-study-on-plantix/]. It "tracks outbreaks up to district level by leveraging anonymised metadata like GPS coordinates and timestamps" [Plantix blog, ibid] — i.e., the student tool can use Plantix-style image classification as the leaf-symptom feature and combine it with weather-driven disease-risk modelling.

**Krishify** ("12.5 million users as of 2024" [Tractor Junction — https://www.tractorjunction.com/blog/top-10-agricultural-apps-for-smart-farming-solutions/]) is a community/social app — useful as a content channel, not a data source. **IFFCO Kisan** is an advisory app from IFFCO [https://krishijagran.com/agriculture-apps/iffco-kisan-agriculture/]. **Bayer FarmRise** "grew by 66% in growth rate" and moved from 11th to 7th in 2024 app rankings [Chloropy — https://www.chloropy.com/post/india-s-top-agricultural-apps-leading-the-way-in-2024]. None of these are mango-specialised; the IMD's **Meghdoot** remains the single most relevant phone app for a Konkan Alphonso grower (district-level advisories twice weekly, official AMFU content).

---

## B. Data Available WITHOUT Any Farm Sensors

1. **IMD Agromet Advisory Service:** State and AMFU bulletins free at https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php; Meghdoot app pushes them district-wise twice a week. Granularity: district (not block) for most of Konkan in practice.
2. **NASA POWER:** Free API for daily T, RH, radiation, ET0, wind, precip globally, derived from MERRA-2 reanalysis [https://power.larc.nasa.gov/docs/methodology/]. Caveat for Konkan: validation studies show "NASA POWER datasets are more reliable than IMD data for some locations like Ranichauri (at all timescales) and Roorkee" for temperature, but "IMD gridded product outperforms in detecting rainfall events" in monsoon basins [Springer/Theoretical and Applied Climatology — https://link.springer.com/article/10.1007/s00704-023-04787-5; Springer/EMA Narmada study — https://link.springer.com/article/10.1007/s10661-023-12206-5]. So: use NASA POWER for temperature/RH/radiation, prefer IMD gridded data for rainfall.
3. **Open-Meteo:** Free, no API key, "high-resolution open data ranging from 1 to 11 kilometres" by aggregating ECMWF, NOAA, DWD, JMA and others [https://open-meteo.com/]. Best practical free forecast layer for a student app — gives hourly forecast and 80+ years of historical reanalysis in one API.
4. **Sentinel-2 (10 m, 5-day revisit) via Google Earth Engine / Sentinel Hub:** "The revisit frequency of each single Sentinel-2 satellite is 10 days and the combined constellation revisit is 5 days" [Sentinel Hub docs — https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l1c/]. Critical Konkan caveat: "during the monsoon period (July-August), average cloud cover in Western Ghats districts reached 92% or 90% in 2017 and 2018... resulting in 25% or 23% of mapped areas being unmapped" [PMC — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11760589/]. For a ~5 ha orchard, a 10 m pixel gives only ~500 pixels; "Sentinel-2's limited spatial resolution can pose challenges... where the overlapping tree crowns and ground pixels complicate accurate analysis" [arXiv weed-mapping paper — https://arxiv.org/pdf/2504.19991]. NDVI trends are still useful for season-scale canopy stress; pixel-level alerts are not.
5. **AGMARKNET / data.gov.in:** Daily mandi prices for ~200 commodities including mango via the OGD catalog [https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi] and the official AGMARKNET portal [https://agmarknet.gov.in]. Useful for the harvest-timing / marketing module of the student tool.
6. **CROPSAP** [https://cropsap.maharashtra.gov.in/] — taluka-level pest surveillance data for Maharashtra (mango pests explicitly tracked).

---

## C. Accuracy Gap: Free Public vs Single Station vs Commercial Service

The clearest published numbers come from disease models, not raw weather:

- **Mango anthracnose (Colletotrichum gloeosporioides):** the published logistic / regression models "indicated 95% variability in the progression of anthracnose disease with wind speed, relative humidity (morning), and sunshine hours being the most responsive environmental variables... with an R² value of 0.93" [ResearchGate, anthracnose-weather correlation study — https://www.researchgate.net/figure/Correlation-between-mango-anthracnose-severity-and-weather-parameters-2018_fig4_340896997]. Humid Thermal Ratio (HTR) is the single most predictive index.
- **Mango powdery mildew (Oidium mangiferae):** "temperature range of 11-14 C (minimum) and 17-31 C (maximum) along with moderate relative humidity (64-72%) was most congenial" — and "maximum spore occurrences were noted around 25 C and relative humidity of 40-60%" [ResearchGate powdery-mildew correlation — https://www.researchgate.net/figure/Correlation-of-mango-powdery-mildew-with-weather-parameters-Table-r-value-at-5-0396_tbl1_352900148; NHB technical bulletin — https://nhb.gov.in/pdf/fruits/mango/man002.pdf; ICAR forewarning paper — https://www.researchgate.net/publication/291815012_Forewarning_powdery_mildew_caused_by_Oidium_mangiferae_in_mango_Mangifera_indica_using_logistic_regression_models].

What that means in practice for the student's three-tier accuracy comparison:

| Data source | Spatial scale | Anthracnose model usable? | Powdery mildew usable? | Realistic delta |
|---|---|---|---|---|
| (a) Free public only (IMD Agromet + NASA POWER + Open-Meteo + Sentinel-2) | District / 1-11 km | Yes for HTR (morning RH is in the reanalysis), but no in-canopy RH | Yes for coarse temp/RH thresholds | Baseline |
| (b) + single on-farm station (T/RH/leaf-wetness/rain) | Orchard (~5 ha) | Yes — leaf-wetness duration is the missing variable | Yes — canopy-microclimate RH and dew detected | Recovers most of the gap; multiple studies attribute the biggest accuracy lift to leaf-wetness data, not to denser weather forecasts |
| (c) Commercial (Fyllo/Fasal) | Same as (b), plus tuned models | Yes, with vendor model | Yes, with vendor model | Marginal over (b) for the same hardware *if* you have an equivalent model |

The empirical anchor: published mango disease models reach R² ~0.93 with just T, RH, wind and sunshine [ResearchGate, ibid] — variables present in NASA POWER + Open-Meteo. The single biggest accuracy gain from adding a farm station is the **leaf-wetness duration** signal, which no free public dataset provides. There is no peer-reviewed direct comparison of "Fyllo vs DIY station vs free public" for Konkan mango in the public literature as of 2024-26; closest analogs are vineyard studies (Fyllo's own Nashik origin).

---

## D. Concrete Recommendation for the Student

For a partially absentee owner of ~10 acres of Konkan Alphonso, with a smartphone and no current IoT, the most plausible monitoring stack that the student can either *tap* (free) or *build* (under INR 15,000) is:

**Free public data layer (zero rupees, code-only).**
1. Open-Meteo hourly forecast + ERA5 historical [https://open-meteo.com/].
2. NASA POWER daily for ET0 and historical climatology [https://power.larc.nasa.gov/].
3. IMD Meghdoot district advisory (scraped or via the official app) [https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php].
4. DBSKKV Dapoli weather-forecast page for Konkan-tuned advisories [https://www.dbskkv.org/farmers-corner/weather-forecast].
5. CROPSAP Maharashtra pest data [https://cropsap.maharashtra.gov.in/].
6. Sentinel-2 NDVI 5-day composites via Google Earth Engine — used for **seasonal canopy-vigour trend per block** (not pixel alerts), with explicit fallback to Sentinel-1 SAR during the monsoon to bypass the 90%+ cloud-cover blackout.
7. AGMARKNET mandi prices via OGD API for the marketing module [https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi].

**One DIY in-orchard node (~INR 7,000-12,000).** Single ESP32-based logger, solar-powered, LoRa or 4G hotspot uplink, placed in the canopy near a representative block. Bill of materials, all from Robu.in, Amazon.in or ElectronicsComp:
- ESP32 dev board: ~INR 500
- DHT22 or SHT31 air T/RH: ~INR 700
- BMP280 pressure: ~INR 200
- Capacitive soil moisture (TechnoSam V2 or DFRobot IP65): ~INR 1,500 (DFRobot waterproof) [https://www.amazon.in/TechnoSam-Capacitive-Anti-Corrosion-Compatible-Development/dp/B0B21LRMZK; https://www.dfrobot.com/product-2054.html]
- Renke leaf-wetness sensor RS-485 (the highest-leverage sensor for mango disease risk): ~INR 5,500 [https://robu.in/product/leaf-wetness-sensor-type-rs485/]
- DFRobot Gravity tipping-bucket rain gauge: ~INR 3,500-4,500 [https://robu.in/product/dfrobot-gravity-tipping-bucket-rainfall-sensor-i2c-uart/]
- Solar panel + 18650 + TP4056 + enclosure: ~INR 1,500
- Total: **INR 13,000-14,000**.

**Why this beats the alternatives at this price point.**
- It captures the **one variable (leaf-wetness duration) that the free public stack cannot give**, and that variable is what closes most of the disease-prediction R² gap to a commercial service.
- It uses sensors whose accuracy class is documented (Renke RS-485, DFRobot Gravity) rather than INR 30 hobbyist resistive probes.
- It is owned outright by the farmer — no recurring INR 25k+/year subscription, which matters because a "rich mid-sized" partially absentee owner of a 10-acre orchard does not yet have a documented commercial-IoT deployment in the IDH/Farm Gate or Fyllo case-study literature for Konkan.

**Effort estimate for the student:** 2-3 weekends to build and test the node; 1-2 weeks of API integration (Open-Meteo + POWER + GEE + AGMARKNET); 1 week to wire in the mango-anthracnose (HTR) and powdery-mildew (temperature-band x RH) risk models from the published ICAR/CISH coefficients [https://www.researchgate.net/figure/Correlation-between-mango-anthracnose-severity-and-weather-parameters-2018_fig4_340896997; https://nhb.gov.in/pdf/fruits/mango/man002.pdf].

**Upgrade path (optional, if the farmer later wants to buy in):** add one Fyllo "Nero" multi-depth soil probe at INR 16,000 [Inc42, ibid] for a second irrigation/fertigation block. This keeps the student's free-data + DIY-node architecture as the spine and uses commercial hardware only where it pays off (fertigation precision in a block with non-uniform soil).

---

## Key Sources

- Inc42 on Fyllo pricing and deployment: https://inc42.com/startups/how-fyllo-firms-up-farm-decisions-using-iot-and-precision-weather-forecasts/
- Entrackr on Fyllo USD 4M round: https://entrackr.com/2024/05/fyllo-raises-4-mn-led-by-india-quotient-and-sidbi-ventures/
- Fyllo on its Nashik origin: https://thebetterindia.com/247857/agritech-sumit-sheoran-sudhanshu-rai-startup-fyllo-bengaluru-agriculture-farming-water-conservation-success-story-him16/
- Fasal architecture: https://thebetterindia.com/changemakers/fasal-kranti-iot-ai-transforming-indian-farming-uttar-pradesh-10627593
- CropIn-AWS case study: https://pages.awscloud.com/rs/112-TZM-766/images/aws-cropin-case-study-with-Intel.pdf
- BharatRohan hyperspectral drones: https://thebetterindia.com/441296/two-engineers-amandeep-panwar-rishabh-choudhary-drone-technology-agriculture-india-crop-protection
- NITI Aayog on drone hyperspectral: https://frontiertech.niti.gov.in/story/drone-based-hyperspectral-imaging-transforming-indian-agriculture-for-sustainable-growth/
- IDH Project Farm Gate 2.0 (Ratnagiri): https://www.idhsustainabletrade.com/project/farm-gate-2-0-sustainable-mango-farming-in-india/
- IMD GKMS SOP: https://mausam.imd.gov.in/imd_latest/contents/pdf/gkms_sop.pdf
- IMD Agromet portal: https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php
- IMD Meghdoot PIB release: https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1739245
- Meghdoot paper (Maharashtra advisory volume): https://www.academia.edu/80091536/Meghdoot_A_Mobile_App_to_Access_Location_Specific_Weather_Based_Agro_Advisories_Pan_India
- DBSKKV Dapoli weather-forecast portal: https://www.dbskkv.org/farmers-corner/weather-forecast
- ICAR-CISH IPM mango hopper: https://cish.icar.gov.in/ipm_MangoHopper.php
- ICAR-CISH smart-orchard paper: https://epubs.icar.org.in/index.php/IndHort/article/view/177199
- CROPSAP Maharashtra: https://cropsap.maharashtra.gov.in/ and M-Cropsap: https://cropsap.maharashtra.gov.in/Mcropsap/
- NCIPM CROPSAP report (mango pests): https://ncipm.icar.gov.in/NCIPMPDFs/FOLDERS/CROPSAPBookforWEB_.pdf
- Plantix India footprint: https://plantix.net/en/blog/plantix-networked-india/
- NASA POWER methodology: https://power.larc.nasa.gov/docs/methodology/
- NASA POWER vs IMD vs MarkSim (Uttarakhand): https://link.springer.com/article/10.1007/s00704-023-04787-5
- Narmada gauge vs satellite rainfall: https://link.springer.com/article/10.1007/s10661-023-12206-5
- Open-Meteo: https://open-meteo.com/
- Sentinel-2 5-day revisit (Sentinel Hub docs): https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l1c/
- Western Ghats monsoon cloud cover 90%+: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11760589/
- AGMARKNET on data.gov.in: https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi
- Anthracnose-weather model R^2 0.93: https://www.researchgate.net/figure/Correlation-between-mango-anthracnose-severity-and-weather-parameters-2018_fig4_340896997
- Powdery-mildew weather window: https://nhb.gov.in/pdf/fruits/mango/man002.pdf and https://www.researchgate.net/publication/291815012_Forewarning_powdery_mildew_caused_by_Oidium_mangiferae_in_mango_Mangifera_indica_using_logistic_regression_models
- Renke leaf-wetness sensor on Robu.in: https://robu.in/product/leaf-wetness-sensor-type-rs485/
- DFRobot tipping-bucket rain gauge on Robu.in: https://robu.in/product/dfrobot-gravity-tipping-bucket-rainfall-sensor-i2c-uart/
- TechnoSam capacitive soil-moisture sensor on Amazon.in: https://www.amazon.in/TechnoSam-Capacitive-Anti-Corrosion-Compatible-Development/dp/B0B21LRMZK
- DFRobot IP65 capacitive soil moisture (waterproof): https://www.dfrobot.com/product-2054.html
- Pessl iMETOS 3.3: https://metos.global/en/imetos33/ and Metos India: https://www.indiamart.com/metos-instruments-india-pvt-ltd/
