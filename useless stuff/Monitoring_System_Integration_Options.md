# Monitoring System Integration Options for a Konkan Alphonso Decision-Support Tool

**Author:** CREST-Gold / JSR submission preparation
**Date:** 2026-05-30
**Scope:** Realism audit of existing monitoring systems a Konkan Alphonso farmer may already have, and whether a non-paying student researcher can tap their data without deploying new hardware.

---

## 1. Fyllo (AgriHawk Technologies)

1. **Data outputs.** Soil moisture at multiple root-zone depths, soil temperature (Nero unit), plus a separate weather node (Kairo) reporting at ~20-minute intervals across ~100-150 acres: rainfall, air temperature, humidity, leaf wetness, solar / lux. Crop-level advisories are layered on top in the Fyllo app. (https://fyllo.in/, https://www.electronicsforyou.biz/startups/weve-deployed-over-6000-iot-crop-maintenance-devices-across-13-states-in-india-in-three-years/)
2. **Data access for a non-paying student.** Fyllo's own ToS asserts ownership of "data, software, APIs, and other smart device applications" (https://fyllo.in/app-policies). There is **no documented public/developer API and no published CSV-export endpoint**. The pragmatic path is: ask the farmer to log into the Fyllo app, screen-share, and either (a) export the per-plot historical chart as a PNG/PDF the app already supports, or (b) screenshot + OCR. A formal partnership requires direct contact with Fyllo (sales@fyllo.in).
3. **Authentication / cost.** Farmer owns device (Nero ~Rs 16,000, Kairo ~Rs 45,000) plus ~Rs 2,000-6,000/year subscription per device (https://www.electronicsforyou.biz/startups/weve-deployed-over-6000-iot-crop-maintenance-devices-across-13-states-in-india-in-three-years/). Student costs nothing if the farmer shares the login.
4. **Konkan coverage.** Fyllo's primary crop is grapes (Nashik) and pomegranate (https://yourstory.com/2021/01/iot-based-agritech-startup-empowers-farmers-provide-crop-data). 4,000+ devices across 10 states / 15+ crops — no specifically documented Alphonso deployment in Ratnagiri / Sindhudurg.
5. **Likelihood your farmer has it.** **Low-to-moderate.** A "rich mid-sized" Konkan farmer growing for export *may* have it if they also do grapes/pomegranate elsewhere, but Fyllo is not a Konkan-default install.

## 2. Fasal (Wolkus Technology Solutions)

1. **Data outputs.** "Fasal Kranti" v4 node carries 12+ sensors: rainfall, wind speed/direction, lux, solar intensity, air temperature, humidity, leaf wetness, soil temperature, and soil water tension at multiple depths. Sampling appears to be sub-hourly. (https://thebetterindia.com/243842/bengaluru-agritech-startup-new-tech-innovation-fasal-kranti-water-saving-precision-farmer-irrigation-pest-management-india-nor41/, https://yourstory.com/2021/01/farming-agritech-startup-fasal-iot-horticulture-farmers)
2. **Data access for a non-paying student.** **No public REST API documented.** Fasal markets a B2B "Enterprise" product (https://www.fasal.co/enterprise-product) but that is contract-only. The realistic path is again farmer-app login + manual chart export, or a one-off NDA-style data dump from connect@wolkus.com. Mobile app PDF/CSV export is *not* documented but may exist for paying users.
3. **Authentication / cost.** Upfront device fee + monthly subscription (no public list price). Student access is free only if the farmer shares the app login.
4. **Konkan coverage.** Documented operations in Maharashtra, Karnataka, Chhattisgarh, MP across 10,000+ acres; specific Konkan / Alphonso case studies are **not** in public reporting. Fasal's headline horticulture crops are grapes and pomegranate. (https://yourstory.com/2021/01/farming-agritech-startup-fasal-iot-horticulture-farmers)
5. **Likelihood your farmer has it.** **Low-to-moderate.** Same logic as Fyllo — possible if farmer is sophisticated and multi-crop, but not a Konkan default.

## 3. CropIn

1. **Data outputs.** "SmartFarm" is a farm-ERP layer — plot polygon, crop variety, seed, sowing date, scouting photos, voice notes, plus a satellite-derived NDVI / canopy layer in Cropin Grow. (https://www.cropin.com/cropin-grow-smartfarm-plus/)
2. **Data access for a non-paying student.** SmartFarm is explicitly **B2B-only** — login credentials are issued by the enterprise client (exporter, processor, FPO), not by individual farmers (https://apps.apple.com/in/app/cropin-smartfarm/id1458577484). There is **no farmer-side CSV export, no public API**. To use it, the student would need an exporter sponsor.
3. **Authentication / cost.** Enterprise SaaS contract; no free tier.
4. **Konkan coverage.** Not specifically documented for Alphonso. CropIn typically appears via exporters / produce aggregators.
5. **Likelihood your farmer has it.** **Very low** unless the farmer ships through a large exporter (e.g., Devgad Taluka Amba Utpadak Sahakari Sanstha tie-ups). Even then, the *farmer* doesn't own the data — the exporter does.

## 4. AgNext

1. **Data outputs.** Spectral / image-based **quality assessment at procurement points** — moisture, foreign matter, broken/shrivelled fraction, etc. Their Qualix platform analyses commodity samples in ~30 seconds (https://agnext.com/, https://indiaai.gov.in/article/providing-ai-driven-solutions-for-agriculture-and-food-commodity-value-chains).
2. **Data access for a non-paying student.** AgNext is a **B2B SaaS for buyers / FCI / mandi-side actors**, not for farmers. No public farmer-side API or CSV.
3. **Authentication / cost.** Enterprise contract only.
4. **Konkan coverage.** AgNext is strong in cereals / spices / dairy procurement; no documented mango-on-farm deployment.
5. **Likelihood your farmer has it.** **Effectively zero.** Wrong tier of the value chain.

## 5. IMD Meghdoot + AMFU Agromet Advisory

1. **Data outputs.** District- and block-level 5-day forecasts (rainfall, T, RH, wind, cloud) and twice-weekly (Tuesday/Friday) crop-and-district-specific agromet bulletins in vernacular (https://internal.imd.gov.in/press_release/20220824_pr_1790.pdf, https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php).
2. **Data access for a non-paying student.** Two clean paths: (a) **scrape** the public agromet bulletin PDFs at `mausam.imd.gov.in/responsive/agromet_adv_ser_block_past_en.php`, and (b) use the IMD API portal at `api.imd.gov.in` (14 published endpoints — district nowcast, district rainfall, district warning, etc.) (https://mausam.imd.gov.in/responsive/apis.php, https://api.imd.gov.in/public/api_reference.html). IMD APIs require IP-whitelisting via Dr. Sankar Nath (sankar.nath@imd.gov.in) — a student-grade research request is realistic.
3. **Authentication / cost.** Free, but email-gated for the API. PDF scraping requires no auth.
4. **Konkan coverage.** Ratnagiri and Sindhudurg AMFUs both publish through this channel — perfect Konkan coverage.
5. **Likelihood your farmer has it.** The farmer doesn't "have" it in any installed sense; the data is **public and Konkan-relevant by default**. Treat it as a baseline feed, not an integration.

## 6. Maharashtra CROPSAP / M-Cropsap

1. **Data outputs.** Field-scout-entered pest and disease incidence (insect counts, infestation %), GPS-tagged, with expert advisory pushed back via SMS (https://cropsap.maharashtra.gov.in/, http://egovmobileapps.nic.in/apps/m-cropsap).
2. **Data access for a non-paying student.** The public-facing CROPSAP portal allows browsing — pest maps, district summaries — but the underlying database login is restricted to Department of Agriculture staff (https://cropsap.maharashtra.gov.in/dept/). **No public API.** Realistic path is HTML scrape of the public dashboards.
3. **Authentication / cost.** Free for public dashboard scraping.
4. **Konkan coverage.** CROPSAP's original mandate was cotton/soybean/pulses, but it has been extended; DBSKKV Dapoli is named as a CROPSAP implementation partner (https://ncipm.icar.gov.in/databasenetworking.aspx, https://farmer.gov.in/imagedefault/handbooks/BooKLet/MAHARASHTRA/20160725144307_CROPSAP_Booklet_for_web.pdf). Mango-specific surveillance is patchy but present in Konkan.
5. **Likelihood your farmer has it.** Indirect — pest pressure data for their **taluka** is published whether they participate or not.

## 7. DBSKKV Dapoli (Konkan Krishi Vidyapeeth) weather page

1. **Data outputs.** Konkan-specific weather forecast + annual climate-trend PDFs for Dapoli (e.g., `Climate-trend_dapoli-2023-24.pdf`) (https://www.dbskkv.org/farmers-corner/weather-forecast, https://old.dbskkv.org/pdf/2022-23/Farmers_Corner/Weather_Forecast/Climate-trend_dapoli-2023-24.pdf).
2. **Data access for a non-paying student.** Static HTML / PDF scrape. No API. Trivially automatable with `requests` + `pdfplumber`.
3. **Authentication / cost.** Free, no auth.
4. **Konkan coverage.** Best-in-class for Konkan microclimate — this is the agronomic source-of-truth used by AMFUs in the region.
5. **Likelihood your farmer has it.** Universally referenced in Konkan; the farmer probably reads its WhatsApp forwards even if not the page itself.

## 8. Plantix (PEAT GmbH)

1. **Data outputs.** Phone-camera image-based disease/pest/nutrient diagnosis with treatment advice; community Q&A. Per-user diagnosis **history log** is kept in-app (https://plantix.net/en/, https://www.mdpi.com/2073-4395/12/8/1869).
2. **Data access for a non-paying student.** Plantix sells a B2B "Plantix Vision" pathogen-recognition API (https://plantix.net/en/business/plantix-vision-api/) — that is sales-contract gated. A 17-app comparative review notes 70.6% of plant-disease apps (including Plantix in practice) provide **no user data export** (https://www.mdpi.com/2073-4395/12/8/1869). Realistic path: farmer screenshots their history and shares them — manual OCR / Vision-LLM parse.
3. **Authentication / cost.** Free for the farmer; API is enterprise-priced.
4. **Konkan coverage.** Plantix is widely installed across India by retail-shop and extension-officer recommendation; specific Konkan numbers not published.
5. **Likelihood your farmer has it.** **Moderate-to-high.** Plantix is one of the most-installed agri apps in India; even small-to-mid Alphonso growers have it.

## 9. Government data portals — AGMARKNET / e-NAM / data.gov.in

1. **Data outputs.** AGMARKNET = daily wholesale min/max/modal prices for ~200 commodities including mango, by mandi (https://agmarknet.gov.in/, https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi). e-NAM = electronic-trade arrivals + price for ~1,000 linked APMCs (https://www.enam.gov.in/web/dashboard/agmarknet, https://en.wikipedia.org/wiki/E-NAM). data.gov.in republishes AGMARKNET as CSV/JSON with a Data API.
2. **Data access for a non-paying student.** **Genuinely public.** Daily price CSV/JSON via `data.gov.in` Data API (free API key on registration). AGMARKNET also has community-maintained API wrappers (https://farmonaut.com/api-development/agmarknet-api-access-crop-prices-market-data-india, https://lynxbee.com/getting-real-time-indian-agricultural-commodity-market-rates-using-agmarknet-api/). e-NAM exposes a public trade-data dashboard (https://enam.gov.in/web/dashboard/trade-data) — scrapable, though no first-party REST API.
3. **Authentication / cost.** Free with data.gov.in API key.
4. **Konkan coverage.** Vashi (Mumbai), Ratnagiri, Devgad, Vengurla mandis all report mango arrivals. Real caveat: Konkan Alphonso is largely sold direct-to-consumer / via Devgad-Hapus-branded e-commerce, so APMC volume undercounts the actual market.
5. **Likelihood your farmer has it.** Not an "install" — the farmer's *price reality* is in this feed whether they look at it or not.

## 10. BharatRohan / drone-as-a-service

1. **Data outputs.** Hyperspectral + multispectral drone surveys every 7-15 days yielding prescription maps; **delivery to farmer is via WhatsApp message + chatbot report**, not a structured file (https://thebetterindia.com/441296/two-engineers-amandeep-panwar-rishabh-choudhary-drone-technology-agriculture-india-crop-protection, https://themachinemaker.com/news/bharatrohan-expands-drone-services-through-strategic-partnerships-with-agri-input-dealers/).
2. **Data access for a non-paying student.** No farmer-side machine-readable export. Reusing the data means parsing WhatsApp PDFs / chatbot screenshots. Their CropAssure/SeedAssure/SourceAssure platforms are B2B contracts.
3. **Authentication / cost.** Farmer pays per-acre per-survey; student gets the chatbot output only via the farmer.
4. **Konkan coverage.** BharatRohan operates across ~7 states but its anchor crops are wheat, paddy, cotton, mustard. **No documented Alphonso deployment.**
5. **Likelihood your farmer has it.** **Low.** Drone-as-service in Konkan mango is still pilot-stage and dominated by ad-hoc local operators.

## 11. Pessl iMETOS / FieldClimate

1. **Data outputs.** Full agro-meteorological station — temperature, RH, leaf wetness, rainfall, solar radiation, wind, soil moisture profiles. Per-sensor frequency typically 5-15 min.
2. **Data access for a non-paying student.** **Best-in-class for our purposes.** Pessl exposes a documented public REST API at `api.fieldclimate.com/v1/docs/` and `v2/docs/` with HMAC authentication; the *station owner* generates HMAC public/private keys via `ng.fieldclimate.com -> User -> API services -> GENERATE NEW` (https://api.fieldclimate.com/v2/docs/, https://support.metos.at/en/support/solutions/articles/15000018359-create-hmac-api-keys-using-fieldclimate). Mature client libraries already exist (Python — SatAgro, R — BASF, .NET — nuvemtecnologia) (https://github.com/SatAgro/fieldclimate, https://github.com/basf/rfieldclimate). If the farmer owns an iMETOS, the student can be pulling time-series CSV within an hour.
3. **Authentication / cost.** Free for station owners; HMAC keys issued at no cost. The farmer pays for the hardware (₹2-4 lakh) and the data plan.
4. **Konkan coverage.** Pessl is the premium choice for export-oriented Indian horticulture (grapes, pomegranate, apples); presence in Konkan is rare but not zero — large Devgad / Ratnagiri exporters do own them.
5. **Likelihood your farmer has it.** **Low overall, but high in your specific persona.** A "rich mid-sized Konkan Alphonso farmer" exporting to Gulf / EU is the most likely Pessl owner in the entire mango sector.

## 12. Digital Green / Avanijal / smaller agritech in Maharashtra

1. **Data outputs.** Digital Green = video-based extension content (not a sensor system). Avanijal = irrigation-controller automation (Karnataka-anchored). Neither runs a structured per-farm telemetry feed for mango.
2. **Data access.** Digital Green publishes content libraries openly; Avanijal data is owner-app-locked. Neither is a useful sensor source.
3. **Cost.** Free / N-A.
4. **Konkan coverage.** Negligible for Alphonso. The Maharashtra government's MahaAgri-AI 2025-2029 policy (₹500 cr) is the relevant umbrella but is still rolling out (https://www.tribuneindia.com/news/business/agritech-4-0-making-maharashtra-the-first-ai-powered-farming-state/).
5. **Likelihood your farmer has it.** **Very low.**

---

## Summary table

| System | Likelihood farmer has it | Data accessible for student? | Realistic integration effort (hrs) | What to do if farmer has it |
|---|---|---|---|---|
| Fyllo | Low-moderate | App login + screenshot/OCR only (no public API) | 20-30 (OCR + manual chart export) | Get login, scrape weekly chart exports |
| Fasal | Low-moderate | App login + manual export; no public API | 20-30 | Same — login share + chart parse |
| CropIn | Very low | B2B-only, exporter-owned | 40+ (need exporter NDA) | Skip unless exporter sponsor |
| AgNext | ~0 | Wrong tier of chain | N/A | Skip |
| **IMD Meghdoot + Agromet** | Always available (public) | **Public API + scrapable PDF bulletins** | **8-12** | Baseline weather + advisory feed for every user |
| CROPSAP / M-Cropsap | Public surveillance, taluka-level | Web scrape of public dashboard | 10-15 | Treat as district pest pressure layer |
| **DBSKKV Dapoli** | Public, Konkan-specific | **Static page + PDF scrape** | **4-6** | Highest-trust Konkan microclimate baseline |
| Plantix | Moderate-high | Screenshot history + Vision-LLM parse | 15-25 | Ask farmer for last 6 months of diagnosis screenshots |
| **AGMARKNET / e-NAM / data.gov.in** | Always public | **Free API key, CSV/JSON** | **6-10** | Default price + arrivals layer |
| BharatRohan / drones | Low | Chatbot PDF only | 25-40 | Parse the WhatsApp report if shared |
| **Pessl iMETOS / FieldClimate** | Low overall, **high for export-grade Alphonso grower** | **Public REST API with HMAC; mature client libs** | **6-10** | Ask farmer for HMAC keys, ingest directly |
| Digital Green / Avanijal | Very low | Content only | N/A | Skip |

---

## Recommendation — build connectors for these 5, in priority order

The selection rule is `likelihood × per-farmer-value × ease`. Two of the five are public baselines (so they ship for every user regardless of who the farmer is) and three are the realistic farm-side integrations a Konkan Alphonso grower is plausibly running.

1. **AGMARKNET / data.gov.in price API** (free, public, CSV/JSON, ~6-10 hrs). Ships for every user. Provides the market-side leg of the decision-support tool. (https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)
2. **IMD Mausam + Meghdoot agromet bulletins** (free API + PDF scrape, ~8-12 hrs). Ships for every user. Block-level forecast + twice-weekly agromet advisory in Marathi — the same data Konkan extension officers already trust. (https://api.imd.gov.in/public/api_reference.html, https://mausam.imd.gov.in/responsive/apis.php)
3. **DBSKKV Dapoli weather + climate-trend PDFs** (free scrape, ~4-6 hrs). Ships for every Konkan user. Highest-credibility regional microclimate source — also strong for JSR defensibility because reviewers will recognise it as the Konkan domain authority. (https://www.dbskkv.org/farmers-corner/weather-forecast)
4. **Pessl FieldClimate REST API** (public docs, HMAC auth, mature Python client, ~6-10 hrs). The **single farm-installed system most likely on your specific persona's farm**, and the only commercial Indian agri-sensor vendor with a documented public API. If the persona owns one, this is the highest-value real-time on-farm telemetry leg of the entire tool. (https://api.fieldclimate.com/v2/docs/, https://github.com/SatAgro/fieldclimate)
5. **Plantix screenshot/history connector** (~15-25 hrs of OCR + Vision-LLM parsing). Realistic because Plantix install rates are genuinely high among Indian smallholders and the farmer can simply share screenshots. Gives the disease/pest-diagnosis leg without depending on Plantix's B2B Vision API. (https://plantix.net/en/, https://www.mdpi.com/2073-4395/12/8/1869)

**Explicit non-recommendations:** do **not** budget for CropIn, AgNext, BharatRohan, Digital Green, or Avanijal — all are either wrong-tier (procurement-side, not farm-side), B2B-contract-gated, or have no realistic Konkan-Alphonso footprint. Treat Fyllo and Fasal as **opportunistic** connectors: if a specific farmer turns out to have one, build a one-off app-login + screen-scrape adapter; do not invest in a productized integration since neither vendor exposes a public API.

**Defensibility note for CREST-Gold / JSR.** The five-connector architecture above is defensible in review because (a) three of the five are open-government primary sources — the reviewer cannot dispute access — and (b) the two farm-side connectors (Pessl, Plantix) are the only commercial systems with either a public REST API or a user-exportable data trail. This means the tool is genuinely reproducible by another student researcher without any enterprise contract — which is the central realism claim the paper has to defend.

---

## Sources

- [Fyllo by AgriHawk Technologies](https://fyllo.in/)
- [Fyllo App Policies (data ownership)](https://fyllo.in/app-policies)
- [Fyllo / Electronics For You device pricing](https://www.electronicsforyou.biz/startups/weve-deployed-over-6000-iot-crop-maintenance-devices-across-13-states-in-india-in-three-years/)
- [Fyllo YourStory profile](https://yourstory.com/2021/01/iot-based-agritech-startup-empowers-farmers-provide-crop-data)
- [Fasal The Better India profile](https://thebetterindia.com/243842/bengaluru-agritech-startup-new-tech-innovation-fasal-kranti-water-saving-precision-farmer-irrigation-pest-management-india-nor41/)
- [Fasal YourStory profile](https://yourstory.com/2021/01/farming-agritech-startup-fasal-iot-horticulture-farmers)
- [Fasal Enterprise product](https://www.fasal.co/enterprise-product)
- [CropIn Grow / SmartFarm+](https://www.cropin.com/cropin-grow-smartfarm-plus/)
- [CropIn SmartFarm App Store listing — B2B credentials only](https://apps.apple.com/in/app/cropin-smartfarm/id1458577484)
- [AgNext company site](https://agnext.com/)
- [AgNext IndiaAI profile](https://indiaai.gov.in/article/providing-ai-driven-solutions-for-agriculture-and-food-commodity-value-chains)
- [IMD Meghdoot press release](https://internal.imd.gov.in/press_release/20220824_pr_1790.pdf)
- [IMD Agromet advisory current](https://mausam.imd.gov.in/imd_latest/contents/agromet/advisory/englishstate_current.php)
- [IMD APIs portal](https://mausam.imd.gov.in/responsive/apis.php)
- [IMD API reference](https://api.imd.gov.in/public/api_reference.html)
- [IMD API Management](https://api.imd.gov.in/)
- [CROPSAP Maharashtra portal](https://cropsap.maharashtra.gov.in/)
- [M-Cropsap mobile app](http://egovmobileapps.nic.in/apps/m-cropsap)
- [CROPSAP booklet (incl. DBSKKV role)](https://farmer.gov.in/imagedefault/handbooks/BooKLet/MAHARASHTRA/20160725144307_CROPSAP_Booklet_for_web.pdf)
- [NCIPM CROPSAP databasenetworking](https://ncipm.icar.gov.in/databasenetworking.aspx)
- [DBSKKV Dapoli weather forecast](https://www.dbskkv.org/farmers-corner/weather-forecast)
- [DBSKKV Dapoli climate-trend PDF (2023-24)](https://old.dbskkv.org/pdf/2022-23/Farmers_Corner/Weather_Forecast/Climate-trend_dapoli-2023-24.pdf)
- [Plantix main site](https://plantix.net/en/)
- [Plantix Vision API (B2B)](https://plantix.net/en/business/plantix-vision-api/)
- [MDPI plant-disease-app comparative review](https://www.mdpi.com/2073-4395/12/8/1869)
- [AGMARKNET portal](https://agmarknet.gov.in/)
- [data.gov.in daily mandi prices catalog](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)
- [e-NAM AGMARKNET dashboard](https://www.enam.gov.in/web/dashboard/agmarknet)
- [e-NAM trade data dashboard](https://enam.gov.in/web/dashboard/trade-data)
- [Farmonaut AGMARKNET API guide](https://farmonaut.com/api-development/agmarknet-api-access-crop-prices-market-data-india)
- [Lynxbee AGMARKNET API tutorial](https://lynxbee.com/getting-real-time-indian-agricultural-commodity-market-rates-using-agmarknet-api/)
- [BharatRohan The Better India profile](https://thebetterindia.com/441296/two-engineers-amandeep-panwar-rishabh-choudhary-drone-technology-agriculture-india-crop-protection)
- [BharatRohan Machine Maker partnership news](https://themachinemaker.com/news/bharatrohan-expands-drone-services-through-strategic-partnerships-with-agri-input-dealers/)
- [Pessl FieldClimate API v1 docs](https://api.fieldclimate.com/v1/docs/)
- [Pessl FieldClimate API v2 docs](https://api.fieldclimate.com/v2/docs/)
- [Pessl HMAC key generation guide](https://support.metos.at/en/support/solutions/articles/15000018359-create-hmac-api-keys-using-fieldclimate)
- [SatAgro Python client for FieldClimate](https://github.com/SatAgro/fieldclimate)
- [BASF R client for FieldClimate](https://github.com/basf/rfieldclimate)
- [Maharashtra MahaAgri-AI 2025-2029 policy coverage (Tribune)](https://www.tribuneindia.com/news/business/agritech-4-0-making-maharashtra-the-first-ai-powered-farming-state/)
