"""
Task definitions for the Courtroom Argument Simulator.
Three tasks ranging from easy (petty theft) to hard (premeditated murder).
"""

TASKS = {

    # ──────────────────────────────────────────────────────────────────────────
    # TASK 1 — EASY
    # A straightforward shoplifting case with strong alibi evidence.
    # An LLM should be able to win this by presenting the alibi and arguing clearly.
    # ──────────────────────────────────────────────────────────────────────────
    "task_easy": {
        "name": "The Shoplifting Alibi",
        "difficulty": "easy",
        "description": (
            "Defend Marcus Webb, accused of shoplifting electronics worth $320 from a convenience store. "
            "He has a solid alibi: he was at a documented medical appointment across town at the time. "
            "The prosecution's only evidence is a blurry CCTV image they claim shows Marcus."
        ),
        "charge": "Petty theft (shoplifting), value $320",
        "max_turns": 10,
        "initial_jury_mood": 0.45,
        "initial_case_strength": 0.6,
        "objections_per_phase": 3,
        "plea_available": True,
        "defendant_profile": {
            "name": "Marcus Webb",
            "age": 28,
            "occupation": "Warehouse worker",
            "prior_record": "None",
            "alibi": "Medical appointment at City Clinic, 3:15 PM — same time as alleged theft",
        },
        "witnesses": [
            {
                "id": "w1",
                "name": "Dr. Sarah Okafor",
                "role": "Defense witness — treating physician",
                "testimony_summary": "Confirms Marcus was at his appointment from 3:00–3:45 PM on the date in question.",
                "credibility": 0.9,
            },
            {
                "id": "w2",
                "name": "Officer Brent Caruso",
                "role": "Prosecution witness — arresting officer",
                "testimony_summary": "Claims CCTV footage shows someone matching Marcus's description.",
                "credibility": 0.5,
            },
        ],
        "evidence": [
            {
                "id": "ev1",
                "name": "Medical appointment record",
                "description": "Signed and timestamped record from City Clinic confirming the 3:15 PM visit.",
                "strength": 0.9,
            },
            {
                "id": "ev2",
                "name": "CCTV footage analysis",
                "description": "Independent expert analysis showing the footage is too blurry for positive ID.",
                "strength": 0.7,
            },
            {
                "id": "ev3",
                "name": "Bus pass transaction log",
                "description": "Bus card swipe record showing Marcus boarded a bus 2 miles from the store at 2:50 PM.",
                "strength": 0.8,
            },
        ],
        "prosecution_opening": (
            "The prosecution will show that on the afternoon of March 14th, the defendant Marcus Webb "
            "was clearly identified on store surveillance footage stealing electronics. "
            "We have a positive ID and will prove guilt beyond reasonable doubt."
        ),
        "prosecution_responses": [
            "The CCTV image is sufficiently clear — our expert will testify to that.",
            "The defense alibi witness has a personal relationship with the defendant.",
            "We maintain the footage shows the defendant. The jury can see for themselves.",
            "Any bus pass record could have been arranged. The visual evidence speaks clearly.",
            "The prosecution rests on the strength of eyewitness identification.",
        ],
        "win_condition": "not_guilty or hung_jury",
        "target_score": 0.65,
    },


    # ──────────────────────────────────────────────────────────────────────────
    # TASK 2 — MEDIUM
    # A financial fraud case with conflicting expert witnesses and partial evidence.
    # Requires strategic evidence presentation and targeted cross-examination.
    # ──────────────────────────────────────────────────────────────────────────
    "task_medium": {
        "name": "The Embezzlement Trial",
        "difficulty": "medium",
        "description": (
            "Defend Priya Nair, CFO accused of embezzling $2.1M from her company over three years. "
            "The prosecution has bank records and a whistleblower. "
            "The defense must show the transactions were authorized and the whistleblower has a personal vendetta."
        ),
        "charge": "Embezzlement, wire fraud — $2.1M over 36 months",
        "max_turns": 15,
        "initial_jury_mood": 0.3,
        "initial_case_strength": 0.35,
        "objections_per_phase": 4,
        "plea_available": True,
        "defendant_profile": {
            "name": "Priya Nair",
            "age": 44,
            "occupation": "CFO, Vertex Solutions Inc.",
            "prior_record": "None",
            "alibi": "All transactions had dual-signature board approval; documentation exists but is disputed.",
        },
        "witnesses": [
            {
                "id": "w1",
                "name": "James Holloway",
                "role": "Prosecution witness — company whistleblower",
                "testimony_summary": "Claims he personally witnessed Priya transfer funds to a shell account she controlled.",
                "credibility": 0.55,
                "vulnerability": "Was passed over for promotion by Priya; filed an HR complaint six months ago.",
            },
            {
                "id": "w2",
                "name": "Dr. Miriam Leach",
                "role": "Prosecution witness — forensic accountant",
                "testimony_summary": "Traced $2.1M to accounts linked to the defendant.",
                "credibility": 0.75,
                "vulnerability": "Did not review board meeting minutes approving the transactions.",
            },
            {
                "id": "w3",
                "name": "Board Chair Gerald Singh",
                "role": "Defense witness — company board chair",
                "testimony_summary": "States the board approved all major financial restructuring transactions.",
                "credibility": 0.7,
            },
        ],
        "evidence": [
            {
                "id": "ev1",
                "name": "Board resolution minutes",
                "description": "Signed minutes from Q3 board meetings authorizing financial restructuring transfers.",
                "strength": 0.75,
            },
            {
                "id": "ev2",
                "name": "HR complaint record",
                "description": "Internal HR record showing Holloway filed a harassment complaint against Priya after being denied promotion.",
                "strength": 0.65,
            },
            {
                "id": "ev3",
                "name": "Dual-authorization audit trail",
                "description": "System logs showing every transaction required two executive sign-offs.",
                "strength": 0.7,
            },
            {
                "id": "ev4",
                "name": "Forensic accountant rebuttal report",
                "description": "Independent analysis showing the transferred funds were reinvested in subsidiary operations.",
                "strength": 0.6,
            },
        ],
        "prosecution_opening": (
            "Over three years, Priya Nair systematically looted Vertex Solutions, routing millions "
            "through shell corporations for personal gain. We have bank records, a credible eyewitness, "
            "and forensic analysis that will prove this beyond any doubt."
        ),
        "prosecution_responses": [
            "Board minutes can be fabricated after the fact — we'll show the timestamps are inconsistent.",
            "The dual-authorization system was bypassed using administrative override credentials held by the defendant.",
            "The HR complaint is a red herring — Holloway's testimony is corroborated by the financial trail.",
            "The subsidiary operations claim falls apart under our forensic accountant's cross-analysis.",
            "The prosecution's case is built on hard financial evidence, not personal grievances.",
            "We will show the board approval claim is contradicted by testimony from two other board members.",
        ],
        "win_condition": "not_guilty or hung_jury or guilty_reduced",
        "target_score": 0.50,
    },


    # ──────────────────────────────────────────────────────────────────────────
    # TASK 3 — HARD
    # A premeditated murder case with circumstantial evidence but no direct proof.
    # Requires sophisticated multi-phase strategy: discredit witnesses, create
    # reasonable doubt, and deliver a compelling closing argument.
    # ──────────────────────────────────────────────────────────────────────────
    "task_hard": {
        "name": "The Premeditated Murder Trial",
        "difficulty": "hard",
        "description": (
            "Defend Elias Vance, accused of the premeditated murder of his business partner, "
            "Daniel Roe. The prosecution claims Elias killed Roe for a $4M insurance payout and "
            "control of their company. Evidence is entirely circumstantial — no weapon found, "
            "no DNA at scene — but public sentiment is hostile and the prosecution is aggressive. "
            "You must dismantle every piece of circumstantial evidence while building a coherent "
            "alternative narrative."
        ),
        "charge": "First-degree premeditated murder",
        "max_turns": 20,
        "initial_jury_mood": 0.2,
        "initial_case_strength": 0.25,
        "objections_per_phase": 5,
        "plea_available": False,
        "defendant_profile": {
            "name": "Elias Vance",
            "age": 52,
            "occupation": "Co-founder & CEO, Vance-Roe Capital",
            "prior_record": "None",
            "alibi": "Claims he was at his mountain cabin — no witnesses, but phone metadata is consistent.",
        },
        "witnesses": [
            {
                "id": "w1",
                "name": "Det. Rosa Fuentes",
                "role": "Prosecution witness — lead detective",
                "testimony_summary": "Describes the crime scene, the financial motive, and Elias's opportunity.",
                "credibility": 0.8,
                "vulnerability": "Did not obtain a warrant before searching Elias's vehicle; evidence may be inadmissible.",
            },
            {
                "id": "w2",
                "name": "Angela Roe",
                "role": "Prosecution witness — victim's wife",
                "testimony_summary": "States Elias and Daniel had a violent argument two days before the death.",
                "credibility": 0.7,
                "vulnerability": "Stands to inherit nothing if Elias is acquitted — potential bias.",
            },
            {
                "id": "w3",
                "name": "Prof. Calvin Bright",
                "role": "Prosecution witness — financial forensics expert",
                "testimony_summary": "Testifies the business partnership would have dissolved within 6 months, giving Elias motive.",
                "credibility": 0.65,
                "vulnerability": "Projection based on 3-month data window; doesn't account for a signed mediation agreement.",
            },
            {
                "id": "w4",
                "name": "Lena Park",
                "role": "Defense witness — cybersecurity expert",
                "testimony_summary": "Phone metadata places Elias's device consistently at the mountain cabin.",
                "credibility": 0.75,
            },
            {
                "id": "w5",
                "name": "Dr. Omar Hassan",
                "role": "Defense witness — forensic pathologist",
                "testimony_summary": "Time of death window is inconsistent with the prosecution's timeline.",
                "credibility": 0.8,
            },
        ],
        "evidence": [
            {
                "id": "ev1",
                "name": "Phone metadata log",
                "description": "Cell tower and GPS metadata showing Elias's phone at the cabin for 48 hours around time of death.",
                "strength": 0.7,
            },
            {
                "id": "ev2",
                "name": "Mediation agreement",
                "description": "Signed document showing Elias and Daniel were actively resolving their dispute via mediation.",
                "strength": 0.75,
            },
            {
                "id": "ev3",
                "name": "Illegal search motion",
                "description": "Motion to suppress: Detective Fuentes searched the vehicle without a warrant.",
                "strength": 0.8,
            },
            {
                "id": "ev4",
                "name": "Pathology report — time of death",
                "description": "Independent pathologist's finding that death occurred 4–6 hours earlier than prosecution claims.",
                "strength": 0.65,
            },
            {
                "id": "ev5",
                "name": "Angela Roe estate beneficiary document",
                "description": "Legal document showing Angela Roe benefits financially only if Elias is convicted.",
                "strength": 0.6,
            },
        ],
        "prosecution_opening": (
            "Elias Vance had motive: four million dollars in life insurance and full company control. "
            "He had opportunity: no verified alibi. He had means: access to the victim's private estate. "
            "This was cold, calculated, premeditated murder and we will prove it step by step."
        ),
        "prosecution_responses": [
            "Phone metadata proves presence of a device, not a person — the phone could have been left there deliberately.",
            "The mediation agreement means nothing — it shows the conflict was serious enough to require formal mediation.",
            "The vehicle search produced no weapon — it's irrelevant to the prosecution's case.",
            "The pathology discrepancy is within normal forensic variation. Our expert stands by the timeline.",
            "Angela Roe's emotional testimony is credible. She has no reason to lie about what she heard.",
            "The defendant has no alibi witness. A cabin in the mountains, alone? The jury sees through this.",
            "The prosecution's case rests on an unbroken chain of circumstantial evidence. Each link holds.",
            "We will call rebuttal witnesses to address every defense claim systematically.",
        ],
        "win_condition": "not_guilty or hung_jury",
        "target_score": 0.40,
    },
}
