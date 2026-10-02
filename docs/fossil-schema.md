Write a JSON array. Each fossil item has EXACTLY these fields:
{
 "id": kebab-case unique, prefix "fos-",
 "taxon": scientific name as in the source (genus species, or genus sp.); no invented species,
 "group": one of "trilobite","nautiloid","graptolite","conodont","tentaculitid","brachiopod","fusulinid","coral","ammonoid","bivalve","gastropod","radiolarian","crinoid","fish","reptile","dinosaur","mammal","primate","plant","other",
 "age_top_ma": younger bound of the age range in Ma (number), "age_base_ma": older bound (number, > age_top_ma),
   (convert stated stages with the ICS 2024/12 chart and say so in _notes),
 "stage": stage / series name as stated (e.g. "Darriwilian", "Middle Permian (Wordian)", "Early Cretaceous (Barremian–Aptian)"),
 "formation_en": formation/group name or null, "formation_th": Thai name or null,
 "locality": {
   "name_en", "name_th": the site / village / hill / quarry name,
   "tambon_th": Thai tambon name or null, "amphoe_th": Thai district name or null,
   "province_th", "province_en": province (required),
   "lat", "lon": decimal degrees (required; use the published coordinate if given, otherwise the centre of the village/tambon/district you name),
   "precision": "site" (coordinate given in the source) | "area" (village/tambon centre) | "district" (only the district/province known)
 },
 "significance_th": 1–2 sentences natural university-level Thai (English terms in brackets on first use): why this is an index fossil / what age or environment it indicates,
 "significance_en": same in English,
 "citation": {"text": "Authors Year, Short title, Journal vol:pages", "url": "https://doi.org/... or stable URL"},
 "source_type": "peer-reviewed"|"government-report"|"thesis"|"conference"|"preprint",
 "verified": false,
 "_notes": English note for the instructor: what the source states (age, locality wording, coordinates), how you read it (full text / abstract / snippet), how you got the tambon/amphoe and coordinates (source, Wikipedia/GeoNames/official gazetteer), and doubts.
}
Rules: NEVER invent a taxon, locality, tambon/amphoe name, coordinate or citation. If the tambon or amphoe is not stated by a source or confirmable from an official/encyclopedic gazetteer for the named place, set it to null. Confirm every DOI on Crossref (https://api.crossref.org/works/<doi>). Validate the JSON parses.
